from app import app, db
from models import Player

with app.app_context():
    players = Player.query.all()
    print(f"\nTotal number of players: {len(players)}\n")
    print("Player details:")
    print("-" * 80)
    for player in players:
        print(f"ID: {player.id}")
        print(f"Name: {player.full_name}")
        print(f"Mobile: {player.mobile_number}")
        print(f"Registration Status: {player.registration_status}")
        print(f"Payment Status: {player.payment_status}")
        print("-" * 80)