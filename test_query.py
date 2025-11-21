from app import app, db
from models import Player

app.app_context().push()

full_name = "ravidone"
mobile_number = "7598433777"

print(f"Testing query for: {full_name}, {mobile_number}\n")

# Test pending query
pending_player = Player.query.filter(
    Player.full_name.ilike(full_name),
    Player.mobile_number == mobile_number,
    Player.registration_status == 'pending',
    Player.payment_status == False
).first()
print(f"Pending Query Result: {pending_player}")

# Test completed query
completed_player = Player.query.filter(
    Player.full_name.ilike(full_name),
    Player.mobile_number == mobile_number,
    Player.registration_status == 'completed',
    Player.payment_status == True
).first()
print(f"Completed Query Result: {completed_player}")
if completed_player:
    print(f"  ID: {completed_player.id}")
    print(f"  Name: {completed_player.full_name}")
    print(f"  Mobile: {completed_player.mobile_number}")
    print(f"  Payment Status: {completed_player.payment_status}")
    print(f"  Registration Status: {completed_player.registration_status}")
