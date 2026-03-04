# SarkariSaathi Frontend Deployment Guide

Complete guide for deploying the SarkariSaathi frontend to production.

## 📋 Pre-Deployment Checklist

- [ ] Backend infrastructure deployed via AWS CDK
- [ ] API Gateway URL obtained from CDK output
- [ ] API Key generated (if using API key authentication)
- [ ] CloudFront distribution created (optional but recommended)
- [ ] Domain name configured (optional)
- [ ] SSL certificate provisioned (for custom domain)

## 🔧 Step 1: Configure Environment Variables

### Get Backend URLs

After deploying the backend with AWS CDK, you'll get outputs like:

```bash
# Deploy backend
cd ../infrastructure
cdk deploy

# Outputs:
# SarkariSaathiStack.ApiGatewayUrl = https://abc123.execute-api.ap-south-1.amazonaws.com/prod
# SarkariSaathiStack.CloudFrontUrl = https://d123abc.cloudfront.net
# SarkariSaathiStack.ApiKey = your-api-key-here
```

### Update .env File

```bash
cd frontend
cp .env.example .env
```

Edit `.env`:

```env
REACT_APP_API_URL=https://abc123.execute-api.ap-south-1.amazonaws.com/prod
REACT_APP_API_KEY=your-api-key-here
REACT_APP_CLOUDFRONT_URL=https://d123abc.cloudfront.net
REACT_APP_USE_MOCK_DATA=false
REACT_APP_ENABLE_VOICE=true
REACT_APP_DEFAULT_LANGUAGE=hi-IN
```

## 🏗️ Step 2: Build Production Bundle

```bash
# Install dependencies
npm install

# Create optimized production build
npm run build

# Verify build
ls -lh build/
```

The `build/` directory will contain:

- `index.html` - Main HTML file
- `static/js/` - Minified JavaScript bundles
- `static/css/` - Minified CSS files
- `static/media/` - Images and other assets

## 🚀 Step 3: Deploy to AWS S3 + CloudFront

### Option A: Using AWS CLI

#### 1. Create S3 Bucket

```bash
# Create bucket
aws s3 mb s3://sarkari-saathi-frontend --region ap-south-1

# Enable static website hosting
aws s3 website s3://sarkari-saathi-frontend \
  --index-document index.html \
  --error-document index.html
```

#### 2. Configure Bucket Policy

Create `bucket-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::sarkari-saathi-frontend/*"
    }
  ]
}
```

Apply policy:

```bash
aws s3api put-bucket-policy \
  --bucket sarkari-saathi-frontend \
  --policy file://bucket-policy.json
```

#### 3. Upload Build Files

```bash
# Sync build folder to S3
aws s3 sync build/ s3://sarkari-saathi-frontend \
  --delete \
  --cache-control "public, max-age=31536000" \
  --exclude "index.html" \
  --exclude "service-worker.js"

# Upload index.html with no-cache
aws s3 cp build/index.html s3://sarkari-saathi-frontend/index.html \
  --cache-control "no-cache, no-store, must-revalidate"
```

#### 4. Create CloudFront Distribution

Create `cloudfront-config.json`:

```json
{
  "CallerReference": "sarkari-saathi-frontend-2026",
  "Comment": "SarkariSaathi Frontend Distribution",
  "DefaultRootObject": "index.html",
  "Origins": {
    "Quantity": 1,
    "Items": [
      {
        "Id": "S3-sarkari-saathi-frontend",
        "DomainName": "sarkari-saathi-frontend.s3.ap-south-1.amazonaws.com",
        "S3OriginConfig": {
          "OriginAccessIdentity": ""
        }
      }
    ]
  },
  "DefaultCacheBehavior": {
    "TargetOriginId": "S3-sarkari-saathi-frontend",
    "ViewerProtocolPolicy": "redirect-to-https",
    "AllowedMethods": {
      "Quantity": 2,
      "Items": ["GET", "HEAD"]
    },
    "ForwardedValues": {
      "QueryString": false,
      "Cookies": {
        "Forward": "none"
      }
    },
    "MinTTL": 0,
    "DefaultTTL": 86400,
    "MaxTTL": 31536000
  },
  "Enabled": true
}
```

Create distribution:

```bash
aws cloudfront create-distribution \
  --distribution-config file://cloudfront-config.json
```

#### 5. Invalidate CloudFront Cache (for updates)

