from app import app, db
from models import Player
from datetime import datetime

app.app_context().push()

# Find the player
player = Player.query.filter_by(full_name='ravidone', mobile_number='7598433777').first()

if player:
    print(f"Updating player: {player.full_name}")
    # Mark as completed payment
    player.payment_status = True
    player.registration_status = 'completed'
    player.payment_date = datetime.utcnow()
    db.session.commit()
    print(f"✓ Updated successfully!")
    print(f"  Payment Status: {player.payment_status}")
    print(f"  Registration Status: {player.registration_status}")
    print(f"  Payment Date: {player.payment_date}")
else:
    print("Player not found")
