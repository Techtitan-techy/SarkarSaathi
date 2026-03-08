# ⚡ Vercel Quick Start - 5 Minutes to Live Site

## 🚀 Deploy in 3 Steps

### Step 1: Go to Vercel

👉 https://vercel.com → Sign in with GitHub

### Step 2: Import Project

1. Click "Add New" → "Project"
2. Select `Techtitan-techy/SarkarSaathi`
3. Click "Import"

### Step 3: Configure & Deploy

**IMPORTANT**: Set these settings:

```
Framework Preset: Create React App
Root Directory: frontend          ← IMPORTANT!
Build Command: npm run build
Output Directory: build
Install Command: npm install
```

Click "Deploy" → Wait 2-3 minutes → Done! 🎉

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

### Build Fails?

**Check**: Root Directory is set to `frontend` in Vercel settings

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
