# Railway Deployment Guide

Railway is the easiest way to deploy your Cricket Registration app. It's simple, affordable, and automatically deploys when you push to GitHub.

## Step-by-Step Deployment

### Step 1: Create Railway Account
1. Go to https://railway.app
2. Click "Start Free" or "Login"
3. Sign up with GitHub (easiest option)
4. Authorize Railway to access your GitHub

### Step 2: Create New Project
1. Click "New Project" button
2. Select "Deploy from GitHub repo"
3. If prompted, authorize Railway to access your repositories

### Step 3: Select Your Repository
1. Look for `cricket_registration` in the list
2. Click on it to select
3. Railway will ask to install the Railway GitHub App
4. Click "Install" and authorize

### Step 4: Configure Environment Variables
Railway will detect it's a Python/Flask app. Now add your environment variables:

1. Click on the project to open the dashboard
2. Click "Variables" tab
3. Add these variables:

```
FLASK_ENV=production
SECRET_KEY=<generate-random-hex-32-chars>
DB_USER=root
DB_PASSWORD=<your-secure-password>
DB_HOST=<database-host>
DB_NAME=cricket_tournament
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
TWILIO_ACCOUNT_SID=<your-twilio-sid>
TWILIO_AUTH_TOKEN=<your-twilio-token>
TWILIO_PHONE_NUMBER=+1234567890
UPI_ID=your-upi-id@bank
```

### Step 5: Configure PostgreSQL Database (Free)
Railway includes a free PostgreSQL database. However, your app uses MySQL.

**Option A: Use Railway's PostgreSQL** (Easiest)
1. In Railway dashboard, click "Add Service"
2. Select "PostgreSQL"
3. Update your `.env` to use PostgreSQL connection string

**Option B: Use External MySQL Database**
If you have an external MySQL database:
1. Set `DB_HOST` to your external database host
2. Set `DB_USER` and `DB_PASSWORD`
3. Ensure your database is accessible from Railway

### Step 6: Generate SECRET_KEY
In PowerShell on your computer, run:
```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```
Copy the output and paste it as `SECRET_KEY` in Railway

### Step 7: Deploy
1. Click "Deploy" button
2. Railway will:
   - Clone your repository
   - Install Python dependencies from `requirements.txt`
   - Run migrations
   - Start the app

3. **Your app will be live in 2-5 minutes!**

### Step 8: Get Your App URL
After deployment completes:
1. Click on your project
2. Look for "Deployments" tab
3. Copy your app URL (something like: `https://cricket-registration-production.up.railway.app`)

---

## Important Configuration for Railway

### Procfile (Optional but Recommended)
Create a file named `Procfile` in your project root:

```
web: gunicorn wsgi:app
```

This tells Railway exactly how to run your app.

### Add to Your Project
```powershell
cd C:\Users\Ravi\Desktop\cricket_registration
echo 'web: gunicorn wsgi:app' > Procfile
git add Procfile
git commit -m "Add Procfile for Railway deployment"
git push origin main
```

---

## Database Setup on Railway

### Option 1: PostgreSQL (Recommended)
1. Your app needs a small code change for PostgreSQL
2. Update connection string in `config.py`

### Option 2: External MySQL
Keep using your current MySQL setup:
- Set proper DB_HOST (must be accessible from internet)
- Enable remote connections on your database
- Add Railway IP to your database firewall (if needed)

---

## Environment Variables Checklist

Before deploying, prepare all these values:

```
✓ FLASK_ENV=production
✓ SECRET_KEY=<generate-new>
✓ DB_HOST=<your-database-host>
✓ DB_USER=<database-user>
✓ DB_PASSWORD=<database-password>
✓ DB_NAME=cricket_tournament
✓ STRIPE_SECRET_KEY=sk_live_...
✓ STRIPE_PUBLISHABLE_KEY=pk_live_...
✓ TWILIO_ACCOUNT_SID=AC...
✓ TWILIO_AUTH_TOKEN=<token>
✓ TWILIO_PHONE_NUMBER=+...
✓ UPI_ID=your-upi@bank
```

---

## Testing Your Deployment

After Railway deploys:

1. Visit your app URL
2. Test the registration form
3. Check admin dashboard
4. Verify payment functionality

If you see errors:
1. Click "Logs" in Railway dashboard
2. Check error messages
3. Update environment variables if needed

---

## Updating Your App

Railway automatically deploys on every GitHub push!

To update your app after fixing bugs:

```powershell
cd C:\Users\Ravi\Desktop\cricket_registration

# Make changes to your code
# ...

# Commit and push
git add .
git commit -m "Your commit message"
git push origin main

# Railway automatically redeploys within 2-5 minutes!
```

---

## Railway Pricing

- **Free tier**: $5 credit/month
  - Good for testing and light usage
  
- **Pay-as-you-go**: After free credit
  - Compute: $0.25/hour per unit (1 GB RAM)
  - Database: ~$5-10/month
  - **Total**: $10-20/month for most apps

---

## Troubleshooting

### App won't start
- Check logs in Railway dashboard
- Verify all environment variables are set
- Check database connection string

### 502 Bad Gateway
- Railway is still deploying (wait 5 minutes)
- Check application logs
- Verify WSGI entry point (should be `wsgi:app`)

### Database connection failed
- Verify DB_HOST is accessible from internet
- Check firewall rules
- Verify credentials in environment variables

### Static files not loading
- Check `STATIC_FOLDER` in config
- Verify files are committed to Git

---

## Getting Help

Railway support: https://railway.app/help
Check logs: Dashboard → Deployments → Logs tab

---

## Next Steps

1. ✅ Create Railway account
2. ✅ Deploy from GitHub
3. ✅ Add environment variables
4. ✅ Test your app
5. ✅ Share your live URL with users!

**Your app will be live on the internet in minutes!** 🚀