```bash
aws cloudfront create-invalidation \
  --distribution-id YOUR_DISTRIBUTION_ID \
  --paths "/*"
```

### Option B: Using AWS CDK (Recommended)

Add to your CDK stack:

```typescript
import * as s3 from "aws-cdk-lib/aws-s3";
import * as s3deploy from "aws-cdk-lib/aws-s3-deployment";
import * as cloudfront from "aws-cdk-lib/aws-cloudfront";
import * as origins from "aws-cdk-lib/aws-cloudfront-origins";

// Create S3 bucket for frontend
const frontendBucket = new s3.Bucket(this, "FrontendBucket", {
  bucketName: "sarkari-saathi-frontend",
  websiteIndexDocument: "index.html",
  websiteErrorDocument: "index.html",
  publicReadAccess: true,
  removalPolicy: cdk.RemovalPolicy.DESTROY,
  autoDeleteObjects: true,
});

// Create CloudFront distribution
const distribution = new cloudfront.Distribution(this, "FrontendDistribution", {
  defaultBehavior: {
    origin: new origins.S3Origin(frontendBucket),
    viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
    cachePolicy: cloudfront.CachePolicy.CACHING_OPTIMIZED,
  },
  defaultRootObject: "index.html",
  errorResponses: [
    {
      httpStatus: 404,
      responseHttpStatus: 200,
      responsePagePath: "/index.html",
    },
  ],
});

// Deploy frontend build
new s3deploy.BucketDeployment(this, "DeployFrontend", {
  sources: [s3deploy.Source.asset("../frontend/build")],
  destinationBucket: frontendBucket,
  distribution,
  distributionPaths: ["/*"],
});

// Output URLs
new cdk.CfnOutput(this, "FrontendUrl", {
  value: `https://${distribution.distributionDomainName}`,
  description: "Frontend CloudFront URL",
});
```

Deploy:

```bash
cd infrastructure
cdk deploy
```

## 🌐 Step 4: Configure Custom Domain (Optional)

### 1. Request SSL Certificate

```bash
# Request certificate in us-east-1 (required for CloudFront)
aws acm request-certificate \
  --domain-name sarkari-saathi.example.com \
  --validation-method DNS \
  --region us-east-1
```

### 2. Validate Certificate

Add DNS records provided by ACM to your domain registrar.

### 3. Update CloudFront Distribution

```bash
aws cloudfront update-distribution \
  --id YOUR_DISTRIBUTION_ID \
  --distribution-config file://cloudfront-config-with-domain.json
```

### 4. Update DNS Records

Add CNAME record:

```
sarkari-saathi.example.com -> d123abc.cloudfront.net
```

## 🔄 Step 5: Continuous Deployment

### GitHub Actions Workflow

Create `.github/workflows/deploy-frontend.yml`:

```yaml
name: Deploy Frontend

on:
  push:
    branches: [main]
    paths:
      - "frontend/**"

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: "18"

      - name: Install dependencies
        working-directory: ./frontend
        run: npm ci

      - name: Build
        working-directory: ./frontend
        env:
          REACT_APP_API_URL: ${{ secrets.API_URL }}
          REACT_APP_API_KEY: ${{ secrets.API_KEY }}
          REACT_APP_CLOUDFRONT_URL: ${{ secrets.CLOUDFRONT_URL }}
        run: npm run build

      - name: Deploy to S3
        uses: jakejarvis/s3-sync-action@master
        with:
          args: --delete
        env:
          AWS_S3_BUCKET: sarkari-saathi-frontend
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          AWS_REGION: ap-south-1
          SOURCE_DIR: frontend/build

      - name: Invalidate CloudFront
        uses: chetan/invalidate-cloudfront-action@v2
        env:
          DISTRIBUTION: ${{ secrets.CLOUDFRONT_DISTRIBUTION_ID }}
          PATHS: "/*"
          AWS_REGION: ap-south-1
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
```

### Required GitHub Secrets

Add these secrets to your GitHub repository:

- `API_URL` - API Gateway URL
- `API_KEY` - API Key
- `CLOUDFRONT_URL` - CloudFront distribution URL
- `CLOUDFRONT_DISTRIBUTION_ID` - CloudFront distribution ID
- `AWS_ACCESS_KEY_ID` - AWS access key
- `AWS_SECRET_ACCESS_KEY` - AWS secret key

## 🧪 Step 6: Verify Deployment

### 1. Check S3 Bucket

```bash
aws s3 ls s3://sarkari-saathi-frontend/
```

### 2. Test CloudFront URL

```bash
curl -I https://d123abc.cloudfront.net
```

### 3. Test API Integration

Open browser console and check:

- Network tab for API calls
- Console for any errors
- Application tab for session storage

### 4. Test Features

- [ ] Voice input works
- [ ] Scheme matching returns results
- [ ] Language switching works
- [ ] Session persistence works
- [ ] Mobile responsive design works

## 📊 Step 7: Monitoring

### CloudWatch Metrics

Monitor these metrics:

- CloudFront requests
- S3 bucket size
- API Gateway requests
- Lambda invocations
- Error rates

### Set Up Alarms

```bash
# Create CloudWatch alarm for 4xx errors
aws cloudwatch put-metric-alarm \
  --alarm-name sarkari-saathi-frontend-4xx \
  --alarm-description "Alert on high 4xx error rate" \
  --metric-name 4xxErrorRate \
  --namespace AWS/CloudFront \
  --statistic Average \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2
