#!/usr/bin/env python
"""
Script to update admin password in the database
"""
from app import app, db
from models import Admin
from werkzeug.security import generate_password_hash

def update_admin_password():
    with app.app_context():
        # Find the admin user
        admin = Admin.query.filter_by(username='admin').first()
        
        if admin:
            # Update password to mark$123
            admin.password = generate_password_hash('mark$123')
            db.session.commit()
            print("✅ Admin password updated successfully to 'mark$123'")
        else:
            print("❌ Admin user not found!")

if __name__ == '__main__':
    update_admin_password()
