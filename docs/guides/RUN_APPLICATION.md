# How to Run SarkariSaathi Application

## Quick Start Guide

### Option 1: Run Frontend Only (Recommended for Demo)

The frontend works standalone with mock data - no backend deployment needed!

```bash
# Open a terminal and run:
cd frontend
npm install
npm start
```

The app will open at `http://localhost:3000` (or another port if 3000 is busy).

**Features Available:**

- ✅ Voice input (10+ Indian languages)
- ✅ Text chat interface
- ✅ Scheme discovery with mock data
- ✅ Eligibility matching
- ✅ Full UI/UX experience

### Option 2: Run with AWS Backend (Production)

To use the full backend with AWS services:

#### Step 1: Deploy Backend to AWS

```bash
# Make sure you have AWS credentials configured
aws configure

# Deploy the CDK stack
cdk bootstrap  # Only needed once
cdk deploy

# Note the outputs:
# - ApiEndpoint: https://xxxxx.execute-api.ap-south-1.amazonaws.com/dev
# - ApiKeyId: xxxxx
# - CloudFrontDistributionDomain: xxxxx.cloudfront.net
```

#### Step 2: Get API Key

```bash
# Get the API key value
aws apigateway get-api-key --api-key YOUR_API_KEY_ID --include-value
```

#### Step 3: Configure Frontend

```bash
cd frontend

# Create .env file
cp .env.example .env

# Edit .env and add:
# REACT_APP_API_URL=https://your-api-gateway-url.execute-api.ap-south-1.amazonaws.com/dev
# REACT_APP_API_KEY=your-api-key-value
# REACT_APP_USE_MOCK_DATA=false
```

#### Step 4: Run Frontend

```bash
npm install
npm start
```

### Option 3: Local Backend Development (Advanced)

For local backend testing, you can use AWS SAM:

```bash
# Install AWS SAM CLI
# https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html

# Build and run locally
sam build
sam local start-api --port 3001

# In another terminal, run frontend
cd frontend
npm start
```

## Current Status

Based on your setup:

1. **Frontend**: ✅ Ready to run
   - All dependencies installed
   - Mock data available
   - Works standalone

2. **Backend**: ⚠️ Requires AWS Deployment
   - CDK stack defined
   - Lambda functions ready
   - Needs AWS credentials and deployment

## Recommended Approach for Demo

**Just run the frontend!**

```bash
cd frontend
npm start
```

This gives you a fully functional demo with:

- Voice input in multiple languages
- Intelligent conversation
- Scheme recommendations
- Beautiful UI
- No AWS deployment needed

## Troubleshooting

### Port 3000 Already in Use

If you see "Something is already running on port 3000":

**Option A: Use different port**

- Press `Y` when prompted
- App will run on port 3001 or next available port

**Option B: Kill existing process**

```bash
# Windows
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# Then restart
npm start
```

### npm install fails

```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Voice input not working

- Use Chrome or Edge browser (best support)
- Allow microphone permissions
- Check internet connection (Web Speech API needs internet)
- Use text input as fallback

## What You'll See

### Frontend (http://localhost:3000)

1. **Landing Page**
   - SarkariSaathi header
   - Voice/Text input interface
   - Language selector

2. **Interaction**
   - Speak or type: "I am a 35 year old farmer from Punjab with income 200000"
   - AI responds with eligible schemes
   - Scheme cards appear below

3. **Features**
   - Multi-language support
   - Real-time conversation
   - Scheme details and application info
   - Responsive design

## Next Steps

1. **For Demo**: Just run frontend with mock data
2. **For Production**: Deploy to AWS and configure frontend
3. **For Development**: Set up local backend with SAM

## Need Help?

- Check `frontend/README.md` for detailed frontend docs
- Check `frontend/DEPLOYMENT.md` for deployment guide
- Check `FRONTEND_UPDATE_SUMMARY.md` for integration details
- Check AWS CloudWatch logs for backend issues

## Quick Commands Reference

```bash
# Frontend only (recommended)
cd frontend && npm start

# Backend deployment
cdk deploy

# Check backend status
aws cloudformation describe-stacks --stack-name SarkariSaathiStack

# View Lambda logs
aws logs tail /aws/lambda/SarkariSaathi-VoiceHandler --follow

# Frontend build for production
cd frontend && npm run build
```

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│                   Frontend                       │
│  (React App - http://localhost:3000)            │
│                                                  │
│  • Voice Input (Web Speech API)                 │
│  • Chat Interface                               │
│  • Scheme Display                               │
│  • Mock Data Service (Fallback)                 │
└─────────────────┬───────────────────────────────┘
                  │
                  │ (Optional - when backend deployed)
                  │
┌─────────────────▼───────────────────────────────┐
│              AWS Backend                         │
│                                                  │
│  • API Gateway + CloudFront                     │
│  • Lambda Functions                             │
│  • Step Functions (Conversation)                │
│  • Bedrock (Claude 3.5 Sonnet)                  │
│  • OpenSearch (Scheme Search)                   │
│  • DynamoDB (User Data)                         │
│  • S3 (Audio Storage)                           │
└──────────────────────────────────────────────────┘
```

## Success Indicators

✅ Frontend running: Browser opens to http://localhost:3000
✅ Voice working: Microphone icon pulses when speaking
✅ Chat working: Messages appear in chat interface
✅ Schemes working: Scheme cards display after providing info
✅ Languages working: Can switch between Hindi, English, etc.

## Demo Script

1. Open http://localhost:3000
2. Click microphone or use text input
3. Say/Type: "Namaste, I am a farmer from Punjab, age 35, income 2 lakh"
4. See AI response with scheme recommendations
5. Click on schemes to see details
6. Try different languages
7. Show application guidance

Perfect for hackathon demo! 🚀
