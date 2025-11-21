from app import app, db
from models import Admin
from werkzeug.security import generate_password_hash

def create_admin():
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Check if admin already exists
        admin = Admin.query.filter_by(username='admin').first()
        if not admin:
            admin = Admin(
                username='admin',
                password=generate_password_hash('mark$123')  # Change this password
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin user created successfully!")
        else:
            print("Admin user already exists!")

if __name__ == '__main__':
    create_admin()