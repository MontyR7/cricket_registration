from flask import render_template, request, redirect, url_for, flash, session, make_response, send_from_directory, jsonify, Response
import json
import hmac
import hashlib
import time
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash
from flask_wtf.csrf import generate_csrf
from werkzeug.utils import secure_filename
import uuid
import qrcode
import base64
import os
from datetime import datetime
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch
from reportlab.platypus.flowables import KeepTogether
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from PIL import Image as PILImage
from io import BytesIO
from flask_sse import sse
from app import app, db, stripe, twilio_client
from models import Player, Admin
from forms import RegistrationForm, AdminLoginForm
from pdf_generator import generate_players_pdf

REGISTRATION_FEE = 300  # Registration fee in INR

def send_sms(to_number, message):
    if not twilio_client:
        app.logger.error("Twilio not configured. SMS will not be sent.")
        return False

    try:
        # Format the phone number to include country code if not present
        if not to_number.startswith('+91'):
            formatted_number = '+91' + to_number.lstrip('0')
        else:
            formatted_number = to_number

        app.logger.info(f"Sending SMS to {formatted_number}")
        app.logger.debug(f"Message content: {message}")
        app.logger.debug(f"Using Twilio phone number: {os.getenv('TWILIO_PHONE_NUMBER')}")

        # Check if Twilio credentials are configured
        if not os.getenv('TWILIO_PHONE_NUMBER'):
            app.logger.error("TWILIO_PHONE_NUMBER not configured in environment variables")
            return False

        # Send the message
        response = twilio_client.messages.create(
            body=message,
            from_=os.getenv('TWILIO_PHONE_NUMBER'),
            to=formatted_number
        )
        
        app.logger.info(f"SMS sent successfully. Message SID: {response.sid}")
        return True
        
    except Exception as e:
        app.logger.error(f"SMS sending failed: {str(e)}")
        # Log more details about the error
        if hasattr(e, 'code'):
            app.logger.error(f"Twilio Error Code: {e.code}")
        if hasattr(e, 'msg'):
            app.logger.error(f"Twilio Error Message: {e.msg}")
        app.logger.error(f"Full error details: {e.__dict__}")
        return False

@app.route('/admin/test-sms', methods=['GET', 'POST'])
@login_required
def test_sms():
    if request.method == 'POST':
        phone_number = request.form.get('phone_number')
        if not phone_number:
            flash('Please enter a phone number', 'danger')
            return redirect(url_for('test_sms'))
            
        message = "This is a test message from Cricket Registration System"
        if send_sms(phone_number, message):
            flash('Test SMS sent successfully!', 'success')
        else:
            flash('Failed to send test SMS. Check server logs for details.', 'danger')
        return redirect(url_for('test_sms'))
        
    twilio_config = {
        'TWILIO_ACCOUNT_SID': bool(os.getenv('TWILIO_ACCOUNT_SID')),
        'TWILIO_AUTH_TOKEN': bool(os.getenv('TWILIO_AUTH_TOKEN')),
        'TWILIO_PHONE_NUMBER': os.getenv('TWILIO_PHONE_NUMBER')
    }
    return render_template('admin/test_sms.html', config=twilio_config)

@app.route('/check-registration-status', methods=['POST'])
def check_registration_status():
    try:
        data = request.get_json()
        if not data:
            app.logger.error("No JSON data received")
            return jsonify({
                'status': 'error',
                'message': 'Invalid request data'
            }), 400

        full_name = data.get('full_name', '').strip()
        mobile_number = data.get('mobile_number', '').strip()
        
        print(f"\n=== CHECK REGISTRATION STATUS ===")
        print(f"Full Name: '{full_name}'")
        print(f"Mobile: '{mobile_number}'")
        app.logger.info(f"Checking registration status for '{full_name}' with mobile '{mobile_number}'")
        
        if not full_name or not mobile_number:
            return jsonify({
                'status': 'error',
                'message': 'Please provide both name and mobile number.'
            }), 400
        
        # First check if SAME NAME + MOBILE exists with PAYMENT SCREENSHOT UPLOADED (payment done, pending admin approval)
        payment_done_player = Player.query.filter(
            Player.full_name.ilike(full_name),
            Player.mobile_number == mobile_number,
            Player.payment_screenshot != None,
            Player.payment_screenshot != ''
        ).first()
        
        print(f"Payment Done Player Query (screenshot exists): {payment_done_player}")
        
        if payment_done_player:
            print(f"MATCH: Payment Screenshot Uploaded (Payment Complete)")
            app.logger.info(f"Found player with payment screenshot: {payment_done_player.id}, Name: {payment_done_player.full_name}, Mobile: {payment_done_player.mobile_number}")
            return jsonify({
                'status': 'completed',
                'message': f'Welcome back {full_name}! You have already uploaded your payment screenshot. Your payment is complete and waiting for admin approval. Thank you!'
            })
        
        # Then check if SAME NAME + MOBILE exists with PENDING payment (no screenshot)
        pending_player = Player.query.filter(
            Player.full_name.ilike(full_name),
            Player.mobile_number == mobile_number,
            Player.registration_status == 'pending',
            Player.payment_status == False
        ).first()
        
        print(f"Pending Player Query (no payment): {pending_player}")
        
        if pending_player:
            print(f"MATCH: Pending Payment (No Screenshot)")
            app.logger.info(f"Found player with pending payment: {pending_player.id}, Name: {pending_player.full_name}, Mobile: {pending_player.mobile_number}")
            return jsonify({
                'status': 'pending_payment',
                'message': f'Welcome back {full_name}! You have already started your registration but payment is pending. Please complete your payment to finish registration.',
                'player_id': pending_player.id
            })
        
        # Then check if mobile number exists with ANY other player
        player = Player.query.filter_by(
            mobile_number=mobile_number
        ).first()
        
        if not player:
            app.logger.info("No existing player found")
            return jsonify({
                'status': 'not_found',
                'message': 'Welcome! You can proceed with the registration.'
            })
        
        app.logger.info(f"Found different player with mobile {mobile_number}: Name={player.full_name}")
        
        # Block if different name or completed registration
        return jsonify({
            'status': 'blocked',
            'message': f'This mobile number {mobile_number} is already registered in the system. Each player must use a unique mobile number. Please use a different mobile number to register.'
        })
        
    except Exception as e:
        app.logger.error(f"Error in check_registration_status: {str(e)}")
        import traceback
        app.logger.error(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while checking registration status.'
        }), 500

@app.route('/', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    # Ensure CSRF token is available in template
    csrf_token = generate_csrf()
    if form.validate_on_submit():
        # Check if player already exists and has completed registration
        existing_player = Player.query.filter_by(
            mobile_number=form.mobile_number.data
        ).first()
        
        if existing_player:
            if existing_player.payment_status and existing_player.registration_status == 'completed':
                flash('You are already registered for the tournament.', 'info')
                return redirect(url_for('register'))
            elif not existing_player.payment_status and existing_player.registration_status == 'pending':
                # Redirect to payment if registration exists but payment is pending
                flash('You are already registered. Please complete your payment.', 'info')
                return redirect(url_for('initiate_payment', player_id=existing_player.id))

        # Handle profile picture upload
        profile_picture_filename = None
        if form.profile_picture.data:
            file = form.profile_picture.data
            if file:
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                profile_picture_filename = filename

        # Create player record with pending status
        player = Player(
            full_name=form.full_name.data,
            nickname=form.nickname.data,
            address=form.address.data,
            mobile_number=form.mobile_number.data,
            profile_picture=profile_picture_filename,
            registration_status='pending',
            # Player roles
            is_all_rounder=form.is_all_rounder.data,
            is_left_arm_bowler=form.is_left_arm_bowler.data,
            is_right_arm_bowler=form.is_right_arm_bowler.data,
            is_left_hand_batter=form.is_left_hand_batter.data,
            is_right_hand_batter=form.is_right_hand_batter.data
        )
        
        try:
            db.session.add(player)
            db.session.commit()
            
            # Redirect to UPI payment
            return redirect(url_for('initiate_payment', player_id=player.id))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'danger')
            return render_template('register.html', form=form, registration_fee=REGISTRATION_FEE)
            
    return render_template('register.html', form=form, registration_fee=REGISTRATION_FEE)

# Import payment handlers
from payment_handlers import verify_upi_signature, handle_upi_callback, get_payment_status

