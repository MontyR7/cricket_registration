from app import app, db
from models import Player
from create_player_assets import generate_player_card
import os

def test_card_generation():
    with app.app_context():
        # Get the first player from the database
        player = Player.query.first()
        
        if not player:
            print("No players found in database!")
            return
            
        print(f"\nTesting card generation with player: {player.full_name}")
        
        # Template path
        template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                   'templates', 'player_card_template.html')
        
        # Output path
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                 'static', 'test')
        os.makedirs(output_dir, exist_ok=True)
        
        output_path = os.path.join(output_dir, f'test_card_{player.id}.png')
        
        # Generate test card
        generate_player_card(player, template_path, output_path)
        
        if os.path.exists(output_path):
            print(f"\nTest successful! Card generated at: {output_path}")
            print("You can open this file to verify the card generation is working correctly.")
        else:
            print("\nTest failed! Card was not generated.")

if __name__ == '__main__':
    test_card_generation()