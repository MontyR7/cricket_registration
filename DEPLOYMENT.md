# Production Deployment Guide

## Overview
This guide provides instructions for deploying the Cricket Registration application to a production environment.

## Pre-Deployment Checklist

### 1. Environment Setup
- [ ] Clone/pull the repository
- [ ] Create `.env` file from `.env.example`
- [ ] Set all required environment variables (see below)
- [ ] Ensure `.env` is NOT committed to Git

### 2. Generate Secure Credentials
```bash
# Generate a strong SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"
```

### 3. Required Environment Variables

```env
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=<generate-a-strong-key>
DEBUG=False

# Database Configuration
DB_USER=root
DB_PASSWORD=<secure-password>
DB_HOST=<database-host>
DB_NAME=cricket_tournament

# Stripe Payment (get from Stripe dashboard)
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...

# Twilio SMS (get from Twilio dashboard)
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=<token>
TWILIO_PHONE_NUMBER=+1234567890

# UPI Payment
UPI_ID=your-upi-id@bank

# Redis (optional, for SSE)
USE_REDIS=false
REDIS_URL=redis://localhost:6379

# Admin Credentials (change from defaults)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=<secure-password>
```

## Installation Steps

### 1. System Requirements
- Python 3.8+
- MySQL/MariaDB 5.7+
- Linux/Unix server (Ubuntu 20.04+ recommended)

### 2. Install Dependencies
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt

# For production, also install Gunicorn or Waitress
pip install gunicorn  # Linux/Mac
pip install waitress  # Windows
```

### 3. Database Setup
```bash
# Create database
mysql -u root -p -e "CREATE DATABASE cricket_tournament CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# Run migrations
flask db upgrade
```

### 4. Directory Permissions
```bash
# Ensure directories are writable
chmod 755 uploads/
chmod 755 Player_Event_Assets/
chmod 755 static/
```

## Deployment Methods

### Option 1: Gunicorn (Recommended for Linux)
```bash
# Install Gunicorn
pip install gunicorn

# Run application
gunicorn --workers 4 --worker-class sync --bind 0.0.0.0:5000 app:app

# With environment file
gunicorn --env-file .env --workers 4 --worker-class sync --bind 0.0.0.0:5000 app:app
```

### Option 2: Waitress (Windows/Cross-platform)
```bash
# Install Waitress
pip install waitress

# Create serve.py
echo "from waitress import serve
from app import app
serve(app, host='0.0.0.0', port=5000)" > serve.py

# Run
python serve.py
```

### Option 3: Nginx + Gunicorn (Recommended for production)
```nginx
# /etc/nginx/sites-available/cricket-app
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /path/to/app/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

Enable the site:
```bash
ln -s /etc/nginx/sites-available/cricket-app /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

## Security Best Practices

### 1. HTTPS/SSL
```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Get free SSL certificate
sudo certbot certonly --nginx -d your-domain.com

# Auto-renewal
sudo systemctl enable certbot.timer
```

### 2. Firewall
```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 3. Database Security
- Use strong passwords
- Restrict database access to localhost only
- Regular backups
- Enable binary logging for recovery

### 4. Environment Variables
- Never commit `.env` to version control
- Use `.env.example` for documentation
- Rotate credentials regularly
- Store passwords in secure vaults

## Monitoring & Logging

### Application Logs
```bash
# Tail logs
tail -f /var/log/cricket-app/app.log

# Set up log rotation
sudo apt-get install logrotate
```

### Health Check
```bash
# Add to crontab
*/5 * * * * curl -f http://localhost:5000/health || notify-admin
```

## Backup & Recovery

### Database Backup
```bash
# Daily backup
mysqldump -u root -p cricket_tournament > backup-$(date +%Y%m%d).sql

# Restore
mysql -u root -p cricket_tournament < backup-20250121.sql
```

### Upload Folders
```bash
# Backup uploads
tar -czf uploads-backup-$(date +%Y%m%d).tar.gz uploads/
```

## Troubleshooting

### 500 Error
1. Check application logs
2. Verify environment variables are set
3. Check database connection
4. Review Flask error logs

### Database Connection Issues
```bash
# Test MySQL connection
mysql -h <DB_HOST> -u <DB_USER> -p <DB_NAME>
```

### Static Files Not Loading
1. Check `STATIC_FOLDER` path
2. Verify file permissions
3. Clear browser cache

## Update & Maintenance

### Deploying Updates
```bash
# Pull latest code
git pull origin main

# Install any new dependencies
pip install -r requirements.txt

# Run migrations
flask db upgrade

# Restart application
systemctl restart gunicorn  # or your app service
```

### Security Updates
- Regularly update Python packages: `pip install --upgrade pip -r requirements.txt`
- Monitor dependency vulnerabilities: `pip-audit`
- Keep OS packages updated: `apt update && apt upgrade`

## Support
For issues, check:
- Application logs in `logs/` directory
- Database error logs
- Nginx/Gunicorn error logs
- Browser console for frontend errors