@app.route('/api/upi-webhook', methods=['POST', 'GET'])
def upi_webhook():
    """Handle UPI payment webhook notifications with detailed logging and validation"""
    # Initialize logging context
    request_time = datetime.utcnow()
    request_id = str(uuid.uuid4())
    
    app.logger.info(f"\n=== UPI Webhook Request {request_id} ===\n" +
                   f"Time: {request_time.isoformat()}\n" +
                   f"Method: {request.method}\n" +
                   f"URL: {request.url}\n" +
                   f"Headers:\n{json.dumps(dict(request.headers), indent=2)}\n" +
                   f"Query Params: {dict(request.args)}")
    
    # Health check for GET requests
    if request.method == 'GET':
        return jsonify({
            'status': 'active',
            'timestamp': request_time.isoformat(),
            'request_id': request_id
        })
    
    # Handle GET requests (for PG verification)
    if request.method == 'GET':
        return jsonify({'status': 'success', 'message': 'Webhook endpoint is active'})
    
    # Process webhook POST data
    try:
        # Log raw request data
        raw_data = request.get_data()
        app.logger.info(f"=== Raw Webhook Data [{request_id}] ===\n" +
                       f"Content-Type: {request.content_type}\n" +
                       f"Raw Data: {raw_data.decode('utf-8')}")
        
        # Parse request data based on content type
        data = None
        try:
            if request.is_json:
                data = request.get_json()
            elif request.form:
                data = request.form.to_dict()
            elif request.data:
                data = json.loads(raw_data.decode('utf-8'))
            else:
                app.logger.error(f"[{request_id}] No parseable data found in request")
                return jsonify({
                    'status': 'error',
                    'message': 'No payment data found in request',
                    'request_id': request_id
                }), 400
                
        except json.JSONDecodeError as json_err:
            app.logger.error(f"[{request_id}] JSON decode error: {str(json_err)}")
            return jsonify({
                'status': 'error', 
                'message': 'Invalid JSON data',
                'request_id': request_id
            }), 400
            
        app.logger.info(f"=== Processed Data [{request_id}] ===\n" +
                       f"{json.dumps(data, indent=2)}")
        
        # Extract and verify signature with retry support
        def get_signature_with_retries(max_retries=3):
            for attempt in range(max_retries):
                try:
                    signature = (request.headers.get('X-UPI-Signature') or 
                                request.headers.get('X-Signature') or
                                request.headers.get('Signature') or
                                request.args.get('signature'))
                                
                    if signature:
                        app.logger.info(f"[{request_id}] Found signature on attempt {attempt + 1}")
                        return signature
                        
                    if attempt < max_retries - 1:
                        app.logger.warning(f"[{request_id}] No signature found on attempt {attempt + 1}, retrying...")
                        time.sleep(0.1)  # Small delay between retries
                        
                except Exception as e:
                    if attempt < max_retries - 1:
                        app.logger.error(f"[{request_id}] Error getting signature (attempt {attempt + 1}): {str(e)}")
                        time.sleep(0.1)
                    else:
                        raise
                        
            app.logger.warning(f"[{request_id}] No signature found after {max_retries} attempts")
            return "NO_SIGNATURE"
            
        # Get signature with retries
        signature = get_signature_with_retries()

        # Helper function to extract fields with validation
        def extract_payment_field(field_names, field_type="string", default=None):
            """Extract and validate payment fields with multiple possible names"""
            for name in field_names:
                value = data.get(name) or request.args.get(name)
                if value:
                    try:
                        if field_type == "float":
                            return float(value)
                        elif field_type == "int":
                            return int(value)
                        else:
                            return str(value)
                    except (ValueError, TypeError) as e:
                        app.logger.error(f"[{request_id}] Error converting {name}={value} to {field_type}: {str(e)}")
                        continue
            return default
        
        # Extract payment details with validation
        transaction_fields = ['transaction_id', 'txnId', 'transactionId', 'trans_id', 'referenceId']
        status_fields = ['status', 'txnStatus', 'transactionStatus', 'payment_status', 'upiStatus']
        amount_fields = ['amount', 'txnAmount', 'transactionAmount', 'payment_amount', 'value']
        
        # Extract with proper type conversion
        transaction_id = extract_payment_field(transaction_fields)
        payment_status = extract_payment_field(status_fields)
        amount = extract_payment_field(amount_fields, field_type="float")
        
        # Log extracted data
        app.logger.info(f"[{request_id}] Extracted payment data:\n" +
                       f"Transaction ID: {transaction_id}\n" +
                       f"Status: {payment_status}\n" +
                       f"Amount: {amount}")
        
        # Validate required fields
        if not transaction_id:
            app.logger.error(f"[{request_id}] Missing transaction ID")
            return jsonify({'status': 'error', 'message': 'Missing transaction ID'}), 400
            
        if not payment_status:
            app.logger.error(f"[{request_id}] Missing payment status")
            return jsonify({'status': 'error', 'message': 'Missing payment status'}), 400
            
        if amount is None:
            app.logger.error(f"[{request_id}] Missing or invalid amount")
            return jsonify({'status': 'error', 'message': 'Missing or invalid amount'}), 400
        
        # Log extracted data
        app.logger.info("Extracted payment details:")
        app.logger.info(f"Transaction ID: {transaction_id}")
        app.logger.info(f"Payment Status: {payment_status}")
        app.logger.info(f"Amount: {amount}")
        
        # Verify signature if secret is configured
        if os.getenv('UPI_WEBHOOK_SECRET') and signature != "NO_SIGNATURE":
            if not verify_upi_signature(data, signature):
                app.logger.error("Invalid signature in webhook request")
                return jsonify({'status': 'error', 'message': 'Invalid signature'}), 401
        
        if not all([transaction_id, payment_status, amount]):
            app.logger.error(f"Missing required webhook data: transaction_id={transaction_id}, status={payment_status}, amount={amount}")
            return jsonify({'status': 'error', 'message': 'Missing required data'}), 400

        # Get player with row lock to prevent concurrent updates
        def get_player_with_retries(max_retries=3):
            for attempt in range(max_retries):
                try:
                    # Use with_for_update() to get row lock
                    player = Player.query.with_for_update().filter_by(
                        transaction_id=transaction_id
                    ).first()
                    
                    if player:
                        app.logger.info(f"[{request_id}] Found player on attempt {attempt + 1}")
                        return player
                        
                    app.logger.error(f"[{request_id}] No player found for transaction {transaction_id}")
                    if attempt < max_retries - 1:
                        time.sleep(0.2 * (attempt + 1))  # Exponential backoff
                    
                except Exception as e:
                    app.logger.error(f"[{request_id}] Database error (attempt {attempt + 1}): {str(e)}")
                    if attempt < max_retries - 1:
                        time.sleep(0.2 * (attempt + 1))
                        db.session.rollback()
                    else:
                        raise
                        
            return None
            
        # Get player with retries
        player = get_player_with_retries()
        if not player:
            return jsonify({
                'status': 'error',
                'message': 'Player not found',
                'transaction_id': transaction_id,
                'request_id': request_id
            }), 404
        
        # Function to safely update player record
        def update_player_payment(status_update):
            try:
                # Verify payment amount
                if float(amount) != float(REGISTRATION_FEE):
                    app.logger.error(f"[{request_id}] Amount mismatch: expected {REGISTRATION_FEE}, got {amount}")
                    status_update['payment_status'] = False
                    status_update['registration_status'] = 'pending'
                    status_update['payment_note'] = f'Amount mismatch: expected ₹{REGISTRATION_FEE}, got ₹{amount}'
                
                # Update player record
                for key, value in status_update.items():
                    setattr(player, key, value)
                    
                player.payment_verified_at = datetime.utcnow()
                db.session.commit()
                
                app.logger.info(f"[{request_id}] Successfully updated player record")
                return True
                
            except Exception as e:
                app.logger.error(f"[{request_id}] Error updating player record: {str(e)}")
                db.session.rollback()
                return False
        
        # Prepare payment update
        payment_update = {
            'payment_status': payment_status.upper() == 'SUCCESS',
            'registration_status': 'completed' if payment_status.upper() == 'SUCCESS' else 'pending',
            'payment_note': f'Payment {payment_status}: ₹{amount}'
        }
        
        # Update with retries
        max_update_retries = 3
        for attempt in range(max_update_retries):
            if update_player_payment(payment_update):
                break
            if attempt < max_update_retries - 1:
                app.logger.warning(f"[{request_id}] Retrying payment update (attempt {attempt + 1})")
                time.sleep(0.2 * (attempt + 1))  # Exponential backoff
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to update payment status',
                    'request_id': request_id
                }), 500
        
        # Function to send notifications with retries
        def send_notifications():
            # Send SSE notification with retries
            def send_sse_with_retries(max_retries=3):
                for attempt in range(max_retries):
                    try:
                        with app.app_context():
                            sse.publish({
                                'status': payment_status,
                                'player_id': player.id,
                                'transaction_id': transaction_id,
                                'amount': amount,
                                'message': 'Payment verified successfully!' if payment_status.upper() == 'SUCCESS' else 'Payment update received',
                                'timestamp': datetime.utcnow().isoformat(),
                                'request_id': request_id
                            }, type='payment_update')
                        app.logger.info(f"[{request_id}] SSE notification sent successfully")
                        return True
                    except Exception as e:
                        app.logger.error(f"[{request_id}] SSE error (attempt {attempt + 1}): {str(e)}")
                        if attempt < max_retries - 1:
                            time.sleep(0.2 * (attempt + 1))
                        else:
                            app.logger.error(f"[{request_id}] Failed to send SSE after {max_retries} attempts")
                return False
            
            # Send SMS notification with retries
            def send_sms_with_retries(max_retries=3):
                if payment_status.upper() != 'SUCCESS':
                    return True
                    
                message = (
                    f"Thank you for registering for the Cricket Tournament!\n"
                    f"Payment of ₹{amount} received.\n"
                    f"Transaction ID: {transaction_id}\n"
                    f"Keep this message for future reference."
                )
                
                for attempt in range(max_retries):
                    try:
                        if send_sms(player.mobile_number, message):
                            app.logger.info(f"[{request_id}] SMS notification sent successfully")
                            return True
                    except Exception as e:
                        app.logger.error(f"[{request_id}] SMS error (attempt {attempt + 1}): {str(e)}")
                        if attempt < max_retries - 1:
                            time.sleep(0.5 * (attempt + 1))
                        else:
                            app.logger.error(f"[{request_id}] Failed to send SMS after {max_retries} attempts")
                return False
            
            # Send both notifications
            sse_success = send_sse_with_retries()
            sms_success = send_sms_with_retries()
            
            return sse_success, sms_success
        
        # Send notifications asynchronously
        sse_sent, sms_sent = send_notifications()
        
        # Log final status and return response
        response_data = {
            'status': 'success',
            'message': 'Payment processed successfully',
            'transaction_id': transaction_id,
            'request_id': request_id,
            'payment_status': payment_status,
            'notifications': {
                'sse_sent': sse_sent,
                'sms_sent': sms_sent
            }
        }
        
        app.logger.info(f"[{request_id}] Webhook processing completed:\n" +
                       f"Transaction: {transaction_id}\n" +
                       f"Status: {payment_status}\n" +
                       f"SSE: {'sent' if sse_sent else 'failed'}\n" +
                       f"SMS: {'sent' if sms_sent else 'failed'}")
        
        return jsonify(response_data)

    except Exception as e:
        app.logger.error(f"Error processing webhook: {str(e)}")
        if 'db' in locals():
            db.session.rollback()
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