```

## 🔒 Step 8: Security Hardening

### 1. Enable S3 Bucket Encryption

```bash
aws s3api put-bucket-encryption \
  --bucket sarkari-saathi-frontend \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'
```

### 2. Enable CloudFront Security Headers

Add response headers policy:

```json
{
  "SecurityHeadersConfig": {
    "StrictTransportSecurity": {
      "Override": true,
      "IncludeSubdomains": true,
      "Preload": true,
      "AccessControlMaxAgeSec": 31536000
    },
    "ContentTypeOptions": {
      "Override": true
    },
    "FrameOptions": {
      "Override": true,
      "FrameOption": "DENY"
    },
    "XSSProtection": {
      "Override": true,
      "Protection": true,
      "ModeBlock": true
    }
  }
}
```

### 3. Enable WAF (Optional)

```bash
# Create WAF web ACL
aws wafv2 create-web-acl \
  --name sarkari-saathi-frontend-waf \
  --scope CLOUDFRONT \
  --default-action Allow={} \
  --rules file://waf-rules.json
```

## 🚨 Troubleshooting

### Issue: 403 Forbidden

**Solution**: Check S3 bucket policy allows public read access

### Issue: Blank Page

**Solution**:

1. Check browser console for errors
2. Verify API URL in .env
3. Check CloudFront error responses configuration

### Issue: API Calls Failing

**Solution**:

1. Verify API Gateway CORS configuration
2. Check API key is correct
3. Verify backend is deployed and healthy

### Issue: Slow Loading

**Solution**:

1. Enable CloudFront compression
2. Optimize bundle size with code splitting
3. Use lazy loading for components

## 📝 Rollback Procedure

If deployment fails:

```bash
# Rollback S3 to previous version
aws s3 sync s3://sarkari-saathi-frontend-backup/ s3://sarkari-saathi-frontend/ --delete

# Invalidate CloudFront
aws cloudfront create-invalidation --distribution-id YOUR_DIST_ID --paths "/*"
```

## 🎯 Performance Optimization

### 1. Enable Compression

```bash
# CloudFront automatically compresses text files
# Verify in CloudFront behavior settings
```

### 2. Optimize Images

```bash
# Use WebP format
# Compress images before deployment
npm install -g imagemin-cli
imagemin public/images/* --out-dir=public/images/optimized
```

### 3. Code Splitting

Already configured in React. Verify in build output:

```
File sizes after gzip:
  45.2 KB  build/static/js/main.abc123.js
  1.2 KB   build/static/css/main.def456.css
```

## ✅ Post-Deployment Checklist

- [ ] Frontend accessible via CloudFront URL
- [ ] API integration working
- [ ] Voice input functional
- [ ] Scheme matching returns results
- [ ] Multi-language support working
- [ ] Mobile responsive
- [ ] HTTPS enabled
- [ ] Monitoring configured
- [ ] Alarms set up
- [ ] Documentation updated
- [ ] Team notified

---

**Deployment Complete! 🎉**

Frontend URL: https://your-cloudfront-url.cloudfront.net
Backend API: https://your-api-gateway-url.execute-api.ap-south-1.amazonaws.com/prod

For support, contact: [your-email@example.com]
