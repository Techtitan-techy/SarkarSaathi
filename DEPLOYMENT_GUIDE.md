# Deployment Guide - AWS Translate Integration

## 🎯 Overview

This guide walks you through deploying the SarkariSaathi application with AWS Translate integration (replacing Bhashini).

## ✅ Pre-Deployment Checklist

- [x] AWS SDK dependencies installed (`@aws-sdk/client-translate`, `@aws-sdk/client-comprehend`)
- [x] Translation service created (`lambda/shared/translationService.ts`)
- [x] CDK stack updated with AWS Translate permissions
- [x] Configuration files updated (removed Bhashini references)
- [x] Environment variables updated
- [x] Tests updated
- [x] Documentation updated

## 🚀 Deployment Steps

### Step 1: Verify AWS Credentials

```bash
# Check AWS credentials are configured
aws sts get-caller-identity

# Should return your AWS account details
```

### Step 2: Install Dependencies

```bash
# Install root dependencies
npm install

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### Step 3: Build the Project

```bash
# Build frontend
npm run build

# This will create optimized production build in frontend/build/
```

### Step 4: Bootstrap CDK (First Time Only)

```bash
# Bootstrap CDK in your AWS account
cdk bootstrap aws://ACCOUNT-ID/ap-south-1

# Replace ACCOUNT-ID with your AWS account ID
```

### Step 5: Review Changes

```bash
# See what will be deployed
cdk diff

# This shows:
# - Resources to be created
# - Resources to be modified
# - Resources to be deleted
```

### Step 6: Deploy to AWS

```bash
# Deploy the stack
cdk deploy

# Or deploy with auto-approval (skip confirmation)
cdk deploy --require-approval never
```

### Step 7: Verify Deployment

After deployment completes, you'll see outputs like:

```
Outputs:
SarkariSaathiStack.ApiEndpoint = https://xxxxxxxxxx.execute-api.ap-south-1.amazonaws.com/dev/
SarkariSaathiStack.ApiKeyId = xxxxxxxxxx
SarkariSaathiStack.OpenSearchEndpoint = https://xxxxxxxxxx.ap-south-1.es.amazonaws.com
```

## 🧪 Testing the Deployment

### Test 1: Health Check

```bash
# Test API Gateway health
curl https://YOUR-API-ENDPOINT/dev/health
```

### Test 2: Translation Service

```bash
# Test translation endpoint (if you have one)
curl -X POST https://YOUR-API-ENDPOINT/dev/translate \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR-API-KEY" \
  -d '{
    "text": "मुझे सरकारी योजनाओं के बारे में बताएं",
    "targetLanguage": "en"
  }'
```

### Test 3: Conversation Endpoint

```bash
# Test conversation with Hindi input
curl -X POST https://YOUR-API-ENDPOINT/dev/conversation \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR-API-KEY" \
  -d '{
    "message": "मुझे PM-KISAN योजना के बारे में बताएं",
    "sessionId": "test-session-123",
    "language": "hi"
  }'
```

## 📊 Monitoring

### CloudWatch Logs

```bash
# View Lambda logs
aws logs tail /aws/lambda/SarkariSaathi-ConversationManager --follow

# View API Gateway logs
aws logs tail /aws/apigateway/sarkari-saathi-access --follow
```

### CloudWatch Metrics

Monitor these metrics in CloudWatch:

- `AWS/Translate` - Translation usage and errors
- `AWS/Comprehend` - Language detection calls
- `AWS/Lambda` - Function invocations and errors
- `AWS/ApiGateway` - API requests and latency

### Cost Monitoring

```bash
# Check AWS Translate usage
aws cloudwatch get-metric-statistics \
  --namespace AWS/Translate \
  --metric-name CharacterCount \
  --start-time 2026-03-01T00:00:00Z \
  --end-time 2026-03-04T23:59:59Z \
  --period 86400 \
  --statistics Sum
```

## 🔧 Troubleshooting

### Issue: CDK Deploy Fails

**Solution:**

```bash
# Clean and rebuild
rm -rf cdk.out
cdk synth
cdk deploy
```

### Issue: Lambda Function Errors

**Solution:**

```bash
# Check Lambda logs
aws logs tail /aws/lambda/FUNCTION-NAME --follow

