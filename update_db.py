from app import app, db
from sqlalchemy import text
from models import Player, Admin

def column_exists(conn, table, column):
    result = conn.execute(text(f"""
        SELECT COUNT(*) 
        FROM information_schema.columns 
        WHERE table_name = '{table}' 
        AND column_name = '{column}';
    """))
    return result.scalar() > 0

def update_database():
    with app.app_context():
        # Create the new columns
        with db.engine.connect() as conn:
            # Check and add payment_screenshot
            if not column_exists(conn, 'player', 'payment_screenshot'):
                conn.execute(text('ALTER TABLE player ADD COLUMN payment_screenshot VARCHAR(255);'))
            
            # Check and add admin_approved
            if not column_exists(conn, 'player', 'admin_approved'):
                conn.execute(text('ALTER TABLE player ADD COLUMN admin_approved BOOLEAN DEFAULT FALSE;'))
            
            # Check and add approved_by
            if not column_exists(conn, 'player', 'approved_by'):
                conn.execute(text('ALTER TABLE player ADD COLUMN approved_by INTEGER;'))
            
            # Check and add approved_at
            if not column_exists(conn, 'player', 'approved_at'):
                conn.execute(text('ALTER TABLE player ADD COLUMN approved_at DATETIME;'))
            
            # Add foreign key in a separate statement to handle if it already exists
            try:
                conn.execute(text('''
                    ALTER TABLE player
                    ADD CONSTRAINT fk_player_approved_by
                    FOREIGN KEY (approved_by) REFERENCES admin(id);
                '''))
            except Exception as e:
                print(f"Note: Foreign key may already exist: {e}")
            
            conn.commit()
            
        print("Database updated successfully!")

if __name__ == '__main__':
    update_database()