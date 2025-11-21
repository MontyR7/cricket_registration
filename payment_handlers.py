from flask import current_app as app
from models import Player, db
from datetime import datetime
import hmac
import hashlib
import json
import os
from routes import REGISTRATION_FEE  # Import registration fee constant

# Import redis for payment status tracking
from flask_sse import sse
from app import app

def verify_upi_signature(data, signature):
    """Verify the signature from UPI provider"""
    secret_key = os.getenv('UPI_WEBHOOK_SECRET')
    if not secret_key:
        app.logger.error("UPI_WEBHOOK_SECRET not configured")
        return False
        
    try:
        expected_signature = hmac.new(
            secret_key.encode(),
            json.dumps(data, sort_keys=True).encode(),
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(signature, expected_signature)
    except Exception as e:
        app.logger.error(f"Error verifying signature: {str(e)}")
        return False

def handle_upi_callback(data, request_id):
    """Process UPI callback data and update payment status with retry logic"""
    try:
        app.logger.info(f"=== Processing UPI Callback [{request_id}] ===\n" +
                       f"Data: {json.dumps(data, indent=2)}")
        
        # Helper to extract field with multiple possible keys
        def extract_field(field_names):
            for name in field_names:
                value = data.get(name)
                if value:
                    app.logger.info(f"[{request_id}] Found {name}: {value}")
                    return str(value)
            return None
            
        # Extract payment details with multiple possible field names
        transaction_id = extract_field(['txnId', 'transactionId', 'transaction_id', 'trans_id', 'referenceId'])
        status = extract_field(['txnStatus', 'status', 'transactionStatus', 'payment_status'])
        amount = extract_field(['txnAmount', 'amount', 'transactionAmount', 'payment_amount'])
        
        app.logger.info(f"Processing payment:")
        app.logger.info(f"- Transaction ID: {transaction_id}")
        app.logger.info(f"- Status: {status}")
        app.logger.info(f"- Amount: {amount}")
        
        if not all([transaction_id, status, amount]):
            app.logger.error(f"Missing required webhook data: transaction_id={transaction_id}, status={status}, amount={amount}")
            return False
        
        app.logger.info(f"Received UPI callback for transaction {transaction_id} with status {status}")
        
        # Find the player by transaction ID
        player = Player.query.filter_by(transaction_id=transaction_id).first()
        
        if not player:
            app.logger.error(f"No player found for transaction {transaction_id}")
            return False
            
        # Get amount in rupees
        try:
            amount_float = float(amount)
        except ValueError:
            app.logger.error(f"Invalid amount format: {amount}")
            return False
            
        if status == 'SUCCESS':
            # Verify payment amount
            if amount_float != REGISTRATION_FEE:
                player.payment_status = False
                player.registration_status = 'pending'
                player.payment_note = f'Amount mismatch: expected ₹{REGISTRATION_FEE}, got ₹{amount_float}'
                player.payment_date = datetime.utcnow()
                db.session.commit()
                app.logger.error(f"Payment amount mismatch for transaction {transaction_id}: "
                               f"expected ₹{REGISTRATION_FEE}, got ₹{amount_float}")
                return True
                
            # Update player status
            # Store payment temporarily before committing
            update_data = {
                'payment_status': True,
                'registration_status': 'completed',
                'payment_date': datetime.utcnow(),
                'payment_note': f'Payment successful: ₹{amount_float}'
            }
            
            # Try to update the payment status with retry
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    for key, value in update_data.items():
                        setattr(player, key, value)
                    db.session.commit()
                    app.logger.info(f"Successfully updated payment status on attempt {attempt + 1}")
                    break
                except Exception as commit_error:
                    app.logger.error(f"Failed to commit payment status on attempt {attempt + 1}: {str(commit_error)}")
                    db.session.rollback()
                    if attempt == max_retries - 1:
                        raise
            
            app.logger.info(f"Payment successful for player {player.id}")
            # Send payment notification via SSE
            try:
                sse.publish(
                    {
                        'status': 'SUCCESS',
                        'player_id': player.id,
                        'transaction_id': transaction_id,
                        'amount': amount_float,
                        'message': 'Payment successful!'
                    },
                    type='payment_update'
                )
            except Exception as sse_error:
                app.logger.error(f"Error sending SSE notification: {str(sse_error)}")
            return True
            
        elif status in ['FAILED', 'CANCELLED']:
            # Update player status
            player.payment_status = False
            player.registration_status = 'pending'
            player.payment_note = f'Payment {status.lower()}'
            player.payment_date = datetime.utcnow()
            db.session.commit()
            
            app.logger.warning(f"Payment {status.lower()} for player {player.id}")
            return True
        
        return False
        
    except Exception as e:
        app.logger.error(f"Error in handle_upi_callback: {str(e)}")
        if 'db' in locals():
            db.session.rollback()
        return False

def get_payment_status(transaction_id):
    """Get current payment status for a transaction"""
    try:
        with app.app_context():
            app.logger.info(f"=== Payment Status Check ===")
            app.logger.info(f"Checking status for transaction: {transaction_id}")
            app.logger.info(f"Check time: {datetime.utcnow().isoformat()}")
            
            if not transaction_id:
                app.logger.error("No transaction_id provided")
                return None
                
            app.logger.info(f"Checking payment status for transaction {transaction_id}")
            
            player = Player.query.filter_by(transaction_id=transaction_id).first()
            if not player:
                app.logger.error(f"No player found for transaction {transaction_id}")
                return None
                
            app.logger.info(f"Player details:")
            app.logger.info(f"- ID: {player.id}")
            app.logger.info(f"- Name: {player.full_name}")
            app.logger.info(f"- Payment Status: {player.payment_status}")
            app.logger.info(f"- Registration Status: {player.registration_status}")
            app.logger.info(f"- Payment Date: {player.payment_date}")
            app.logger.info(f"- Payment Note: {player.payment_note}")
            
            status = 'success' if player.payment_status else 'pending'
            
            # Build response with all relevant information
            response = {
                'status': status,
                'message': 'Payment successful!' if player.payment_status else 'Waiting for payment...',
                'timestamp': player.payment_date.isoformat() if player.payment_date else None,
                'player_id': player.id,
                'transaction_id': transaction_id,
                'amount': str(getattr(player, 'registration_fee', REGISTRATION_FEE)),
                'registration_status': player.registration_status
            }
            
            app.logger.info(f"Status for transaction {transaction_id}: {status}")
            return response
            
    except Exception as e:
        app.logger.error(f"Error in get_payment_status: {str(e)}")
        return None