# Common issues:
# 1. Missing IAM permissions - Check CDK stack
# 2. Timeout - Increase timeout in CDK
# 3. Memory - Increase memory in CDK
```

### Issue: Translation Not Working

**Solution:**

1. Check IAM permissions for `translate:TranslateText`
2. Verify AWS Translate is available in `ap-south-1` region
3. Check CloudWatch logs for error messages
4. Verify language codes are correct (e.g., "hi" not "hindi")

### Issue: High Costs

**Solution:**

1. Enable caching for common translations
2. Monitor usage in CloudWatch
3. Set up billing alerts
4. Optimize translation calls (only translate user-facing text)

## 🔄 Updating the Deployment

### Update Lambda Code

```bash
# After making code changes
cdk deploy

# CDK will automatically:
# 1. Package Lambda functions
# 2. Upload to S3
# 3. Update Lambda functions
```

### Update Configuration

```bash
# Update SSM parameters
aws ssm put-parameter \
  --name "/sarkari-saathi/features/enable-aws-translate" \
  --value "true" \
  --overwrite

# Restart Lambda functions (they'll pick up new config)
```

### Rollback Deployment

```bash
# If something goes wrong, rollback
cdk deploy --previous-version

# Or manually in AWS Console:
# 1. Go to CloudFormation
# 2. Select your stack
# 3. Click "Rollback"
```

## 🗑️ Cleanup (Destroy Resources)

### Warning: This will delete all resources!

```bash
# Destroy the stack
cdk destroy

# Confirm when prompted
# This will delete:
# - Lambda functions
# - DynamoDB tables
# - S3 buckets (if empty)
# - API Gateway
# - All other resources
```

### Manual Cleanup

Some resources may need manual deletion:

1. S3 buckets with content
2. CloudWatch log groups
3. OpenSearch domain (if retention is set)

## 📈 Performance Optimization

### 1. Enable Caching

Add DynamoDB caching for common translations:

```typescript
// Cache translation in DynamoDB
const cacheKey = `${text}-${sourceLang}-${targetLang}`;
const cached = await getFromCache(cacheKey);
if (cached) return cached;

const translated = await translateText(text, sourceLang, targetLang);
await saveToCache(cacheKey, translated, 86400); // 24 hour TTL
```

### 2. Batch Translations

```typescript
// Instead of translating one by one
const translations = await Promise.all(
  texts.map((text) => translateText(text, "hi", "en")),
);
```

### 3. Reduce Translation Calls

- Only translate user input and final output
- Keep internal processing in English
- Cache common phrases

## 🔐 Security Best Practices

### 1. API Key Rotation

```bash
# Rotate API Gateway key
aws apigateway create-api-key --name "SarkariSaathi-API-Key-New"
aws apigateway update-usage-plan --usage-plan-id PLAN-ID --patch-operations op=add,path=/apiStages,value=API-ID:STAGE
```

### 2. Enable WAF

Already configured in CDK stack:

- Rate limiting
- IP blocking
- SQL injection protection

### 3. Monitor Access

```bash
# Check API access logs
aws logs filter-log-events \
  --log-group-name /aws/apigateway/sarkari-saathi-access \
  --filter-pattern "{ $.status = 403 }"
```

## 📞 Support

### AWS Support

- AWS Console: https://console.aws.amazon.com/support/
- AWS Documentation: https://docs.aws.amazon.com/

### Project Issues

- Check CloudWatch logs first
- Review CDK stack configuration
- Verify IAM permissions
- Test with AWS CLI

## 🎉 Success Criteria

Your deployment is successful when:

- ✅ CDK deploy completes without errors
- ✅ API Gateway endpoint is accessible
- ✅ Lambda functions execute successfully
- ✅ Translation works for Hindi, Tamil, Telugu, etc.
- ✅ CloudWatch logs show no errors
- ✅ Frontend can connect to backend
- ✅ Costs are within expected range

## 📝 Next Steps

After successful deployment:

1. ✅ Test all language translations
2. ✅ Set up CloudWatch alarms
3. ✅ Configure billing alerts
4. ✅ Update frontend with API endpoint
5. ✅ Load scheme data into DynamoDB
6. ✅ Test end-to-end user flows
7. ✅ Monitor performance and costs

---

**Deployment Date**: March 4, 2026  
**Version**: 1.0.0 with AWS Translate  
**Status**: Ready for Production
