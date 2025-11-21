from app import app, db
from models import Player

app.app_context().push()
players = Player.query.all()
print(f"Total players in database: {len(players)}\n")

for player in players:
    print(f"ID: {player.id}")
    print(f"  Name: {player.full_name}")
    print(f"  Mobile: {player.mobile_number}")
    print(f"  Payment Status: {player.payment_status}")
    print(f"  Registration Status: {player.registration_status}")
    print(f"  Payment Date: {player.payment_date}")
    print(f"  Transaction ID: {player.transaction_id}")
    print()
