from app import app, db
from sqlalchemy import inspect

def check_table_structure():
    with app.app_context():
        inspector = inspect(db.engine)
        print("\nPlayer Table Columns:")
        for col in inspector.get_columns('player'):
            print(f"- {col['name']}: {col['type']} (Nullable: {col['nullable']})")
        
        print("\nForeign Keys:")
        for fk in inspector.get_foreign_keys('player'):
            print(f"- {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")

if __name__ == '__main__':
    check_table_structure()