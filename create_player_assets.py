from app import app
from models import Player
import os
import json
import shutil
from datetime import datetime
from card_generator import create_player_card

def generate_player_card(player, template_path, output_path):
    print(f"\nGenerating card for player: {player.full_name}")
    print(f"Output path: {output_path}")

    try:
        # Determine player role
        role = "All-Rounder" if player.is_all_rounder else \
               "Batter" if (player.is_left_hand_batter or player.is_right_hand_batter) else \
               "Bowler" if (player.is_left_arm_bowler or player.is_right_arm_bowler) else "Batter"
        
        # Get the absolute path for the player's photo
        if not player.profile_picture:
            print("Warning: No profile picture found for player")
            photo_path = os.path.join(os.path.dirname(__file__), 'static', 'images', 'default-profile.png')
        else:
            photo_path = os.path.abspath(os.path.join(app.config['UPLOAD_FOLDER'], player.profile_picture))
        
        print(f"Photo path: {photo_path}")
        
        if not os.path.exists(photo_path):
            print(f"Warning: Photo file not found at {photo_path}")
            photo_path = os.path.join(os.path.dirname(__file__), 'static', 'images', 'default-profile.png')
        
        # Create the card using the new card generator
        success = create_player_card(
            player_name=player.full_name,
            nickname=player.nickname,
            role=role,
            photo_path=photo_path,
            output_path=output_path
        )
        
        if success:
            print(f"Successfully generated card at: {output_path}")
        else:
            print(f"Error: Failed to generate card at {output_path}")
            
    except Exception as e:
        print(f"Error generating card for {player.full_name}:")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        import traceback
        print("Full traceback:")
        print(traceback.format_exc())

def create_player_assets():
    # Base directory for player assets
    base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'Player_Event_Assets')
    
    # Template path
    template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                'templates', 'player_card_template.html')
    
    # Ensure required directories exist
    required_dirs = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static'),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'images'),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads'),
        base_dir
    ]
    
    print("\nChecking and creating required directories:")
    for directory in required_dirs:
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
                print(f"Created directory: {directory}")
            except Exception as e:
                print(f"Error creating directory {directory}: {str(e)}")
        else:
            print(f"Directory exists: {directory}")
    
    # Create base directory and role-based directories
    role_dirs = {
        'All_Rounders': os.path.join(base_dir, '1_All_Rounders'),
        'Batters': os.path.join(base_dir, '2_Batters'),
        'Bowlers': os.path.join(base_dir, '3_Bowlers')
    }
    
    # Create all directories
    for dir_path in role_dirs.values():
        os.makedirs(dir_path, exist_ok=True)
    
    # Create base directory if it doesn't exist
    os.makedirs(base_dir, exist_ok=True)
    
    with app.app_context():
        # Get all players who have registered (regardless of payment status for testing)
        print("\nFetching players from database...")
        players = Player.query.all()
        print(f"Found {len(players)} players in database")
        
        # Track players count in each category
        role_counts = {
            'All_Rounders': 0,
            'Batters': 0,
            'Bowlers': 0
        }
        
        for player in players:
            # Determine player's role directory
            player_role_dir = None
            if player.is_all_rounder:
                player_role_dir = role_dirs['All_Rounders']
                role_counts['All_Rounders'] += 1
            elif player.is_left_hand_batter or player.is_right_hand_batter:
                player_role_dir = role_dirs['Batters']
                role_counts['Batters'] += 1
            elif player.is_left_arm_bowler or player.is_right_arm_bowler:
                player_role_dir = role_dirs['Bowlers']
                role_counts['Bowlers'] += 1
            else:
                # If no role specified, default to Batters
                player_role_dir = role_dirs['Batters']
                role_counts['Batters'] += 1
            
            # Create player directory within role directory
            player_dir = os.path.join(player_role_dir, f"{player.id}_{player.full_name}")
            os.makedirs(player_dir, exist_ok=True)
            
            # Copy profile picture if exists
            if player.profile_picture:
                src_path = os.path.join(app.config['UPLOAD_FOLDER'], player.profile_picture)
                if os.path.exists(src_path):
                    dst_path = os.path.join(player_dir, player.profile_picture)
                    shutil.copy2(src_path, dst_path)
            
            # Create player details JSON
            player_data = {
                'id': player.id,
                'full_name': player.full_name,
                'nickname': player.nickname,
                'address': player.address,
                'mobile_number': player.mobile_number,
                'registration_date': player.registration_date.strftime('%Y-%m-%d %H:%M:%S'),
                'profile_picture': player.profile_picture,
                'roles': {
                    'all_rounder': player.is_all_rounder,
                    'left_arm_bowler': player.is_left_arm_bowler,
                    'right_arm_bowler': player.is_right_arm_bowler,
                    'left_hand_batter': player.is_left_hand_batter,
                    'right_hand_batter': player.is_right_hand_batter
                }
            }
            
            # Save JSON file
            json_path = os.path.join(player_dir, 'player_details.json')
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(player_data, f, indent=4, ensure_ascii=False)
            
            # Generate player card
            card_path = os.path.join(player_dir, f"{player.id}_{player.full_name}_card.png")
            generate_player_card(player, template_path, card_path)
            
            # Create readable text file
            txt_path = os.path.join(player_dir, 'player_details.txt')
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(f"Player Details\n{'='*50}\n\n")
                f.write(f"ID: {player.id}\n")
                f.write(f"Full Name: {player.full_name}\n")
                f.write(f"Nickname: {player.nickname or 'N/A'}\n")
                f.write(f"Mobile: {player.mobile_number}\n")
                f.write(f"Address: {player.address}\n")
                f.write(f"Registration Date: {player.registration_date.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write("Player Roles:\n")
                f.write(f"- All-rounder: {'Yes' if player.is_all_rounder else 'No'}\n")
                f.write(f"- Left-arm Bowler: {'Yes' if player.is_left_arm_bowler else 'No'}\n")
                f.write(f"- Right-arm Bowler: {'Yes' if player.is_right_arm_bowler else 'No'}\n")
                f.write(f"- Left-hand Batter: {'Yes' if player.is_left_hand_batter else 'No'}\n")
                f.write(f"- Right-hand Batter: {'Yes' if player.is_right_hand_batter else 'No'}\n")
        
        # Create summary file
        summary_path = os.path.join(base_dir, 'player_summary.txt')
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(f"Player Distribution Summary\n{'='*50}\n\n")
            f.write(f"All-Rounders: {role_counts['All_Rounders']} players\n")
            f.write(f"Batters: {role_counts['Batters']} players\n")
            f.write(f"Bowlers: {role_counts['Bowlers']} players\n")
            f.write(f"\nTotal Players: {sum(role_counts.values())}\n")
            f.write(f"\nGenerated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        print(f"\nPlayer_Event_Assets Directory Structure Created Successfully!")
        print(f"{'='*50}")
        print(f"Player Distribution:")
        print(f"All-Rounders: {role_counts['All_Rounders']} players")
        print(f"Batters: {role_counts['Batters']} players")
        print(f"Bowlers: {role_counts['Bowlers']} players")
        print(f"Total: {sum(role_counts.values())} players")

if __name__ == '__main__':
    create_player_assets()