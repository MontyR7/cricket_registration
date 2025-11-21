"""
Production WSGI Entry Point for Gunicorn/Waitress
Use this to run the application in production
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Verify required environment variables
required_vars = ['SECRET_KEY', 'DB_PASSWORD', 'STRIPE_SECRET_KEY']
missing_vars = [var for var in required_vars if not os.getenv(var)]

if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Import and run the app
from app import app

if __name__ == '__main__':
    # This file is meant to be run with Gunicorn or Waitress, not directly
    # But this allows testing the WSGI interface
    app.run()
