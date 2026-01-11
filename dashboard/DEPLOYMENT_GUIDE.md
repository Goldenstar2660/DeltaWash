# 🚀 Deployment Guide: Handwash Dashboard

This guide will help you deploy your dashboard with:
- **Frontend** → Vercel (free) + your .tech domain
- **Backend** → Railway (free tier) with PostgreSQL database

---

## 📋 Prerequisites

- A GitHub account (to connect your code)
- Your .tech domain ready
- About 30 minutes of time

---

## Part 1: Deploy Backend to Railway (15 min)

Railway offers a free tier with $5/month credit - enough for a small app.

### Step 1: Create Railway Account

1. Go to [railway.app](https://railway.app)
2. Click **"Login"** → **"Login with GitHub"**
3. Authorize Railway to access your GitHub

### Step 2: Create a New Project

1. Click **"New Project"** on the dashboard
2. Select **"Deploy from GitHub repo"**
3. If this is your first time, click **"Configure GitHub App"** to give Railway access to your repos
4. Select your `handwash` repository

### Step 3: Set Up the Backend Service

1. After selecting the repo, Railway will detect your project
2. Click on the service card that appears
3. Go to **Settings** tab:
   - Set **Root Directory** to: `dashboard/backend`
   - Set **Start Command** to: `alembic upgrade head && uvicorn src.main:app --host 0.0.0.0 --port $PORT`

### Step 4: Add PostgreSQL Database

1. Click **"+ New"** in your project
2. Select **"Database"** → **"Add PostgreSQL"**
3. Railway will automatically create a PostgreSQL database

### Step 5: Configure Environment Variables

1. Click on your backend service
2. Go to **Variables** tab
3. Click **"+ New Variable"** and add these:

| Variable | Value |
|----------|-------|
| `DATABASE_URL` | Click **"Add Reference"** → Select your PostgreSQL → Choose `DATABASE_URL` |
| `JWT_SECRET` | Generate a random 32+ character string (use: `openssl rand -hex 32` in terminal) |
| `JWT_ALGORITHM` | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` |
| `CORS_ORIGINS` | `https://yourdomain.tech,https://www.yourdomain.tech` (replace with your actual domain) |

### Step 6: Deploy

1. Railway should automatically deploy when you add variables
2. Wait for the build to complete (2-3 minutes)
3. Once deployed, click **"Settings"** → **"Networking"**
4. Click **"Generate Domain"** to get your backend URL
5. **Copy this URL!** You'll need it for the frontend (e.g., `https://handwash-backend-production.up.railway.app`)

### Step 7: Seed Demo Data (Optional)

If you want demo data in your dashboard:
1. In Railway, click on your backend service
2. Go to **"Settings"** → **"Service"**
3. Temporarily change the start command to:
   ```
   alembic upgrade head && python -m src.scripts.seed_demo_data && uvicorn src.main:app --host 0.0.0.0 --port $PORT
   ```
4. Click **"Deploy"** to redeploy
5. After deployment succeeds, change the command back to the original (remove the seed script part)

---

## Part 2: Deploy Frontend to Vercel (10 min)

### Step 1: Create Vercel Account

1. Go to [vercel.com](https://vercel.com)
2. Click **"Sign Up"** → **"Continue with GitHub"**
3. Authorize Vercel to access your GitHub

### Step 2: Import Your Project

1. Click **"Add New..."** → **"Project"**
2. Find your `handwash` repository and click **"Import"**
3. Configure the project:
   - **Framework Preset**: Vite
   - **Root Directory**: Click **"Edit"** → Enter `dashboard/frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`

### Step 3: Add Environment Variables

1. Expand **"Environment Variables"**
2. Add this variable:

| Name | Value |
|------|-------|
| `VITE_API_BASE_URL` | Your Railway backend URL from Part 1 (e.g., `https://handwash-backend-production.up.railway.app`) |

### Step 4: Deploy

1. Click **"Deploy"**
2. Wait 1-2 minutes for the build
3. You'll get a URL like `your-project.vercel.app`

---

## Part 3: Connect Your .tech Domain (5 min)

### Step 1: Add Domain in Vercel

1. In Vercel, go to your project
2. Click **"Settings"** → **"Domains"**
3. Enter your domain (e.g., `yourdomain.tech`)
4. Click **"Add"**
5. Vercel will show you the DNS records you need to add

### Step 2: Configure DNS at Your Domain Registrar

Go to where you bought your .tech domain (Namecheap, GoDaddy, Google Domains, etc.) and update DNS:

**Option A: Use Vercel Nameservers (Recommended)**

1. In Vercel, you'll see nameservers like:
   - `ns1.vercel-dns.com`
   - `ns2.vercel-dns.com`
2. Go to your domain registrar's DNS settings
3. Change nameservers to Vercel's nameservers
4. Wait 10-30 minutes for DNS propagation

**Option B: Add DNS Records Manually**

Add these records at your domain registrar:

| Type | Name | Value |
|------|------|-------|
| A | @ | `76.76.21.21` |
| CNAME | www | `cname.vercel-dns.com` |

### Step 3: Verify & Enable HTTPS

1. Go back to Vercel **Settings** → **Domains**
2. Wait for verification (green checkmark)
3. Vercel automatically provides free SSL/HTTPS

---

## Part 4: Update Backend CORS (Important!)

After you have your domain set up, update the backend to accept requests from it:

1. Go to Railway → Your backend service → **Variables**
2. Update `CORS_ORIGINS` to include your new domain:
   ```
   https://yourdomain.tech,https://www.yourdomain.tech
   ```
3. Railway will automatically redeploy

---

## ✅ Final Checklist

- [ ] Backend deployed on Railway
- [ ] PostgreSQL database connected
- [ ] Frontend deployed on Vercel
- [ ] .tech domain connected
- [ ] HTTPS working (green lock icon)
- [ ] CORS configured correctly
- [ ] Demo data seeded (optional)

---

## 🧪 Test Your Deployment

1. Visit `https://yourdomain.tech`
2. The dashboard should load
3. Check browser console (F12) for any errors
4. Test navigation between pages

---

## 🔧 Troubleshooting

### "Failed to fetch" or CORS errors
- Check that `CORS_ORIGINS` in Railway includes your exact domain with `https://`
- Make sure `VITE_API_BASE_URL` in Vercel doesn't have a trailing slash

### Backend not starting
- Check Railway logs: Click on service → "Logs" tab
- Make sure all environment variables are set correctly

### Domain not working
- DNS can take up to 48 hours (usually 10-30 mins)
- Verify DNS with: `nslookup yourdomain.tech`

### Database connection errors
- Make sure you clicked "Add Reference" for DATABASE_URL, not typed it manually
- Check PostgreSQL service is running in Railway

---

## 💰 Cost Summary

| Service | Cost |
|---------|------|
| Vercel Frontend | **Free** (hobby tier) |
| Railway Backend | **Free** ($5 credit/month) |
| Railway PostgreSQL | **Free** (included in $5 credit) |
| .tech Domain | Whatever you paid |
| **Total Monthly** | **$0** (within free tier limits) |

---

## 🔄 Future Updates

When you push code to GitHub:
- **Frontend**: Vercel auto-deploys on every push
- **Backend**: Railway auto-deploys on every push

No manual action needed!

---

## 📞 Need Help?

- Vercel Docs: https://vercel.com/docs
- Railway Docs: https://docs.railway.app
- Check the logs in each platform for error details
