# Railway Deployment - Quick Checklist

## 🚀 Deploy Your App in 5 Minutes!

### ✅ Prerequisites (Before Deployment)

- [ ] GitHub repository: https://github.com/MontyR7/cricket_registration
- [ ] Railway account: https://railway.app (free to create)
- [ ] Environment variables prepared (see below)

### 📋 Required Environment Variables

Gather these values before deploying:

```
FLASK_ENV = production
SECRET_KEY = [Generate: python -c "import secrets; print(secrets.token_hex(32))"]
DB_HOST = [Your database host - can be external MySQL]
DB_USER = root
DB_PASSWORD = [Your database password]
DB_NAME = cricket_tournament
STRIPE_SECRET_KEY = sk_live_[from Stripe dashboard]
STRIPE_PUBLISHABLE_KEY = pk_live_[from Stripe dashboard]
TWILIO_ACCOUNT_SID = AC[from Twilio dashboard]
TWILIO_AUTH_TOKEN = [from Twilio dashboard]
TWILIO_PHONE_NUMBER = +[Your phone number]
UPI_ID = your-upi@bank
```

### 🚀 Deployment Steps

**Step 1: Open Railway**
- [ ] Go to https://railway.app
- [ ] Sign in with GitHub (easiest)

**Step 2: Create Project**
- [ ] Click "New Project"
- [ ] Click "Deploy from GitHub repo"
- [ ] Select `cricket_registration`

**Step 3: Add Environment Variables**
- [ ] In Railway dashboard, go to Variables tab
- [ ] Add all values from the list above
- [ ] Click Save

**Step 4: Deploy**
- [ ] Railway automatically deploys
- [ ] Wait 2-5 minutes for deployment to complete
- [ ] Check Deployments tab for status

**Step 5: Get Your URL**
- [ ] Click on the deployment
- [ ] Copy your live URL (looks like: `https://cricket-registration-xxxxx.up.railway.app`)
- [ ] Test it by visiting the URL

### 🧪 Test Your Deployment

After deployment completes:

- [ ] Visit your live URL
- [ ] Test registration form
- [ ] Check admin login at `/admin/login`
- [ ] Verify payment page loads
- [ ] Check player card generation

### 📊 Monitor Your App

In Railway dashboard:
- [ ] Check "Logs" tab for any errors
- [ ] Monitor resource usage (free tier has limits)
- [ ] Set up alerts for crashes (optional)

### 🔄 Auto-Deploy on Code Changes

From now on, every time you push to GitHub:

```powershell
git add .
git commit -m "Your changes"
git push origin main
```

Railway automatically redeploys within 2-5 minutes! 🎉

### ⚠️ Important Notes

1. **Database**: Your app needs a MySQL database. Options:
   - Keep your current external MySQL (set DB_HOST to your server)
   - Use Railway's PostgreSQL (requires code changes)
   - Use a free MySQL provider (cleardb, etc.)

2. **Credentials**: All credentials in environment variables are encrypted by Railway

3. **Custom Domain**: You can add a custom domain later (optional)

### 💰 Cost

Railway's free tier includes:
- $5 monthly credit (usually enough for testing)
- Pay-as-you-go after that (~$10-20/month for production use)

### 🆘 Troubleshooting

**App won't start?**
1. Check "Logs" in Railway dashboard
2. Verify all environment variables are set
3. Check database connection

**502 Error?**
1. Still deploying (wait 5 minutes)
2. Check logs for errors
3. Verify `Procfile` is correct

**Need help?**
- Railway Docs: https://docs.railway.app
- Railway Support: https://railway.app/help

---

## 🎉 You're Ready!

Your Cricket Registration app will be live on the internet in **5 minutes or less!**

**Next Step**: Go to https://railway.app and start deploying! 🚀

---

## Summary

| Item | Status |
|------|--------|
| Code on GitHub | ✅ Done |
| Production Config | ✅ Done |
| Railway Guide | ✅ Done |
| Procfile | ✅ Done |
| Ready to Deploy | ✅ Yes |

**Your app is production-ready! Deploy it now!** 🚀