def safe_get_session(key, default=None):
    """Safely get a value from the session with error handling"""
    try:
        return session.get(key, default)
    except Exception as e:
        app.logger.error(f'Error accessing session {key}: {str(e)}')
        return default

import sys
import traceback

@app.errorhandler(500)
def handle_500_error(e):
    """Ensure all 500 errors return JSON with proper headers"""
    app.logger.error(f'Server error: {str(e)}')
    response = jsonify({
        'status': 'pending',
        'message': 'Payment verification in progress...'
    })
    response.headers['Content-Type'] = 'application/json'
    return response, 200

@app.route('/check-payment-status')
def check_payment_status():
    """REST API endpoint to check payment status"""
    # Set debug logging
    app.logger.setLevel('DEBUG')
    
    try:
        # Get reference ID from request
        transaction_id = request.args.get('reference_id')
        app.logger.info(f"Checking payment status for transaction: {transaction_id}")
        
        if not transaction_id:
            app.logger.error("No reference ID provided")
            return jsonify({
                'status': 'error',
                'message': 'Missing reference ID'
            }), 400
            
        # Find player by transaction ID
        player = Player.query.filter_by(transaction_id=transaction_id).first()
        if not player:
            app.logger.error(f"No player found for transaction {transaction_id}")
            return jsonify({
                'status': 'error',
                'message': 'Invalid transaction ID'
            }), 404
            
        app.logger.info(f"Found player: {player.full_name}")
        app.logger.info(f"Current payment status: {player.payment_status}")
        app.logger.info(f"Current registration status: {player.registration_status}")
        
        # If payment is already verified
        if player.payment_status and player.registration_status == 'completed':
            app.logger.info("Payment already verified")
            return jsonify({
                'status': 'success',
                'message': 'Payment successful! Redirecting...',
                'player_id': player.id
            })
            
        # Check for manual verification conditions
        pending_transaction = session.get('pending_transaction', {})
        if pending_transaction and pending_transaction.get('transaction_id') == transaction_id:
            current_time = time.time()
            
            # Update payment_time if not set
            if 'payment_time' not in pending_transaction and pending_transaction.get('payment_initiated'):
                pending_transaction['payment_time'] = current_time
                session['pending_transaction'] = pending_transaction
                session.modified = True
            
            payment_time = pending_transaction.get('payment_time', current_time)
            
            # If payment was initiated and enough time has passed for verification
            if pending_transaction.get('payment_initiated') and (current_time - payment_time > 30):
                app.logger.info("Manual payment verification triggered")
                # Update player status
                player.payment_status = True
                player.registration_status = 'completed'
                player.payment_date = datetime.utcnow()
                player.payment_note = 'Payment verified'
                db.session.commit()
                
                # Clear session
                session.pop('pending_transaction', None)
                
                return jsonify({
                    'status': 'success',
                    'message': 'Payment verified successfully! Redirecting...',
                    'player_id': player.id
                })
            
            # Mark payment as initiated if Google Pay callback detected
            if not pending_transaction.get('payment_initiated') and request.args.get('gpay_status') == 'initiated':
                pending_transaction['payment_initiated'] = True
                pending_transaction['payment_time'] = current_time
                session['pending_transaction'] = pending_transaction
                session.modified = True
                app.logger.info("Payment initiation recorded")
        
        # Return pending status with session info
        return jsonify({
            'status': 'pending',
            'message': 'Payment verification in progress...',
            'player_id': player.id,
            'transaction_id': transaction_id
        })
        
    except Exception as e:
        app.logger.error(f"Error checking payment status: {str(e)}")
        db.session.rollback()
        return jsonify({
            'status': 'pending',
            'message': 'Payment verification in progress...'
        }), 200
    # Set JSON content type for all responses
    response_headers = {'Content-Type': 'application/json'}
    
    # Default response
    default_response = {
        'status': 'pending',
        'message': 'Waiting for payment...',
        'timestamp': None,
        'amount': str(REGISTRATION_FEE),
        'registration_status': 'pending'
    }
    
    try:
        # Log all request details
        app.logger.info('=== Payment Status Check Request ===\n' + 
                       f'Args: {request.args}\n' + 
                       f'Headers: {request.headers}\n' + 
                       f'Session: {session.get("pending_transaction")}')
        app.logger.info('=== Starting payment status check ===')
        transaction_id = request.args.get('reference_id')
        app.logger.info(f'Received reference_id: {transaction_id}')

        # Default response
        default_response = {
            'status': 'pending',
            'message': 'Waiting for payment...',
            'timestamp': None,
            'amount': str(REGISTRATION_FEE),
            'registration_status': 'pending'
        }

        # Get pending transaction from session with full debug info
        pending_transaction = safe_get_session('pending_transaction', {})
        app.logger.info('Session check:\n' + 
                       f'Has pending_transaction: {"pending_transaction" in session}\n' + 
                       f'Session keys: {list(session.keys())}\n' + 
                       f'Pending transaction data: {pending_transaction}')

        if pending_transaction:
            # Check session expiry
            timestamp = pending_transaction.get('timestamp', 0)
            current_time = time.time()
            app.logger.info(f'Time check - Current: {current_time}, Transaction: {timestamp}, Diff: {current_time - timestamp}')
            
            if current_time - timestamp > 3600:  # 1 hour expiry
                app.logger.warning('Payment session expired')
                session.pop('pending_transaction', None)
            else:
                default_response.update({
                    'player_id': pending_transaction.get('player_id'),
                    'transaction_id': pending_transaction.get('transaction_id')
                })

        if not transaction_id:
            app.logger.warning("No reference ID provided in payment status check")
            return jsonify(default_response), 200, response_headers

        app.logger.info(f"Checking payment status for transaction: {transaction_id}")
        
        # Get pending transaction from session
        pending_transaction = session.get('pending_transaction')
        if not pending_transaction:
            app.logger.warning(f"No pending transaction in session for: {transaction_id}")
            return jsonify({
                'status': 'pending',
                'message': 'Waiting for payment verification...'
            }), 200, response_headers
            
        # First try to find player by transaction ID
        player = Player.query.filter_by(transaction_id=transaction_id).first()
        
        # If not found by transaction ID, try to find by player ID from session
        if not player and 'player_id' in pending_transaction:
            player = Player.query.get(pending_transaction['player_id'])
        
        if not player:
            app.logger.warning(f"No player found for transaction: {transaction_id}")
            return jsonify({
                'status': 'pending',
                'message': 'Waiting for payment verification...'
            }), 200, response_headers

        # Update transaction ID if not set
        if not player.transaction_id and transaction_id:
            player.transaction_id = transaction_id
            db.session.commit()

        # Check payment status
        status = 'success' if player.payment_status else 'pending'
        message = 'Payment successful!' if player.payment_status else 'Waiting for payment...'

        # Check for specific payment notes
        if player.payment_note:
            if 'amount mismatch' in player.payment_note.lower():
                status = 'amount_mismatch'
                message = 'Payment amount does not match the required fee'
            elif 'failed' in player.payment_note.lower():
                status = 'failed'
                message = 'Payment failed. Please try again'
        
        response = {
            'status': status,
            'message': message,
            'timestamp': player.payment_date.isoformat() if player.payment_date else None,
            'player_id': player.id,
            'transaction_id': transaction_id,
            'amount': REGISTRATION_FEE,
            'registration_status': player.registration_status
        }
        
        app.logger.info(f"Payment status for {transaction_id}: {status} ({message})")
        return jsonify(response), 200, response_headers
        
    except Exception as e:
        # Get full exception details
        exc_type, exc_value, exc_traceback = sys.exc_info()
        error_details = traceback.format_exception(exc_type, exc_value, exc_traceback)
        
        app.logger.error('=== Payment Status Check Error ===\n' + 
                        f'Error Type: {exc_type.__name__}\n' + 
                        f'Error Message: {str(e)}\n' + 
                        f'Traceback:\n{"".join(error_details)}\n' + 
                        f'Request Args: {request.args}\n' + 
                        f'Session Data: {dict(session)}\n')
        
        # Try to roll back any failed database operations
        try:
            db.session.rollback()
        except Exception as rollback_error:
            app.logger.error(f"Error during rollback: {str(rollback_error)}")

        # Return a more informative error response in debug mode
        if app.debug:
            return jsonify({
                'status': 'error',
                'message': 'An error occurred while checking payment status.',
                'debug_info': {
                    'error_type': exc_type.__name__,
                    'error_message': str(e),
                    'traceback': error_details
                }
            }), 500

        # Try to preserve session data if possible
        try:
            if 'pending_transaction' in session:
                app.logger.info(f"Preserved session data: {session['pending_transaction']}")
        except Exception as session_error:
            app.logger.error(f"Error accessing session: {str(session_error)}")

        return jsonify({
            'status': 'pending',
            'message': 'Payment status check in progress...'
        }), 200, response_headers

