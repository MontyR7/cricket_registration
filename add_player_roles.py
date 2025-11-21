from app import app, db
from models import Player

def add_player_role_columns():
    with app.app_context():
        # Add columns for player roles
        columns = [
            'is_all_rounder BOOLEAN DEFAULT FALSE',
            'is_left_arm_bowler BOOLEAN DEFAULT FALSE',
            'is_right_arm_bowler BOOLEAN DEFAULT FALSE',
            'is_left_hand_batter BOOLEAN DEFAULT FALSE',
            'is_right_hand_batter BOOLEAN DEFAULT FALSE'
        ]
        
        for column in columns:
            column_name = column.split()[0]
            try:
                # Check if column exists
                db.session.execute(f"SELECT {column_name} FROM player LIMIT 1")
                print(f"Column {column_name} already exists")
            except Exception as e:
                try:
                    # Add column if it doesn't exist
                    from sqlalchemy import text
                    db.session.execute(text(f"ALTER TABLE player ADD COLUMN {column}"))
                    print(f"Added column: {column_name}")
                except Exception as e:
                    print(f"Error adding column {column_name}: {str(e)}")
        
        db.session.commit()
        print("Database migration completed successfully!")

if __name__ == '__main__':
    add_player_role_columns()