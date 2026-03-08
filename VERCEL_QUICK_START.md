# ⚡ Vercel Quick Start - 5 Minutes to Live Site

## 🚀 Deploy in 3 Steps

### Step 1: Go to Vercel

👉 https://vercel.com → Sign in with GitHub

### Step 2: Import Project

1. Click "Add New" → "Project"
2. Select `Techtitan-techy/SarkarSaathi`
3. Click "Import"

### Step 3: Configure & Deploy

**IMPORTANT**: Vercel will auto-detect the configuration from `vercel.json`.

Just click "Deploy" → Wait 2-3 minutes → Done! 🎉

**Note**: The `vercel.json` file in the root handles all configuration automatically.

---

## 🌐 Your Live URLs

After deployment:

- **Production**: `https://sarkari-saathi.vercel.app`
- **Preview**: `https://sarkari-saathi-git-[branch].vercel.app`

---

## 🔧 Optional: Add Environment Variables

If you have a backend API deployed:

1. Go to Project Settings → Environment Variables
2. Add:
   ```
   REACT_APP_API_ENDPOINT = https://your-api-gateway-url/dev
   REACT_APP_API_KEY = your-api-key
   ```
3. Redeploy

---

## ✅ Verification

Test your deployment:

- [ ] Site loads at Vercel URL
- [ ] Homepage displays correctly
- [ ] Voice input button visible
- [ ] Scheme list works
- [ ] No console errors
- [ ] Mobile responsive

---

## 🆘 Troubleshooting

### Build Fails with "cd: frontend: No such file or directory"?

**Solution**: The `vercel.json` file should handle this automatically. If it still fails:

1. Go to Vercel Dashboard → Project Settings → General
2. Scroll to "Build & Development Settings"
3. Click "Override" and set:
   - **Build Command**: `cd frontend && npm ci && npm run build`
   - **Output Directory**: `frontend/build`
   - **Install Command**: `cd frontend && npm ci`
4. Save and redeploy

### Build Fails with "Could not find index.js"?

**Solution**: This is already fixed. The `frontend/src/index.js` file exists in the repo.

### 404 Errors?

**Check**: Routes are configured (already in vercel.json)

### API Not Working?

**Check**: Environment variables are set in Vercel

---

## 📚 Full Guide

For detailed instructions, see: [docs/VERCEL_DEPLOYMENT.md](docs/VERCEL_DEPLOYMENT.md)

---

**Deployment Time**: 5 minutes  
**Cost**: FREE (100GB bandwidth/month)  
**SSL**: Automatic  
**CDN**: Global