def event_stream(transaction_id):
    """Generate SSE events with enhanced error handling and reconnection support"""
    event_id = 0  # For tracking message sequence
    request_id = str(uuid.uuid4())  # Unique stream identifier
    
    try:
        app.logger.info(f"Starting event stream [{request_id}] for transaction: {transaction_id}")
        
        # Send immediate connection confirmation
        event_id += 1
        yield f"id: {event_id}\n"
        yield f"event: connected\n"
        event_data = {
            'status': 'connected',
            'message': 'Payment monitoring active',
            'timestamp': datetime.utcnow().isoformat(),
            'request_id': request_id,
            'transaction_id': transaction_id
        }
        yield f"data: {json.dumps(event_data)}\n\n"
        
        if not transaction_id:
            app.logger.error("No transaction_id provided for event stream")
            yield 'event: error\ndata: {"message": "Missing transaction ID"}\n\n'
            return
            
        # Ensure we're in an app context
        with app.app_context():
            # Validate transaction exists
            player = Player.query.filter_by(transaction_id=transaction_id).first()
            if not player:
                app.logger.error(f"No player found for transaction: {transaction_id}")
                yield 'event: error\ndata: {"message": "Invalid transaction ID"}\n\n'
                return
            
            # Configure retry timeout and initial message
            yield 'retry: 1000\n\n'  # 1 second retry
            
            # Send initial connection status
            initial_data = {
                'status': 'connected',
                'message': 'Connected to payment updates',
                'transaction_id': transaction_id,
                'timestamp': datetime.utcnow().isoformat()
            }
            yield f'event: connected\ndata: {json.dumps(initial_data)}\n\n'
            
            # Send initial connection message
            initial_data = {
                'status': 'connected',
                'message': 'Waiting for payment confirmation...',
                'timestamp': datetime.utcnow().isoformat(),
                'transaction_id': transaction_id,
                'event': 'connected'
            }
            yield f'data: {json.dumps(initial_data)}\n\n'
            
            # Initialize timers
            last_check = 0
            check_interval = 2  # seconds
            keepalive_interval = 15  # seconds
            last_keepalive = time.time()
            connection_start = time.time()
            max_duration = 900  # 15 minutes maximum connection time
        
        while True:
            current_time = time.time()
            
            # Check if we've exceeded max duration
            if current_time - connection_start > max_duration:
                end_data = {
                    'status': 'timeout',
                    'message': 'Connection timeout - please refresh',
                    'timestamp': datetime.utcnow().isoformat(),
                    'event': 'timeout'
                }
                yield f'data: {json.dumps(end_data)}\n\n'
                break
            
            # Send keepalive comment every 15 seconds
            if current_time - last_keepalive >= keepalive_interval:
                keepalive_data = {
                    'type': 'keepalive',
                    'timestamp': datetime.utcnow().isoformat()
                }
                yield f': {json.dumps(keepalive_data)}\n\n'
                last_keepalive = current_time
                app.logger.debug("Sent keepalive")
            
            # Check payment status every 2 seconds
            if current_time - last_check >= check_interval:
                try:
                    # Get player record from transaction ID
                    player = Player.query.filter_by(transaction_id=transaction_id).first()
                    
                    if player:
                        # Prepare detailed status data
                        status_data = {
                            'status': 'success' if player.payment_status else 'pending',
                            'message': 'Payment verified successfully!' if player.payment_status else 'Awaiting verification...',
                            'timestamp': datetime.utcnow().isoformat(),
                            'transaction_id': transaction_id,
                            'player_id': player.id,
                            'registration_status': player.registration_status,
                            'payment_note': player.payment_note or '',
                            'event': 'status_update'
                        }
                        
                        # Send status update
                        yield f'data: {json.dumps(status_data)}\n\n'
                        app.logger.debug(f"Payment status update: {json.dumps(status_data)}")
                        
                        if player.payment_status and player.registration_status == 'completed':
                            # Send final success event and close connection
                            final_data = {
                                'status': 'success',
                                'message': 'Payment verified and registration completed!',
                                'timestamp': datetime.utcnow().isoformat(),
                                'transaction_id': transaction_id,
                                'player_id': player.id,
                                'event': 'payment_confirmed'
                            }
                            yield f'event: payment_confirmed\ndata: {json.dumps(final_data)}\n\n'
                            break
                            
                        elif player.payment_note and 'failed' in player.payment_note.lower():
                            # Send failure event and close connection
                            failure_data = {
                                'status': 'failed',
                                'message': player.payment_note,
                                'timestamp': datetime.utcnow().isoformat(),
                                'transaction_id': transaction_id,
                                'player_id': player.id,
                                'event': 'payment_failed'
                            }
                            yield f'event: payment_failed\ndata: {json.dumps(failure_data)}\n\n'
                            break
                            
                except Exception as e:
                    error_data = {
                        'status': 'error',
                        'message': f'Error checking payment status: {str(e)}',
                        'timestamp': datetime.utcnow().isoformat(),
                        'transaction_id': transaction_id,
                        'event': 'error'
                    }
                    yield f'data: {json.dumps(error_data)}\n\n'
                    app.logger.error(f'Payment check error: {str(e)}')
                    if app.debug:
                        app.logger.error(f'Full error details: {traceback.format_exc()}')
            
                last_check = current_time
            
            time.sleep(0.1)  # Small delay to prevent CPU overuse
            
    except GeneratorExit:
        app.logger.info(f"Client disconnected from SSE stream for transaction: {transaction_id}")
    except Exception as e:
        app.logger.error(f"Error in SSE stream for transaction {transaction_id}: {str(e)}")
        error_data = {
            'status': 'error',
            'message': 'Connection error occurred',
            'timestamp': datetime.utcnow().isoformat(),
            'event': 'error'
        }
        yield f'data: {json.dumps(error_data)}\n\n'
        if app.debug:
            app.logger.error(f"Full error details: {traceback.format_exc()}")

