# Cricket Registration Application

A Flask-based web application for managing cricket event registrations, player profiles, payments, and asset generation.

## Quick Start

### Prerequisites
- Python 3.8+
- MySQL 5.7+
- Virtual Environment (venv or conda)

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/ravithakur7/cricket_registration.git
   cd cricket_registration
   ```

2. **Create and activate virtual environment**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # Linux/Mac
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Setup database**
   ```bash
   # Create database
   mysql -u root -p -e "CREATE DATABASE cricket_tournament CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
   
   # Run migrations
   flask db upgrade
   ```

6. **Run development server**
   ```bash
   python app.py
   ```
   Access at `http://localhost:5000`

## Project Structure

```
cricket_registration/
├── app.py                 # Main Flask application
├── routes.py              # API endpoints and routes
├── models.py              # Database models (SQLAlchemy)
├── forms.py               # WTForms form definitions
├── extensions.py          # Flask extensions initialization
├── config.py              # Configuration management
├── wsgi.py                # Production WSGI entry point
│
├── templates/             # Jinja2 HTML templates
│   ├── admin/             # Admin dashboard templates
│   ├── base.html          # Base template
│   ├── register.html      # Registration form
│   └── ...
│
├── static/                # Static assets
│   ├── css/               # Stylesheets
│   ├── js/                # JavaScript files
│   ├── images/            # Images
│   └── player_cards/      # Generated player card images
│
├── Player_Event_Assets/   # Generated player assets and summaries
│   ├── 1_All_Rounders/
│   ├── 2_Batters/
│   └── 3_Bowlers/
│
├── migrations/            # Alembic database migrations
├── uploads/               # User uploads (players, documents)
│
├── requirements.txt       # Python dependencies
├── .env.example           # Environment variables template
├── DEPLOYMENT.md          # Production deployment guide
└── README.md              # This file
```

## Configuration

### Environment Variables
See `.env.example` for all available configuration options:

- `FLASK_ENV`: Environment (development/production/testing)
- `SECRET_KEY`: Flask secret key for session encryption
- `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_NAME`: Database credentials
- `STRIPE_SECRET_KEY`: Stripe API key
- `TWILIO_*`: Twilio SMS service credentials
- `UPI_ID`: UPI payment ID

### Database Models
- **Player**: Cricket player information and registration details
- **Admin**: Administrator accounts and permissions
- **Payment**: Payment records and transaction history

## Features

### User Features
- Player registration with profile details
- Event registration and role selection
- Payment processing (Stripe, UPI)
- Player card generation and download
- Event summary and statistics

### Admin Features
- Dashboard with player management
- Payment approval and tracking
- Player asset generation
- Event management
- SMS notifications (via Twilio)

## Development

### Running Tests
```bash
python test_card_generator.py
python test_card_generation.py
python test_query.py
```

### Database Migrations
```bash
# Create migration
flask db migrate -m "Description of changes"

# Apply migration
flask db upgrade

# Downgrade
flask db downgrade
```

### Asset Generation
```bash
# Generate player cards
python card_generator.py

# Create default profiles
python create_default_profile.py

# Generate player assets
python create_player_assets.py
```

## Production Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for comprehensive deployment instructions.

Quick deployment with Gunicorn:
```bash
pip install gunicorn
gunicorn --env-file .env --workers 4 --bind 0.0.0.0:5000 wsgi:app
```

## API Endpoints

### Authentication
- `POST /admin/login` - Admin login
- `POST /admin/logout` - Admin logout

### Registration
- `GET /register` - Registration form
- `POST /register` - Submit registration

### Payments
- `GET /payment` - Payment options
- `POST /payment/stripe` - Stripe payment
- `POST /payment/upi` - UPI payment

### Admin
- `GET /admin/dashboard` - Admin dashboard
- `GET /admin/players` - Player management
- `POST /admin/approve-payment` - Approve payment

## Common Issues

### Database Connection Error
- Verify MySQL is running
- Check database credentials in `.env`
- Ensure database exists

### Static Files Not Loading
- Check `STATIC_FOLDER` path in config
- Verify file permissions
- Clear browser cache

### Redis Connection Failed
- Redis is optional; application works without it
- Set `USE_REDIS=false` in `.env` if not needed
- Or install and run Redis: `redis-server`

## Security Notes

⚠️ **IMPORTANT FOR PRODUCTION:**
1. Never commit `.env` file to version control
2. Use strong, unique `SECRET_KEY` in production
3. Enable HTTPS/SSL
4. Keep dependencies updated: `pip install --upgrade pip -r requirements.txt`
5. Use environment-specific configurations
6. Rotate credentials regularly
7. Enable database backups
8. Monitor application logs

## Contributing

1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## License

Proprietary - All rights reserved

## Support

For issues and questions, refer to:
- [DEPLOYMENT.md](DEPLOYMENT.md) for deployment issues
- Application logs in `logs/` directory
- Database logs for connection issues

## Changelog

### Version 1.0.0
- Initial release
- Player registration system
- Payment processing (Stripe, UPI)
- Admin dashboard
- Player asset generation
