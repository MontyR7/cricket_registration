from flask import Flask, render_template, request, redirect, url_for, flash, session
from extensions import db
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf.csrf import CSRFProtect
from flask_sse import sse
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import redis
from datetime import datetime
from dotenv import load_dotenv
import stripe
from twilio.rest import Client

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')

# MySQL Database Configuration
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_NAME = os.getenv('DB_NAME', 'cricket_tournament')

# Redis Configuration for SSE (make it optional)
use_redis = os.getenv('USE_REDIS', 'false').lower() == 'true'

# Always set a Redis URL even if we're not using Redis
app.config["REDIS_URL"] = os.getenv("REDIS_URL", "redis://localhost:6379")
app.config['SSE_REDIS_URL'] = app.config["REDIS_URL"]

if use_redis:
    try:
        redis_client = redis.from_url(app.config["REDIS_URL"])
        redis_client.ping()  # Test connection
        print('Redis connected successfully')
    except Exception as e:
        print(f'Warning: Redis connection failed: {str(e)}')
        print('Falling back to in-memory storage for SSE')
        use_redis = False
else:
    print('Redis disabled, using in-memory storage for SSE')
    redis_client = None

# Register SSE blueprint
app.register_blueprint(sse, url_prefix='/stream')
app.config['SSE_REDIS_URL'] = app.config['REDIS_URL']  # Ensure SSE uses same Redis URL

# Configure MySQL Database URI
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'
app.config['SQLALCHEMY_POOL_SIZE'] = 10  # Connection pool size
app.config['SQLALCHEMY_MAX_OVERFLOW'] = 20  # Max number of connections to create beyond pool size
app.config['SQLALCHEMY_POOL_TIMEOUT'] = 30  # Timeout in seconds for getting a connection from pool

app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Set static folder path
app.static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')

# Setup required directories
from directory_setup import setup_directories
if not setup_directories(app):
    print("Error setting up directories. Please check logs.")
    exit(1)

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'admin_login'
csrf = CSRFProtect(app)

# Initialize Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

# Initialize Twilio
try:
    twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    twilio_phone_number = os.getenv('TWILIO_PHONE_NUMBER')
    
    if not all([twilio_account_sid, twilio_auth_token, twilio_phone_number]):
        print('WARNING: Twilio credentials not fully configured. SMS functionality will be disabled.')
        print('Missing credentials:')
        if not twilio_account_sid:
            print('- TWILIO_ACCOUNT_SID')
        if not twilio_auth_token:
            print('- TWILIO_AUTH_TOKEN')
        if not twilio_phone_number:
            print('- TWILIO_PHONE_NUMBER')
        twilio_client = None
    else:
        twilio_client = Client(twilio_account_sid, twilio_auth_token)
        print('Twilio configured successfully')
except Exception as e:
    print(f'Error initializing Twilio: {str(e)}')
    twilio_client = None

# Import models after db initialization
from models import Player, Admin

@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))

# Import routes after everything is initialized
from routes import *

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    # Only use debug mode when running directly
    if os.environ.get('FLASK_ENV') == 'development':
        app.run(debug=True)
    else:
        app.run(debug=False)