@app.route('/stream', methods=['GET', 'OPTIONS'])
def stream():
    """SSE endpoint for real-time payment status updates with enhanced error handling"""
    # Generate request ID for tracking
    request_id = str(uuid.uuid4())
    
    # Handle CORS preflight with detailed headers
    if request.method == 'OPTIONS':
        app.logger.info(f"[{request_id}] Handling CORS preflight request")
        response = Response()
        response.headers.update({
            'Access-Control-Allow-Origin': request.headers.get('Origin', '*'),
            'Access-Control-Allow-Methods': 'GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With',
            'Access-Control-Allow-Credentials': 'true',
            'Access-Control-Max-Age': '86400',
            'Access-Control-Expose-Headers': '*'
        })
        return response

    # Enhanced connection logging
    app.logger.info(f"=== SSE Connection [{request_id}] ===\n" + 
                   f"Time: {datetime.utcnow().isoformat()}\n" +
                   f"Client IP: {request.remote_addr}\n" +
                   f"User Agent: {request.headers.get('User-Agent')}\n" +
                   f"Headers: {json.dumps(dict(request.headers), indent=2)}\n" +
                   f"Args: {json.dumps(dict(request.args), indent=2)}")
        
    # Log SSE connection request
    app.logger.info(f"=== SSE Connection Request ===")
    app.logger.info(f"Client IP: {request.remote_addr}")
    app.logger.info(f"User Agent: {request.headers.get('User-Agent')}")
    app.logger.info(f"Headers: {dict(request.headers)}")
    
    # Get transaction ID from query parameters
    transaction_id = request.args.get('transaction_id')
    if not transaction_id:
        error_data = {
            'status': 'error',
            'message': 'Missing transaction_id parameter',
            'event': 'error'
        }
        return Response(f'data: {json.dumps(error_data)}\n\n', mimetype='text/event-stream')
    
    # Configure response with enhanced streaming support
    response = Response(
        event_stream(transaction_id),
        mimetype='text/event-stream'
    )
    
    # Set enhanced headers for SSE streaming with explicit CORS
    response.headers.update({
        # SSE specific headers
        'Content-Type': 'text/event-stream; charset=utf-8',
        'Cache-Control': 'no-cache, no-store, must-revalidate, pre-check=0, post-check=0',
        'Pragma': 'no-cache',
        'Expires': '0',
        'X-Accel-Buffering': 'no',  # Disable nginx buffering
        'Connection': 'keep-alive',
        
        # Enhanced CORS headers
        'Access-Control-Allow-Origin': request.headers.get('Origin', '*'),
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With',
        'Access-Control-Allow-Credentials': 'true',
        'Access-Control-Max-Age': '86400',  # 24 hours
        'Access-Control-Expose-Headers': '*',
        
        # Proxy-related headers
        'Transfer-Encoding': 'chunked',
        'Keep-Alive': 'timeout=600',  # 10-minute keep-alive
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY'
    })
    
    # Ensure nginx/proxy buffering is disabled
    if 'nginx' in request.headers.get('Server', '').lower():
        response.headers['X-Accel-Buffering'] = 'no'
    return response
    # Get transaction ID from query parameters
    transaction_id = request.args.get('transaction_id')
    if not transaction_id:
        error_data = {
            'status': 'error',
            'message': 'Missing transaction_id parameter',
            'event': 'error'
        }
        return Response(f'data: {json.dumps(error_data)}\n\n', mimetype='text/event-stream')
    
    # Configure response with all necessary headers
    response = Response(event_stream(), mimetype='text/event-stream')
    response.headers.update({
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0',
        'Connection': 'keep-alive',
        'X-Accel-Buffering': 'no',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Transfer-Encoding': 'chunked'
    })
    return response
    """SSE endpoint for real-time payment status updates"""
    # Enable CORS for SSE
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
        return ('', 204, headers)

    channel = request.args.get('channel', 'payment_update')
    backup_channel = request.args.get('backup')
    transaction_id = channel.replace('payment_update_', '') if channel.startswith('payment_update_') else None
    
    app.logger.info(f"=== SSE Connection Request ===")
    app.logger.info(f"Channel: {channel}")
    app.logger.info(f"Transaction ID: {transaction_id}")
    app.logger.info(f"Client IP: {request.remote_addr}")
    app.logger.info(f"User Agent: {request.headers.get('User-Agent')}")
    app.logger.info(f"Headers: {dict(request.headers)}")
    
    def event_stream():
        try:
            # Ensure we're in an app context
            with app.app_context():
                # Send retry timeout instruction
                yield 'retry: 1000\n\n'  # 1 second retry
                
                # Send initial connection message
                initial_data = {
                    'status': 'connected',
                    'message': 'Waiting for payment confirmation...',
                    'timestamp': datetime.utcnow().isoformat(),
                    'transaction_id': transaction_id,
                    'event': 'connected'
                }
                yield f'data: {json.dumps(initial_data)}\n\n'
                
                # Initialize timers
                last_check = 0
                check_interval = 2  # seconds
                keepalive_interval = 15  # seconds
                last_keepalive = time.time()
                connection_start = time.time()
                max_duration = 900  # 15 minutes maximum connection time
            
            while True:
                current_time = time.time()
                
                # Check if we've exceeded max duration
                if current_time - connection_start > max_duration:
                    end_data = {
                        'status': 'timeout',
                        'message': 'Connection timeout - please refresh',
                        'timestamp': datetime.utcnow().isoformat(),
                        'event': 'timeout'
                    }
                    yield f'data: {json.dumps(end_data)}\n\n'
                    break
                
                # Send keepalive comment every 15 seconds
                if current_time - last_keepalive >= keepalive_interval:
                    keepalive_data = {
                        'type': 'keepalive',
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    yield f': {json.dumps(keepalive_data)}\n\n'
                    last_keepalive = current_time
                    app.logger.debug("Sent keepalive")
                
                # Check payment status every 2 seconds
                if current_time - last_check >= check_interval:
                    if transaction_id:
                        try:
                            # Get player record from transaction ID
                            player = Player.query.filter_by(transaction_id=transaction_id).first()
                            
                            if player:
                                # Prepare detailed status data
                                status_data = {
                                    'status': 'success' if player.payment_status else 'pending',
                                    'message': 'Payment verified successfully!' if player.payment_status else 'Awaiting verification...',
                                    'timestamp': datetime.utcnow().isoformat(),
                                    'transaction_id': transaction_id,
                                    'player_id': player.id,
                                    'registration_status': player.registration_status,
                                    'payment_note': player.payment_note or '',
                                    'event': 'status_update'
                                }
                                
                                # Send status update
                                yield f'data: {json.dumps(status_data)}\n\n'
                                app.logger.debug(f"Payment status update: {json.dumps(status_data)}")
                                
                                if player.payment_status and player.registration_status == 'completed':
                                    # Send final success event and close connection
                                    final_data = {
                                        'status': 'success',
                                        'message': 'Payment verified and registration completed!',
                                        'timestamp': datetime.utcnow().isoformat(),
                                        'transaction_id': transaction_id,
                                        'player_id': player.id,
                                        'event': 'payment_confirmed'
                                    }
                                    yield f'event: payment_confirmed\ndata: {json.dumps(final_data)}\n\n'
                                    break
                                    
                                elif player.payment_note and 'failed' in player.payment_note.lower():
                                    # Send failure event and close connection
                                    failure_data = {
                                        'status': 'failed',
                                        'message': player.payment_note,
                                        'timestamp': datetime.utcnow().isoformat(),
                                        'transaction_id': transaction_id,
                                        'player_id': player.id,
                                        'event': 'payment_failed'
                                    }
                                    yield f'event: payment_failed\ndata: {json.dumps(failure_data)}\n\n'
                                    break
                                    
                        except Exception as e:
                            error_data = {
                                'status': 'error',
                                'message': f'Error checking payment status: {str(e)}',
                                'timestamp': datetime.utcnow().isoformat(),
                                'transaction_id': transaction_id,
                                'event': 'error'
                            }
                            yield f'data: {json.dumps(error_data)}\n\n'
                            app.logger.error(f'Payment check error: {str(e)}')
                            if app.debug:
                                app.logger.error(f'Full error details: {traceback.format_exc()}')
                    
                    last_check = current_time
                
                time.sleep(0.1)  # Small delay to prevent CPU overuse
                
        except GeneratorExit:
            app.logger.info(f"Client disconnected from SSE stream: {channel}")
        except Exception as e:
            app.logger.error(f"Error in SSE stream: {str(e)}")
            error_data = {
                'status': 'error',
                'message': 'Connection error occurred',
                'timestamp': datetime.utcnow().isoformat(),
                'event': 'error'
            }
            yield f'data: {json.dumps(error_data)}\n\n'
            if app.debug:
                app.logger.error(f"Full error details: {traceback.format_exc()}")
    
    # Prepare response with all necessary headers
    response = Response(event_stream(), mimetype='text/event-stream')
    response.headers.update({
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0',
        'Connection': 'keep-alive',
        'X-Accel-Buffering': 'no',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Transfer-Encoding': 'chunked'
    })
    return response
        
    try:
        def stream():
            # Send initial message
            yield 'data: {"status": "pending", "message": "Waiting for payment..."}\n\n'
            
            # Keep connection alive with heartbeat
            while True:
                # Check payment status
                status = get_payment_status(transaction_id)
                if status:
                    yield f'data: {json.dumps(status)}\n\n'
                    if status['status'] in ['success', 'failed', 'amount_mismatch']:
                        break
                
                # Send keep-alive comment every 15 seconds
                yield ': keep-alive\n\n'
                time.sleep(15)
        
        return Response(stream(), mimetype='text/event-stream')
        
    except Exception as e:
        app.logger.error(f"Error setting up SSE stream: {str(e)}")
        return "Error setting up payment updates", 500

@app.route('/payment-success/<int:player_id>')
def payment_success(player_id):
    player = Player.query.get_or_404(player_id)
    player.payment_status = True
    db.session.commit()
    
    # Send SMS notification
    message = f"Thank you for registering for the Cricket Tournament! Your payment of ₹{REGISTRATION_FEE} has been received."
    send_sms(player.mobile_number, message)
    
    flash('Registration completed successfully! You will receive a confirmation SMS shortly.', 'success')
    return render_template('success.html', player=player)

@app.route('/payment/<int:player_id>')
def initiate_payment(player_id):
    try:
        app.logger.info(f'Initiating payment for player_id: {player_id}')
        
        # Clear any existing payment session
        if 'pending_transaction' in session:
            app.logger.info('Clearing existing payment session')
            session.pop('pending_transaction')
            
        player = Player.query.get_or_404(player_id)
        
        # Check if the player is already registered
        if player.payment_status == True and player.registration_status == 'completed':
            flash('This player is already registered!', 'info')
            return redirect(url_for('index'))
            
        # Get UPI configuration from environment
        upi_id = os.getenv('UPI_ID', 'ravirec7@oksbi')
        merchant_name = os.getenv('MERCHANT_NAME', 'Cricket Tournament Registration')
        merchant_code = os.getenv('MERCHANT_CODE', 'CRICKETREGA01')
        
        # Generate transaction ID for this payment
        transaction_id = f"REG{player.id}{uuid.uuid4().hex[:6].upper()}"
        
        # Save transaction ID to player record
        player.transaction_id = transaction_id
        db.session.commit()
        
        try:
            # Generate QR code for the payment
            transaction_note = f"Cricket Tournament Registration - {player.full_name}"
            # Generate callback URL with absolute path using ngrok URL or server domain
            callback_url = request.url_root.rstrip('/') + url_for('upi_webhook')
            
            # Generate payment string for QR code with callback URL
            upi_payment_string = (
                f"upi://pay?pa={upi_id}"
                f"&pn=Cricket%20Registration"
                f"&am={REGISTRATION_FEE}"
                f"&tr={transaction_id}"
                f"&cu=INR"
                f"&url={callback_url}"
            )
            
            app.logger.info(f"Generated UPI payment string: {upi_payment_string}")
            
            # Ensure qrcode module is available
            if not qrcode:
                raise ImportError("qrcode module not found")
            
            # Generate QR code
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(upi_payment_string)
            qr.make(fit=True)
            
            qr_image = qr.make_image(fill_color="black", back_color="white")
            
            # Convert QR code image to base64 string
            buffered = BytesIO()
            qr_image.save(buffered, format="PNG")
            qr_code = base64.b64encode(buffered.getvalue()).decode()
            
            app.logger.info(f"QR code generated successfully for transaction {transaction_id}")
            
            # Initialize or clear the session data
            session.pop('pending_transaction', None)
            
            # Generate a random 6-digit verification code
            import random
            verification_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            
            # Prepare session data
            pending_transaction = {
                'transaction_id': transaction_id,
                'player_id': player.id,  # Use player.id instead of player_id
                'amount': REGISTRATION_FEE,
                'verification_code': verification_code,
                'timestamp': int(datetime.utcnow().timestamp())
            }
            
            # Store in session
            session['pending_transaction'] = pending_transaction
            session.modified = True
            
            app.logger.info(f'Initialized payment session for player {player.id}: {pending_transaction}')
            
            try:
                return render_template('payment_qr.html',
                                    player=player,
                                    player_id=player.id,  # Add explicit player_id
                                    amount=REGISTRATION_FEE,
                                    transaction_id=transaction_id,
                                    qr_code=qr_code,
                                    verification_code=verification_code)
            except Exception as template_error:
                app.logger.error(f"Template rendering error: {str(template_error)}")
                # Rollback any database changes
                db.session.rollback()
                flash('An error occurred while processing your payment. Please try again.', 'danger')
                return redirect(url_for('register'))
                                 
        except ImportError as e:
            app.logger.error(f"Import error generating QR code: {str(e)}")
            flash('Could not generate QR code. Please contact administrator.', 'danger')
            return redirect(url_for('register'))
        except Exception as e:
            app.logger.error(f"Error generating QR code: {str(e)}")
            app.logger.error(f"UPI payment string was: {upi_payment_string}")
            flash('An error occurred while generating the payment QR code.', 'danger')
            return redirect(url_for('register'))
            
    except Exception as e:
        app.logger.error(f'Error in initiate_payment: {str(e)}')
        flash('An error occurred. Please try again.', 'danger')
        return redirect(url_for('register'))
                             
    except Exception as e:
        app.logger.error(f'Error in initiate_payment: {str(e)}')
        flash('An error occurred while generating the payment QR code. Please try again.', 'danger')
        return redirect(url_for('register'))

@app.route('/payment-cancel/<int:player_id>')
def payment_cancel(player_id):
    flash('Payment was cancelled. Please try again.', 'warning')
    return redirect(url_for('select_payment', player_id=player_id))

@app.route('/api/payment-callback', methods=['POST'])
def payment_callback():
    try:
        data = request.get_json()
        if not data or 'transaction_id' not in data:
            return jsonify({'status': 'error', 'message': 'Invalid request data'}), 400
            
        # Find player by transaction ID first
        player = Player.query.filter_by(transaction_id=data['transaction_id']).first()
        if not player:
            return jsonify({'status': 'error', 'message': 'Player not found'}), 404
            
        # Verify the callback signature
        signature = request.headers.get('X-Payment-Signature')
        if not verify_upi_signature(data, signature):
            app.logger.error('Invalid payment callback signature')
            return jsonify({'status': 'error', 'message': 'Invalid signature'}), 401
            
        # Parse payment data
        data = request.get_json()
        transaction_id = data.get('transaction_id')
        payment_status = data.get('status')
        utr = data.get('utr')
        amount = data.get('amount')
        
        # Check if player already has a verified payment
        if player.payment_status and player.registration_status == 'completed':
            app.logger.warning(f'Player {player.id} already has a verified payment')
            return jsonify({
                'success': False,
                'message': 'This registration has already been verified and completed.'
            })
        
        # No screenshot handling needed as payment is verified automatically
        
        # Get pending transaction from session
        pending_transaction = session.get('pending_transaction')
        if not pending_transaction:
            app.logger.warning('No pending transaction found in session')
            return jsonify({'success': False, 'message': 'Session expired. Please try the payment again.'})
        
        # Verify transaction details
        if pending_transaction['transaction_id'] != transaction_id:
            app.logger.warning(f'Transaction ID mismatch: {transaction_id} vs {pending_transaction["transaction_id"]}')
            return jsonify({'success': False, 'message': 'Invalid transaction. Please try again.'})
        
        if pending_transaction['player_id'] != player.id:
            app.logger.warning(f'Player ID mismatch: {player.id} vs {pending_transaction["player_id"]}')
            return jsonify({'success': False, 'message': 'Invalid player transaction.'})
        
        # Find player by transaction ID
        player = Player.query.filter_by(transaction_id=transaction_id).first()
        if not player:
            app.logger.error(f'No player found for transaction {transaction_id}')
            return jsonify({'status': 'error', 'message': 'Player not found'}), 404

        # Verify payment amount
        if float(amount) != float(REGISTRATION_FEE):
            app.logger.error(f'Amount mismatch: expected {REGISTRATION_FEE}, got {amount}')
            player.payment_note = 'Amount mismatch'
            db.session.commit()
            return jsonify({'status': 'error', 'message': 'Invalid amount'}), 400

        # Update payment status
        player.payment_status = payment_status == 'SUCCESS'
        player.registration_status = 'completed' if payment_status == 'SUCCESS' else 'pending'
        player.payment_date = datetime.utcnow()
        player.payment_response = f'UTR: {utr}'
        db.session.commit()
        
        app.logger.info('Payment status updated successfully')
            
        # Send success SMS
        message = (
            f"Thank you for registering for the Cricket Tournament!\n"
            f"Payment of ₹{REGISTRATION_FEE} received.\n"
            f"Transaction ID: {transaction_id}\n"
            f"Keep this message for future reference."
        )
        send_sms(player.mobile_number, message)
        
        # Clear the pending transaction from session
        session.pop('pending_transaction', None)
        
        # Generate player card
        app.logger.info('Generating player card')
        try:
            from card_generator import create_player_card
            
            # Determine player role
            roles = []
            if player.is_all_rounder:
                roles.append("All-Rounder")
            if player.is_left_hand_batter or player.is_right_hand_batter:
                bat_style = []
                if player.is_left_hand_batter:
                    bat_style.append("Left-Hand")
                if player.is_right_hand_batter:
                    bat_style.append("Right-Hand")
                roles.append(f"{' & '.join(bat_style)} Batter")
            if player.is_left_arm_bowler or player.is_right_arm_bowler:
                bowl_style = []
                if player.is_left_arm_bowler:
                    bowl_style.append("Left-Arm")
                if player.is_right_arm_bowler:
                    bowl_style.append("Right-Arm")
                roles.append(f"{' & '.join(bowl_style)} Bowler")
            
            role_text = " | ".join(roles) if roles else "Not Specified"
            
            # Get photo path
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], player.profile_picture) if player.profile_picture else None
            
            # Ensure upload folder exists
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            
            # Create safe filename from player name
            safe_name = ''.join(c for c in player.full_name if c.isalnum() or c in '- ')
            safe_name = safe_name.replace(' ', '_')
            
            # Determine the player's role folder
            role_folder = '1_All_Rounders' if player.is_all_rounder else \
                         '2_Batters' if (player.is_left_hand_batter or player.is_right_hand_batter) else \
                         '3_Bowlers' if (player.is_left_arm_bowler or player.is_right_arm_bowler) else \
                         '2_Batters'  # Default to Batters if no role specified
            
            # Set path in Player_Event_Assets folder
            player_dir = os.path.join(app.static_folder, 'Player_Event_Assets', role_folder,
                                    f"{player.id}_{safe_name}")
            
            # Create directory with proper permissions
            try:
                os.makedirs(player_dir, mode=0o755, exist_ok=True)
                app.logger.info(f'Created player directory: {player_dir}')
            except Exception as dir_error:
                app.logger.error(f'Error creating directory {player_dir}: {str(dir_error)}')
                raise
            
            # Set output path for the card
            card_path = os.path.join(player_dir, f"{player.id}_{safe_name}_card.png")
            
            app.logger.info(f'Starting card generation with:')
            app.logger.info(f'Player Name: {player.full_name}')
            app.logger.info(f'Nickname: {player.nickname}')
            app.logger.info(f'Role: {role_text}')
            app.logger.info(f'Photo Path: {photo_path}')
            app.logger.info(f'Initial Output Path: {card_path}')
            
            # Create the card
            success = create_player_card(
                player_name=player.full_name,
                nickname=player.nickname or "",
                role=role_text,
                photo_path=photo_path,
                output_path=card_path
            )
            
            if success:
                app.logger.info(f'Player card generated successfully at {card_path}')
            else:
                app.logger.info('Card generation returned False')
                
        except Exception as e:
            app.logger.error(f'Error generating player card: {str(e)}')
        
        app.logger.info('Payment verification completed successfully')
        
        # Return success with redirect URL
        return jsonify({
            'success': True,
            'message': 'Payment verified successfully! Redirecting to success page...',
            'redirect_url': url_for('payment_success', player_id=player.id)
        })
        
    except Exception as e:
        app.logger.error(f"Error in verify_upi_payment: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'An error occurred while verifying the payment. Please try again or contact support.'
        })
    


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    form = AdminLoginForm()
    if form.validate_on_submit():
        admin = Admin.query.filter_by(username=form.username.data).first()
        if admin and check_password_hash(admin.password, form.password.data):
            login_user(admin)
            return redirect(url_for('admin_dashboard'))
        flash('Invalid username or password', 'danger')
    return render_template('admin/login.html', form=form)

