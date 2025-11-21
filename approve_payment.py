from app import app, db
from models import Player
from datetime import datetime

app.app_context().push()

# Find the player
player = Player.query.filter_by(full_name='ravi', mobile_number='7598433620').first()

if player:
    print(f"Found player: {player.full_name} (ID: {player.id})")
    print(f"Current Status:")
    print(f"  Payment Status: {player.payment_status}")
    print(f"  Registration Status: {player.registration_status}")
    print()
    
    # Mark as completed payment
    player.payment_status = True
    player.registration_status = 'completed'
    player.payment_date = datetime.utcnow()
    player.admin_approved = True
    db.session.commit()
    
    print(f"✓ Updated to COMPLETED!")
    print(f"  Payment Status: {player.payment_status}")
    print(f"  Registration Status: {player.registration_status}")
    print(f"  Payment Date: {player.payment_date}")
    print(f"  Admin Approved: {player.admin_approved}")
else:
    print("Player not found")
