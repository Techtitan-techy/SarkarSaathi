# 🚀 Vercel Deployment Guide

> Deploy SarkariSaathi frontend to Vercel in minutes

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Deployment](#quick-deployment)
3. [Configuration](#configuration)
4. [Environment Variables](#environment-variables)
5. [Custom Domain](#custom-domain)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

- ✅ GitHub repository with your code
- ✅ Vercel account (free tier available)
- ✅ Frontend builds successfully (`npm run build`)

---

## Quick Deployment

### Method 1: Deploy via Vercel Dashboard (Easiest)

1. **Go to Vercel**
   - Visit https://vercel.com
   - Sign up or log in with GitHub

2. **Import Project**
   - Click "Add New" → "Project"
   - Select your GitHub repository: `Techtitan-techy/SarkarSaathi`
   - Click "Import"

3. **Configure Project**

   ```
   Framework Preset: Create React App
   Root Directory: ./
   Build Command: cd frontend && npm install && npm run build
   Output Directory: frontend/build
   Install Command: npm install
   ```

4. **Deploy**
   - Click "Deploy"
   - Wait 2-3 minutes
   - Your app will be live at: `https://your-project.vercel.app`

### Method 2: Deploy via Vercel CLI

```bash
# Install Vercel CLI
npm install -g vercel

# Login to Vercel
vercel login

# Deploy from project root
vercel

# Follow the prompts:
# - Set up and deploy? Yes
# - Which scope? Your account
# - Link to existing project? No
# - Project name? sarkari-saathi
# - Directory? ./
# - Override settings? Yes
#   - Build Command: cd frontend && npm install && npm run build
#   - Output Directory: frontend/build
#   - Development Command: cd frontend && npm start

# Deploy to production
vercel --prod
```

### Method 3: Deploy via GitHub Integration (Recommended)

1. **Connect GitHub**
   - Go to https://vercel.com/dashboard
   - Click "Add New" → "Project"
   - Authorize Vercel to access your GitHub

2. **Import Repository**
   - Select `Techtitan-techy/SarkarSaathi`
   - Vercel will auto-detect Create React App

3. **Configure Build**
   - Framework: Create React App
   - Root Directory: `./`
   - Build Command: `cd frontend && npm install && npm run build`
   - Output Directory: `frontend/build`

4. **Deploy**
   - Click "Deploy"
   - Vercel will build and deploy automatically

5. **Auto-Deploy on Push**
   - Every push to `main` branch will auto-deploy
   - Pull requests get preview deployments

---

## Configuration

### vercel.json (Already Created)

```json
{
  "version": 2,
  "name": "sarkari-saathi",
  "buildCommand": "cd frontend && npm install && npm run build",
  "outputDirectory": "frontend/build",
  "framework": "create-react-app",
  "routes": [
    {
      "src": "/(.*)",
      "dest": "/index.html"
    }
  ]
}
```

### Build Settings in Vercel Dashboard

If you need to override settings:

1. Go to Project Settings → General
2. Update:
   - **Framework Preset**: Create React App
   - **Root Directory**: `./`
   - **Build Command**: `cd frontend && npm install && npm run build`
   - **Output Directory**: `frontend/build`
   - **Install Command**: `npm install`
   - **Development Command**: `cd frontend && npm start`

---

## Environment Variables

### Add Environment Variables in Vercel

1. Go to Project Settings → Environment Variables
2. Add these variables:

```bash
# API Configuration (if you have backend deployed)
REACT_APP_API_ENDPOINT=https://your-api-gateway-url.execute-api.ap-south-1.amazonaws.com/dev
REACT_APP_API_KEY=your-api-gateway-key

# Feature Flags
REACT_APP_ENABLE_VOICE=true
REACT_APP_ENABLE_SMS=true
REACT_APP_ENABLE_MOCK_DATA=false

# Optional: Analytics
REACT_APP_GA_TRACKING_ID=UA-XXXXXXXXX-X
```

3. **Environment Scope**:
   - Production: Live site
   - Preview: Pull request previews
   - Development: Local development

### Create .env.local (for local testing)

```bash
# Create frontend/.env.local
cd frontend
cat > .env.local << EOF
REACT_APP_API_ENDPOINT=http://localhost:3000
REACT_APP_ENABLE_MOCK_DATA=true
EOF
```

---

## Custom Domain

### Add Custom Domain to Vercel

1. **Go to Project Settings → Domains**

2. **Add Domain**
   - Enter your domain: `sarkari-saathi.com`
   - Click "Add"

3. **Configure DNS**

   **Option A: Using Vercel Nameservers (Recommended)**

   ```
   Update your domain registrar with Vercel nameservers:
   - ns1.vercel-dns.com
   - ns2.vercel-dns.com
   ```

   **Option B: Using CNAME Record**

   ```
   Add CNAME record in your DNS:
   - Type: CNAME
   - Name: www (or @)
   - Value: cname.vercel-dns.com
   ```

4. **Wait for DNS Propagation** (5-30 minutes)

5. **SSL Certificate**
   - Vercel automatically provisions SSL
   - Your site will be available at `https://your-domain.com`

---

## Deployment Workflow

### Automatic Deployments

Once connected to GitHub:

1. **Production Deployment**
   - Push to `main` branch
   - Vercel automatically deploys to production
   - Live at: `https://your-project.vercel.app`

2. **Preview Deployments**
   - Create pull request
   - Vercel creates preview deployment
   - Test before merging

3. **Branch Deployments**
   - Push to any branch
   - Get unique preview URL
   - Share with team for testing

### Manual Deployments

```bash
# Deploy current directory
vercel

# Deploy to production
vercel --prod

# Deploy specific branch
git checkout feature-branch
vercel
```

---

## Vercel Dashboard Features

### Deployments Tab

- View all deployments
- See build logs
- Rollback to previous versions
- Download build artifacts

### Analytics Tab (Pro Plan)

- Page views
- Unique visitors
- Top pages
- Performance metrics

### Logs Tab

- Real-time function logs
- Error tracking
- Request logs

### Settings Tab

- Environment variables
- Build & development settings
- Domains
- Git integration
- Team members

---

## Troubleshooting

### Build Fails on Vercel

**Error**: `npm run build` fails

**Solution**:

```bash
# Test build locally first
cd frontend
npm install
npm run build

# If it works locally, check:
# 1. Node version in Vercel settings
# 2. Environment variables
# 3. Build logs in Vercel dashboard
```

### 404 on Routes

**Error**: React Router routes return 404

**Solution**: Already configured in `vercel.json`:

```json
{
  "routes": [
    {
      "src": "/(.*)",
      "dest": "/index.html"
    }
  ]
}
```

### API Calls Fail

**Error**: Cannot connect to backend

**Solution**:

1. Add `REACT_APP_API_ENDPOINT` environment variable in Vercel
2. Enable CORS in your API Gateway
3. Check API Gateway URL is correct

### Environment Variables Not Working

**Error**: `process.env.REACT_APP_*` is undefined

**Solution**:

1. Ensure variables start with `REACT_APP_`
2. Redeploy after adding variables
3. Check variable scope (Production/Preview/Development)

### Build Takes Too Long

**Error**: Build timeout

**Solution**:

1. Optimize dependencies
2. Remove unused packages
3. Use Vercel Pro for longer build times
4. Check build logs for bottlenecks

---

## Performance Optimization

### 1. Enable Vercel Analytics

```bash
# Install Vercel Analytics
cd frontend
npm install @vercel/analytics

# Add to your App.jsx
import { Analytics } from '@vercel/analytics/react';

function App() {
  return (
    <>
      <YourApp />
      <Analytics />
    </>
  );
}
```

### 2. Enable Image Optimization

```jsx
// Use Vercel Image component
import Image from "next/image"; // If using Next.js

// Or optimize images before deployment
// Use WebP format, compress images
```

### 3. Enable Caching

Vercel automatically caches:

- Static assets (JS, CSS, images)
- Build outputs
- API responses (with proper headers)

### 4. Use Edge Functions (Optional)

For API routes that need to be fast:

```javascript
// Create api/hello.js in frontend
export default function handler(req, res) {
  res.status(200).json({ message: "Hello from Edge!" });
}
```

---

## Vercel vs AWS S3 + CloudFront

### Vercel Advantages

- ✅ Automatic deployments from GitHub
- ✅ Preview deployments for PRs
- ✅ Built-in SSL certificates
- ✅ Global CDN
- ✅ Zero configuration
- ✅ Free tier (100GB bandwidth)

### AWS S3 + CloudFront Advantages

- ✅ Full control over infrastructure
- ✅ Integration with other AWS services
- ✅ Lower costs at scale
- ✅ Custom caching rules

### Recommendation

- **Use Vercel** for quick deployment and development
- **Use AWS S3 + CloudFront** for production at scale

---

## Cost Estimation

### Vercel Free Tier

- ✅ Unlimited deployments
- ✅ 100GB bandwidth/month
- ✅ Automatic SSL
- ✅ Preview deployments
- ✅ Analytics (basic)

### Vercel Pro ($20/month)

- ✅ 1TB bandwidth/month
- ✅ Advanced analytics
- ✅ Password protection
- ✅ Longer build times
- ✅ Team collaboration

### For Your Project

- **Expected Traffic**: 1000-5000 users/month
- **Bandwidth Usage**: ~10-20GB/month
- **Cost**: **FREE** (within free tier limits)

---

## Deployment Checklist

### Before Deployment

- [x] Frontend builds successfully locally
- [x] vercel.json created
- [x] .vercelignore created
- [x] Environment variables documented
- [ ] GitHub repository is public or Vercel has access
- [ ] Backend API is deployed (optional for demo)

### During Deployment

- [ ] Connect GitHub repository to Vercel
- [ ] Configure build settings
- [ ] Add environment variables
- [ ] Deploy to production

### After Deployment

- [ ] Test the live site
- [ ] Verify all routes work
- [ ] Check API connectivity (if backend deployed)
- [ ] Test on mobile devices
- [ ] Set up custom domain (optional)
- [ ] Enable analytics (optional)

---

## Step-by-Step: First Deployment

### Step 1: Sign Up for Vercel

1. Go to https://vercel.com
2. Click "Sign Up"
3. Choose "Continue with GitHub"
4. Authorize Vercel

### Step 2: Import Project

1. Click "Add New" → "Project"
2. Find `Techtitan-techy/SarkarSaathi` in the list
3. Click "Import"

### Step 3: Configure Build

Vercel should auto-detect Create React App. Verify:

```
Framework Preset: Create React App
Root Directory: ./
Build Command: cd frontend && npm install && npm run build
Output Directory: frontend/build
Install Command: npm install
```

### Step 4: Add Environment Variables (Optional)

If you have a backend API:

```
REACT_APP_API_ENDPOINT = https://your-api.execute-api.ap-south-1.amazonaws.com/dev
REACT_APP_API_KEY = your-api-key
```

### Step 5: Deploy

1. Click "Deploy"
2. Wait 2-3 minutes for build
3. Your site will be live!

### Step 6: Get Your URL

After deployment:

```
Production: https://sarkari-saathi.vercel.app
Preview: https://sarkari-saathi-git-branch.vercel.app
```

---

## Connecting Backend API

### Update Frontend to Use Vercel Deployment

1. **Add API endpoint to Vercel environment variables**:

   ```
   REACT_APP_API_ENDPOINT=https://your-api-gateway-url/dev
   ```

2. **Update CORS in API Gateway**:

   ```typescript
   // In your CDK stack
   defaultCorsPreflightOptions: {
     allowOrigins: [
       'https://sarkari-saathi.vercel.app',
       'https://*.vercel.app', // For preview deployments
       'http://localhost:3000' // For local development
     ],
     allowMethods: apigateway.Cors.ALL_METHODS,
     allowHeaders: ['Content-Type', 'Authorization', 'X-Api-Key'],
   }
   ```

3. **Redeploy API Gateway**:

   ```bash
   npx cdk deploy
   ```

4. **Test Connection**:
   - Visit your Vercel URL
   - Open browser console
   - Check for API calls
   - Verify no CORS errors

---

## Continuous Deployment

### Automatic Deployments

Once connected to GitHub:

1. **Push to main** → Deploys to production
2. **Create PR** → Creates preview deployment
3. **Push to branch** → Updates preview

### Deployment Notifications

Enable notifications in Vercel:

- Slack integration
- Email notifications
- Discord webhooks
- GitHub comments on PRs

---

## Advanced Configuration

### Custom Build Command

If you need custom build steps:

```json
{
  "buildCommand": "cd frontend && npm install && npm run build && npm run post-build",
  "outputDirectory": "frontend/build"
}
```

### Redirects and Rewrites

Add to `vercel.json`:

```json
{
  "redirects": [
    {
      "source": "/old-path",
      "destination": "/new-path",
      "permanent": true
    }
  ],
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://your-api-gateway-url/dev/:path*"
    }
  ]
}
```

### Headers Configuration

Add security headers:

```json
{
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        },
        {
          "key": "X-Frame-Options",
          "value": "DENY"
        },
        {
          "key": "X-XSS-Protection",
          "value": "1; mode=block"
        }
      ]
    }
  ]
}
```

---

## Monitoring

### Vercel Analytics

1. Go to Project → Analytics
2. View:
   - Page views
   - Unique visitors
   - Top pages
   - Performance metrics

### Real User Monitoring

```bash
# Install Vercel Speed Insights
cd frontend
npm install @vercel/speed-insights

# Add to App.jsx
import { SpeedInsights } from '@vercel/speed-insights/react';

function App() {
  return (
    <>
      <YourApp />
      <SpeedInsights />
    </>
  );
}
```

---

## Troubleshooting

### Build Fails

**Error**: Build command failed

**Solution**:

```bash
# Test locally first
cd frontend
npm install
npm run build

# Check Vercel build logs
# Common issues:
# 1. Missing dependencies
# 2. Environment variables
# 3. Build script errors
```

### Site Not Loading

**Error**: Blank page or 404

**Solution**:

1. Check output directory is correct: `frontend/build`
2. Verify routes configuration in `vercel.json`
3. Check browser console for errors
4. Review Vercel function logs

### API Calls Fail

**Error**: CORS or network errors

**Solution**:

1. Add Vercel domain to API Gateway CORS
2. Set `REACT_APP_API_ENDPOINT` in Vercel
3. Check API Gateway is deployed
4. Verify API key is correct

### Slow Build Times

**Solution**:

1. Remove unused dependencies
2. Use Vercel Pro for faster builds
3. Optimize build command
4. Cache node_modules

---

## Rollback Deployment

### Via Dashboard

1. Go to Deployments tab
2. Find previous successful deployment
3. Click "..." → "Promote to Production"

### Via CLI

```bash
# List deployments
vercel ls

# Rollback to specific deployment
vercel rollback [deployment-url]
```

---

## Cost Optimization

### Stay Within Free Tier

- ✅ 100GB bandwidth/month (enough for 5000-10000 users)
- ✅ Unlimited deployments
- ✅ Automatic SSL
- ✅ Global CDN

### Monitor Usage

1. Go to Account Settings → Usage
2. Check:
   - Bandwidth usage
   - Build minutes
   - Serverless function invocations

### Upgrade When Needed

Upgrade to Pro ($20/month) when:

- Bandwidth > 100GB/month
- Need advanced analytics
- Need password protection
- Need team collaboration

---

## Security Best Practices

### 1. Environment Variables

- ✅ Never commit API keys to Git
- ✅ Use Vercel environment variables
- ✅ Different keys for production/preview

### 2. CORS Configuration

- ✅ Whitelist only your Vercel domains
- ✅ Don't use `*` in production
- ✅ Include preview deployment domains

### 3. API Key Protection

```javascript
// Don't expose API keys in frontend
// Use backend proxy instead
const response = await fetch("/api/proxy", {
  method: "POST",
  body: JSON.stringify({ message: "Hello" }),
});
```

### 4. Content Security Policy

Add to `vercel.json`:

```json
{
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "Content-Security-Policy",
          "value": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';"
        }
      ]
    }
  ]
}
```

---

## Testing Deployment

### Test Checklist

After deployment, test:

- [ ] Homepage loads
- [ ] Voice input works (if enabled)
- [ ] Scheme list displays
- [ ] Chat interface works
- [ ] API calls succeed (if backend deployed)
- [ ] Mobile responsive
- [ ] All routes work
- [ ] No console errors

### Test Commands

```bash
# Test production URL
curl https://your-project.vercel.app

# Test API endpoint
curl https://your-project.vercel.app/api/health

# Test with different devices
# - Desktop browser
# - Mobile browser
# - Tablet
```

---

## Vercel CLI Commands

### Useful Commands

```bash
# Deploy to production
vercel --prod

# List deployments
vercel ls

# View logs
vercel logs [deployment-url]

# Remove deployment
vercel rm [deployment-name]

# Link local project to Vercel
vercel link

# Pull environment variables
vercel env pull

# Add environment variable
vercel env add REACT_APP_API_ENDPOINT
```

---

## Integration with GitHub

### Enable GitHub Integration

1. **Automatic Deployments**
   - Every push to main → Production deployment
   - Every PR → Preview deployment
   - Every commit → Build status check

2. **PR Comments**
   - Vercel bot comments on PRs with preview URL
   - See deployment status in PR checks

3. **Branch Protection**
   - Require Vercel deployment to pass before merge
   - Settings → Branches → Add rule

---

## Next Steps

### After First Deployment

1. ✅ Test the live site
2. ✅ Add custom domain (optional)
3. ✅ Set up environment variables
4. ✅ Enable analytics
5. ✅ Configure CORS for backend
6. ✅ Share preview URL with team
7. ✅ Set up deployment notifications

### For Production

1. ✅ Use custom domain
2. ✅ Enable Vercel Pro (if needed)
3. ✅ Set up monitoring
4. ✅ Configure security headers
5. ✅ Enable Web Analytics
6. ✅ Set up error tracking (Sentry)

---

## 📊 Deployment Summary

### What You Get with Vercel

- ✅ **Global CDN** - Fast loading worldwide
- ✅ **Automatic SSL** - HTTPS by default
- ✅ **Preview Deployments** - Test before production
- ✅ **Zero Configuration** - Works out of the box
- ✅ **GitHub Integration** - Auto-deploy on push
- ✅ **Free Tier** - Perfect for hackathons and demos

### Deployment Time

- **First Deployment**: 3-5 minutes
- **Subsequent Deployments**: 1-2 minutes
- **Preview Deployments**: 1-2 minutes

### Success Criteria

Your deployment is successful when:

- ✅ Build completes without errors
- ✅ Site is accessible at Vercel URL
- ✅ All routes work correctly
- ✅ API calls succeed (if backend deployed)
- ✅ No console errors
- ✅ Mobile responsive

---

## 🎉 You're Ready!

Your SarkariSaathi frontend is ready to deploy to Vercel. Follow the Quick Deployment section above to get started.

**Estimated Time**: 5-10 minutes for first deployment

**Live URL**: `https://sarkari-saathi.vercel.app` (after deployment)

---

## 📞 Support

### Vercel Support

- Documentation: https://vercel.com/docs
- Community: https://github.com/vercel/vercel/discussions
- Support: https://vercel.com/support

### Project Issues

- Check Vercel build logs
- Review browser console
- Test API connectivity
- Verify environment variables

---

**Guide Version**: 1.0  
**Last Updated**: March 4, 2026  
**Status**: Ready for deployment