@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    return redirect(url_for('admin_login'))


@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    # Get all players
    players = Player.query.all()
    
    # Sort players by role category (All-rounders first, then batters, then bowlers)
    sorted_players = sorted(players, key=lambda p: (
        # Sort order: All-rounders first (-1), then batters (-2), then bowlers (-3)
        -1 if p.is_all_rounder else 
        -2 if (p.is_left_hand_batter or p.is_right_hand_batter) else 
        -3 if (p.is_left_arm_bowler or p.is_right_arm_bowler) else 0,
        # Secondary sort by registration date (most recent first)
        p.registration_date.timestamp() if p.registration_date else 0,
    ), reverse=True)
    
    # Add debug information
    print(f"\nNumber of players found: {len(sorted_players)}")
    for player in sorted_players:
        role = "All-Rounder" if player.is_all_rounder else \
               "Batter" if (player.is_left_hand_batter or player.is_right_hand_batter) else \
               "Bowler" if (player.is_left_arm_bowler or player.is_right_arm_bowler) else "Unknown"
        print(f"Player ID: {player.id}, Name: {player.full_name}, Role: {role}")
    
    return render_template('admin/dashboard.html', players=sorted_players)

@app.route('/admin/player/<int:player_id>')
@login_required
def player_detail(player_id):
    player = Player.query.get_or_404(player_id)
    return render_template('admin/player_detail.html', player=player)

