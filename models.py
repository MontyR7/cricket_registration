from extensions import db
from flask_login import UserMixin
from datetime import datetime

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    nickname = db.Column(db.String(50))
    address = db.Column(db.Text, nullable=False)
    mobile_number = db.Column(db.String(15), nullable=False, unique=True)
    profile_picture = db.Column(db.String(255))
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    payment_status = db.Column(db.Boolean, default=False)
    registration_status = db.Column(db.String(20), default='pending')  # pending, uploaded, approved, rejected
    payment_date = db.Column(db.DateTime)
    transaction_id = db.Column(db.String(100))
    payment_screenshot = db.Column(db.String(255))  # Path to payment screenshot
    payment_response = db.Column(db.Text)
    payment_type = db.Column(db.String(20))
    payment_note = db.Column(db.Text)
    admin_approved = db.Column(db.Boolean, default=False)
    approved_by = db.Column(db.Integer, db.ForeignKey('admin.id'))
    approved_at = db.Column(db.DateTime)
    # Player roles
    is_all_rounder = db.Column(db.Boolean, default=False)
    is_left_arm_bowler = db.Column(db.Boolean, default=False)
    is_right_arm_bowler = db.Column(db.Boolean, default=False)
    is_left_hand_batter = db.Column(db.Boolean, default=False)
    is_right_hand_batter = db.Column(db.Boolean, default=False)  # pending, completed, cancelled

class Admin(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)