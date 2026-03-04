# CDK Setup and Deployment Guide

## ✅ Issues Fixed

1. **TypeScript Compilation Error** - Fixed `conversationManagerFunction` used before declaration
2. **OpenSearch Configuration** - Fixed T3 instance Multi-AZ standby issue
3. **Bhashini Migration** - Successfully replaced with AWS Translate

## ⚠️ Current Issue: Docker Not Running

CDK requires Docker to bundle Python Lambda functions. You're seeing this error:

```
failed to connect to the docker API at npipe:////./pipe/docker_engine
```

### Solution: Start Docker Desktop

1. **Install Docker Desktop** (if not installed):
   - Download from: https://www.docker.com/products/docker-desktop/
   - Install and restart your computer

2. **Start Docker Desktop**:
   - Open Docker Desktop application
   - Wait for it to fully start (whale icon in system tray should be steady)
   - Verify Docker is running:
     ```bash
     docker --version
     docker ps
     ```

3. **Then run CDK**:
   ```bash
   npx cdk synth
   ```

## Alternative: Skip Docker Bundling (Quick Test)

If you want to test CDK without Docker, you can temporarily disable bundling:

### Option 1: Use Pre-built Lambda Layers

Modify Lambda functions to use layers instead of bundling.

### Option 2: Deploy Without Python Functions

Comment out Python Lambda functions temporarily and deploy only TypeScript/Node.js functions.

### Option 3: Use WSL2 with Docker

If Docker Desktop doesn't work:

1. Enable WSL2
2. Install Docker in WSL2
3. Run CDK from WSL2

## 🚀 Once Docker is Running

### Step 1: Verify Docker

```bash
docker --version
# Should show: Docker version 20.x.x or higher

docker ps
# Should show: CONTAINER ID   IMAGE   COMMAND   CREATED   STATUS   PORTS   NAMES
# (empty list is fine)
```

### Step 2: Synthesize CDK Stack

```bash
npx cdk synth
# This will:
# - Compile TypeScript
# - Bundle Lambda functions using Docker
# - Generate CloudFormation template
```

### Step 3: Deploy to AWS

```bash
# First time only - bootstrap CDK
npx cdk bootstrap

# Deploy the stack
npx cdk deploy
```

## 📋 Pre-Deployment Checklist

- [x] AWS Translate integration complete
- [x] TypeScript compilation errors fixed
- [x] OpenSearch configuration fixed
- [ ] Docker Desktop installed and running
- [ ] AWS credentials configured (`aws configure`)
- [ ] CDK bootstrapped (`npx cdk bootstrap`)

## 🔧 Troubleshooting

### Docker Issues

**Issue**: Docker not starting
**Solution**:

- Restart Docker Desktop
- Check Windows Services - Docker Desktop Service should be running
- Try running as Administrator

**Issue**: Docker permission denied
**Solution**:

- Add your user to docker-users group
- Restart computer

**Issue**: WSL2 required
**Solution**:

- Enable WSL2: `wsl --install`
- Set WSL2 as default: `wsl --set-default-version 2`
- Restart Docker Desktop

### CDK Issues

**Issue**: CDK command not found
**Solution**: Use `npx cdk` instead of `cdk`

**Issue**: AWS credentials not configured
**Solution**:

```bash
aws configure
# Enter:
# - AWS Access Key ID
# - AWS Secret Access Key
# - Default region: ap-south-1
# - Default output format: json
```

**Issue**: CDK not bootstrapped
**Solution**:

```bash
npx cdk bootstrap aws://ACCOUNT-ID/ap-south-1
```

## 📊 What CDK Will Deploy

Once Docker is running, CDK will deploy:

### Infrastructure

- ✅ VPC with public/private subnets
- ✅ DynamoDB tables (Users, Schemes, Applications, Sessions)
- ✅ S3 buckets (Audio, Scheme Docs, TTS Cache)
- ✅ Lambda functions (with AWS Translate integration)
- ✅ API Gateway
- ✅ OpenSearch domain
- ✅ KMS encryption keys
- ✅ IAM roles and policies
- ✅ CloudWatch logs and alarms
- ✅ WAF rules
- ✅ Step Functions state machine

### AWS Translate Integration

- ✅ IAM permissions for Translate and Comprehend
- ✅ Translation service in Lambda shared layer
- ✅ Support for 10+ Indian languages
- ✅ No external API dependencies

## 💰 Estimated Costs

### Free Tier (First 12 Months)

- Lambda: 1M requests/month free
- DynamoDB: 25GB storage free
- S3: 5GB storage free
- AWS Translate: 2M characters/month free
- API Gateway: 1M requests/month free

### After Free Tier

- Lambda: ~$50-100/month
- DynamoDB: ~$50-100/month
- OpenSearch: ~$100-150/month
- AWS Translate: ~$420/month (30M characters)
- **Total**: ~$620-770/month for 1000-5000 users

## 🎯 Next Steps

1. **Start Docker Desktop** ✅ (Most Important!)
2. Verify Docker is running: `docker ps`
3. Run CDK synth: `npx cdk synth`
4. Review generated CloudFormation: Check `cdk.out/` folder
5. Deploy to AWS: `npx cdk deploy`
6. Test endpoints
7. Monitor CloudWatch logs

## 📞 Need Help?

### Docker Issues

- Docker Documentation: https://docs.docker.com/desktop/windows/
- Docker Community: https://forums.docker.com/

### CDK Issues

- AWS CDK Documentation: https://docs.aws.amazon.com/cdk/
- CDK Workshop: https://cdkworkshop.com/

### AWS Translate

- AWS Translate Documentation: https://docs.aws.amazon.com/translate/
- Supported Languages: https://docs.aws.amazon.com/translate/latest/dg/what-is-languages.html

---

## ✅ Summary

**Current Status**: CDK stack is ready, but Docker is required to bundle Lambda functions.

**Action Required**: Start Docker Desktop, then run `npx cdk synth`

**After Docker Starts**: Everything is ready for deployment! 🚀

---

**Last Updated**: March 4, 2026  
**CDK Version**: 2.1108.0  
**Status**: Ready for deployment (pending Docker)
