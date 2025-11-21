from app import app, db
from models import Player
from datetime import datetime

app.app_context().push()

# Find player ravi with mobile 7598433620
player = Player.query.filter_by(full_name='ravi', mobile_number='7598433620').first()

if player:
    print(f"Updating player: {player.full_name}")
    # Mark as completed payment
    player.payment_status = True
    player.registration_status = 'completed'
    player.payment_date = datetime.utcnow()
    db.session.commit()
    print(f"✓ Updated successfully!")
    print(f"  ID: {player.id}")
    print(f"  Name: {player.full_name}")
    print(f"  Mobile: {player.mobile_number}")
    print(f"  Payment Status: {player.payment_status}")
    print(f"  Registration Status: {player.registration_status}")
else:
    print("Player not found")