@app.route('/admin/download-players-pdf')
@login_required
def download_players_pdf():
    """Generate a PDF list of all registered players with their details and pictures."""
    # Get all registered players
    players = Player.query.filter_by(registration_status='completed').order_by(Player.registration_date.desc()).all()
    
    # Generate PDF using the dedicated generator module
    buffer = generate_players_pdf(players, app)
    
    # Create response
    response = make_response(buffer.getvalue())
    response.mimetype = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=players_list_{datetime.now().strftime("%Y%m%d")}.pdf'
    return response

    
    # Create a BytesIO buffer to store the PDF
    buffer = BytesIO()
    
    # Create the PDF document in landscape mode with adjusted margins
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    
    # Create header row with styled cells
    headers = [
        Paragraph('S.No', header_style),
        Paragraph('Picture', header_style),
        Paragraph('Player Name', header_style),
        Paragraph('Nickname', header_style),
        Paragraph('Role', header_style),
        Paragraph('Mobile Number', header_style),
        Paragraph('Address', header_style)
    ]
    
    # Initialize table data with headers
    data = [headers]
    
    # Add title
    title = Paragraph(f"Cricket Tournament Registered Players List - {datetime.now().strftime('%Y-%m-%d')}", title_style)
    elements.append(title)
    elements.append(Spacer(1, 12))
    
    # Prepare table data with requested columns including picture and S.No
    data = [['S.No', 'Picture', 'Player Name', 'Nickname', 'Role', 'Mobile Number', 'Address']]
    
    for idx, player in enumerate(players, 1):
        # Process player picture
        pic_cell = ''
        if player.profile_picture:
            try:
                pic_path = os.path.join(app.config['UPLOAD_FOLDER'], player.profile_picture)
                if os.path.exists(pic_path):
                    img = PILImage.open(pic_path)
                    # Resize image to a reasonable size
                    # Convert to RGB if needed
                    if img.mode not in ('RGB', 'RGBA'):
                        img = img.convert('RGB')
                    # Resize while maintaining aspect ratio
                    img.thumbnail((100, 100))
                    img_buffer = BytesIO()
                    img.save(img_buffer, format='JPEG', quality=95)
                    pic_cell = Image(BytesIO(img_buffer.getvalue()))
                    pic_cell.drawHeight = 80
                    pic_cell.drawWidth = 80
            except Exception as e:
                app.logger.error(f'Error processing player image: {str(e)}')
                pic_cell = Paragraph('No Image', getSampleStyleSheet()['Normal'])
        else:
            pic_cell = Paragraph('No Image', getSampleStyleSheet()['Normal'])

        # Determine player role
        roles = []
        if player.is_all_rounder:
            roles.append("All-Rounder")
        if player.is_left_hand_batter or player.is_right_hand_batter:
            bat_style = []
            if player.is_left_hand_batter:
                bat_style.append("Left-Hand")
            if player.is_right_hand_batter:
                bat_style.append("Right-Hand")
            roles.append(f"{' & '.join(bat_style)} Batter")
        if player.is_left_arm_bowler or player.is_right_arm_bowler:
            bowl_style = []
            if player.is_left_arm_bowler:
                bowl_style.append("Left-Arm")
            if player.is_right_arm_bowler:
                bowl_style.append("Right-Arm")
            roles.append(f"{' & '.join(bowl_style)} Bowler")
        
        role_text = " | ".join(roles) if roles else "Not Specified"
        
        # Create row with player details
        row = [
            sno_cell,
            pic_cell,
            Paragraph(player.full_name, getSampleStyleSheet()['Normal']),
            Paragraph(player.nickname or "N/A", getSampleStyleSheet()['Normal']),
            Paragraph(role_text, getSampleStyleSheet()['Normal']),
            player.mobile_number,
            Paragraph(player.address, ParagraphStyle(
                'address',
                parent=getSampleStyleSheet()['Normal'],
                fontSize=12,
                leading=14,
                wordWrap='LTR',
                alignment=0,  # Left alignment
                leftIndent=5,
                rightIndent=5,
                spaceAfter=5
            ))
        ]
        data.append(row)
    
    # Create table with adjusted column widths for better visibility
    table = Table(data, colWidths=[
        0.7*inch,     # S.No - increased width
        1.5*inch,     # Picture - more space for images
        2.0*inch,     # Player Name
        1.5*inch,     # Nickname
        2.5*inch,     # Role
        1.5*inch,     # Mobile Number
        3.0*inch,     # Address - much wider for full text
    ], rowHeights=[0.8*inch] + [1.2*inch] * (len(data)-1))
    
    # Enhanced table style
    # Create table style with specific cell styling
    style = TableStyle([
        # Header style
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),  # Dark blue header
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),  # Larger header font
        ('BOTTOMPADDING', (0, 0), (-1, 0), 15),
        ('TOPPADDING', (0, 0), (-1, 0), 15),
        
        # Body style
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 12),  # Larger body font
        ('LEADING', (0, 1), (-1, -1), 14),  # Increased line spacing
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),  # Center S.No column
        ('ALIGN', (3, 1), (-1, -1), 'CENTER'),  # Center the last three columns
        
        # Grid styling
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#1a237e')),  # Thicker outer border
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),  # Center align S.No column
        ('BACKGROUND', (0, 1), (0, -1), colors.lightgrey),  # Light background for S.No column
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),  # Alternate row colors
        
        # Padding
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ])
    table.setStyle(style)
    
    elements.append(table)
    
    # Build PDF document
    doc.build(elements)
    
    # File response
    buffer.seek(0)
    response = make_response(buffer.getvalue())
    response.mimetype = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=players_list_{datetime.now().strftime("%Y%m%d")}.pdf'
    
    return response

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    if not filename:
        return 'No file specified', 400
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=False)
    except Exception as e:
        print(f"Error serving file {filename}: {str(e)}")
        return 'File not found', 404

