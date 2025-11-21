import os
from datetime import datetime
from flask import request, jsonify, flash, redirect, url_for, render_template
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from app import app, db
from models import Player, Admin
from flask_login import current_user, login_required
from routes import send_sms  # Import the send_sms function

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload-payment-proof/<int:player_id>', methods=['POST'])
def upload_payment_proof(player_id):
    try:
        player = Player.query.get_or_404(player_id)
        
        if 'payment_screenshot' not in request.files:
            flash('No file uploaded', 'danger')
            return redirect(request.referrer)
            
        file = request.files['payment_screenshot']
        if file.filename == '':
            flash('No file selected', 'danger')
            return redirect(request.referrer)
            
        if file and allowed_file(file.filename):
            # Create a unique filename
            filename = f"payment_{player_id}_{secure_filename(file.filename)}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Save the file
            file.save(filepath)
            
            # Update player record
            player.payment_screenshot = filename
            player.registration_status = 'uploaded'
            db.session.commit()
            
            # Send SMS to player
            message = (
                "Thank you for submitting your payment proof for the Cricket Tournament registration. "
                "You will receive a confirmation SMS once your registration is verified."
            )
            send_sms(player.mobile_number, message)
            
            return render_template('upload_success.html')
            
        flash('Invalid file type. Please upload an image file.', 'danger')
        return redirect(request.referrer)
        
    except Exception as e:
        app.logger.error(f"Error uploading payment proof: {str(e)}")
        flash('An error occurred while uploading the file.', 'danger')
        return redirect(request.referrer)

@app.route('/payment-pending/<int:player_id>')
def payment_pending(player_id):
    player = Player.query.get_or_404(player_id)
    return render_template('payment_pending.html', player=player)

@app.route('/admin/approve-player/<int:player_id>', methods=['POST'])
@login_required
def approve_player(player_id):
    try:
        data = request.get_json()
        passcode = data.get('passcode')
        
        # Verify admin passcode
        admin = Admin.query.get(current_user.id)
        if not admin or not check_password_hash(admin.password, passcode):
            return jsonify({
                'success': False,
                'message': 'Invalid admin passcode'
            }), 401
        
        player = Player.query.get_or_404(player_id)
        
        if not player.payment_screenshot:
            return jsonify({
                'success': False,
                'message': 'No payment proof uploaded'
            }), 400
            
        # Update player status
        player.admin_approved = True
        player.approved_by = current_user.id
        player.approved_at = datetime.utcnow()
        player.payment_status = True
        player.registration_status = 'approved'
        db.session.commit()
        
        # Send confirmation SMS
        message = (
            f"Congratulations! Your registration for the Cricket Tournament has been approved.\n"
            f"Your payment has been verified.\n"
            f"Keep this message for your reference."
        )
        send_sms(player.mobile_number, message)
        
        return jsonify({
            'success': True,
            'message': 'Player registration approved successfully'
        })
        
    except Exception as e:
        app.logger.error(f"Error approving player: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'An error occurred while approving the player'
        }), 500

@app.route('/admin/batch-approve', methods=['POST'])
@login_required
def batch_approve_players():
    try:
        data = request.get_json()
        player_ids = data.get('player_ids', [])
        passcode = data.get('passcode')
        
        # Verify admin passcode
        admin = Admin.query.get(current_user.id)
        if not admin or not check_password_hash(admin.password, passcode):
            return jsonify({
                'success': False,
                'message': 'Invalid admin passcode'
            }), 401
        
        # Get all players with screenshots pending approval
        players = Player.query.filter(
            Player.id.in_(player_ids),
            Player.payment_screenshot.isnot(None),
            Player.admin_approved.is_(False)
        ).all()
        
        if not players:
            return jsonify({
                'success': False,
                'message': 'No valid players to approve'
            }), 400
            
        # Update all players
        current_time = datetime.utcnow()
        for player in players:
            player.admin_approved = True
            player.approved_by = current_user.id
            player.approved_at = current_time
            player.payment_status = True
            player.registration_status = 'approved'
            
            # Send confirmation SMS
            message = (
                f"Congratulations! Your registration for the Cricket Tournament has been approved.\n"
                f"Your payment has been verified.\n"
                f"Keep this message for your reference."
            )
            send_sms(player.mobile_number, message)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully approved {len(players)} players'
        })
        
    except Exception as e:
        app.logger.error(f"Error in batch approval: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'An error occurred during batch approval'
        }), 500