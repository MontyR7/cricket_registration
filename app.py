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
import logging

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Load configuration based on environment
from config import get_config
app.config.from_object(get_config())

# Set static folder path
app.static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')

# Redis Configuration for SSE (make it optional)
use_redis = app.config.get('USE_REDIS', False)

# Initialize Redis if enabled
redis_client = None
if use_redis:
    try:
        redis_client = redis.from_url(app.config.get("REDIS_URL", "redis://localhost:6379"))
        redis_client.ping()  # Test connection
        logger.info('Redis connected successfully')
    except Exception as e:
        logger.warning(f'Redis connection failed: {str(e)}. Falling back to in-memory storage for SSE')
        use_redis = False
else:
    logger.info('Redis disabled, using in-memory storage for SSE')

# Register SSE blueprint
app.register_blueprint(sse, url_prefix='/stream')

# Setup required directories
from directory_setup import setup_directories
if not setup_directories(app):
    logger.error("Error setting up directories. Please check logs.")
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
        logger.warning('Twilio credentials not fully configured. SMS functionality will be disabled.')
        twilio_client = None
    else:
        twilio_client = Client(twilio_account_sid, twilio_auth_token)
        logger.info('Twilio configured successfully')
except Exception as e:
    logger.error(f'Error initializing Twilio: {str(e)}')
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
    
    # Get environment
    env = os.getenv('FLASK_ENV', 'development').lower()
    
    if env == 'production':
        logger.info('Running in PRODUCTION mode')
        logger.warning('Debug mode is OFF. Never run production with debug=True!')
        # In production, use a production WSGI server (Gunicorn, Waitress, etc.)
        # Do NOT use the development server
        app.run(debug=False, host='0.0.0.0', port=5000)
    else:
        logger.info('Running in DEVELOPMENT mode')
        app.run(debug=True, host='127.0.0.1', port=5000)