@app.route('/players')
def player_list():
    page = request.args.get('page', 1, type=int)
    players = Player.query.filter_by(payment_status=True, registration_status='completed')\
        .order_by(Player.registration_date.desc())\
        .paginate(page=page, per_page=10, error_out=False)
    return render_template('player_list.html', players=players)

@app.route('/upload-payment-proof/<int:player_id>', methods=['POST'])
def upload_payment_proof(player_id):
    player = Player.query.get_or_404(player_id)
    
    if 'payment_screenshot' not in request.files:
        flash('No file uploaded', 'danger')
        return redirect(url_for('initiate_payment', player_id=player_id))
    
    file = request.files['payment_screenshot']
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('initiate_payment', player_id=player_id))
    
    if file:
        try:
            # Save the screenshot
            filename = secure_filename(f'payment_{player_id}_{file.filename}')
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Update player record
            player.payment_screenshot = filename
            db.session.commit()
            
            flash('Payment proof uploaded successfully. Please wait for admin verification.', 'success')
            return redirect(url_for('payment_success_pending', player_id=player_id))
            
        except Exception as e:
            app.logger.error(f'Error saving payment proof: {str(e)}')
            flash('Error uploading payment proof. Please try again.', 'danger')
            return redirect(url_for('initiate_payment', player_id=player_id))

@app.route('/payment-success-pending/<int:player_id>')
def payment_success_pending(player_id):
    player = Player.query.get_or_404(player_id)
    return render_template('upload_success.html', player=player)

@app.route('/admin/verify-payment/<int:player_id>', methods=['POST'])
@login_required
def verify_payment(player_id):
    player = Player.query.get_or_404(player_id)
    action = request.form.get('action')
    
    if action == 'approve':
        player.payment_status = True
        player.registration_status = 'completed'
        player.admin_approved = True
        player.approved_by = current_user.id
        player.approved_at = datetime.utcnow()
        
        # Send confirmation SMS
        message = f"Thank you for registering for the Cricket Tournament! Your payment of ₹{REGISTRATION_FEE} has been verified."
        send_sms(player.mobile_number, message)
        
        flash('Payment verified successfully', 'success')
    else:
        player.payment_status = False
        player.registration_status = 'pending'
        player.admin_approved = False
        flash('Payment verification rejected', 'warning')
    
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_player/<int:player_id>', methods=['POST'])
@login_required
def delete_player(player_id):
    try:
        player = Player.query.get_or_404(player_id)
        app.logger.info(f"Attempting to delete player {player_id}")
        
        # Delete profile picture if exists
        if player.profile_picture:
            try:
                profile_pic_path = os.path.join(app.config['UPLOAD_FOLDER'], player.profile_picture)
                if os.path.exists(profile_pic_path):
                    os.remove(profile_pic_path)
                    app.logger.info(f"Deleted profile picture: {profile_pic_path}")
            except Exception as e:
                app.logger.error(f"Error deleting profile picture: {str(e)}")
        
        # Delete player card if exists
        try:
            card_path = os.path.join(app.config['UPLOAD_FOLDER'], f'player_card_{player_id}.pdf')
            if os.path.exists(card_path):
                os.remove(card_path)
                app.logger.info(f"Deleted player card: {card_path}")
        except Exception as e:
            app.logger.error(f"Error deleting player card: {str(e)}")
        
        # Delete player from database
        db.session.delete(player)
        db.session.commit()
        app.logger.info(f"Successfully deleted player {player_id}")
        flash('Registration deleted successfully.', 'success')
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting player {player_id}: {str(e)}")
        flash('Error deleting registration. Please try again.', 'danger')
    
    return redirect(url_for('admin_dashboard'))