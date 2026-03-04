# Bhashini API Alternatives for SarkariSaathi

## Problem

Unable to obtain Bhashini API access for Indian language support in the SarkariSaathi project.

## Recommended Solution: AWS Translate

### Why AWS Translate?

1. **Native AWS Integration** - Already using AWS infrastructure
2. **Indian Language Support** - Supports 10+ Indian languages
3. **Cost-Effective** - 2 million characters free per month for 12 months
4. **No API Key Required** - Uses existing AWS IAM credentials
5. **High Quality** - Neural machine translation with good accuracy

### Supported Indian Languages

AWS Translate supports the following Indian languages:

- **Hindi** (hi)
- **Bengali** (bn)
- **Tamil** (ta)
- **Telugu** (te)
- **Marathi** (mr)
- **Gujarati** (gu)
- **Kannada** (kn)
- **Malayalam** (ml)
- **Punjabi** (pa)
- **Urdu** (ur)

### Pricing

- **Free Tier**: 2 million characters/month for 12 months
- **After Free Tier**: $15 per million characters
- **Estimated Cost**: For 1000-5000 users, approximately $10-30/month

## Alternative Options

### 1. Google Cloud Translation API

**Pros:**

- Supports 100+ languages including all major Indian languages
- High accuracy
- Good documentation

**Cons:**

- Requires separate Google Cloud account
- $20 per million characters (more expensive than AWS)
- Additional integration complexity

### 2. Microsoft Azure Translator

**Pros:**

- Supports 90+ languages including Indian languages
- Good accuracy
- 2 million characters free per month

**Cons:**

- Requires Azure account
- $10 per million characters
- Additional cloud provider complexity

### 3. AI4Bharat IndicTrans2 (Open Source)

**Pros:**

- Free and open source
- Specifically designed for Indian languages
- 22 scheduled Indian languages
- Can be self-hosted

**Cons:**

- Requires hosting infrastructure
- More complex setup
- Need to manage model updates
- Higher latency than cloud APIs

**GitHub**: https://github.com/AI4Bharat/IndicTrans2

### 4. Reverie Language Technologies

**Pros:**

- India-focused company
- Supports 22+ Indian languages
- Good for Indian context

**Cons:**

- Commercial API (pricing not public)
- Requires separate account
- Less documentation than AWS/Google

## Implementation Plan

### Phase 1: Replace Bhashini with AWS Translate (Recommended)

1. **Add AWS Translate SDK**

   ```bash
   npm install @aws-sdk/client-translate
   ```

2. **Update Lambda Functions**
   - Replace Bhashini API calls with AWS Translate
   - Use existing IAM roles (no new API keys needed)

3. **Update Language Detection**
   - Use AWS Comprehend for language detection
   - Or use simple heuristics for common Indian languages

4. **Update Configuration**
   - Remove Bhashini API key parameters
   - Add AWS Translate configuration

### Phase 2: Hybrid Approach (Optional)

For languages not supported by AWS Translate:

- Use AWS Translate for supported languages (10 Indian languages)
- Fall back to Google Translate API for additional languages
- Or integrate AI4Bharat IndicTrans2 for specialized needs

## Code Changes Required

### 1. Update CDK Stack (lib/sarkari-saathi-stack.ts)

- Remove Bhashini SSM parameters
- Add AWS Translate permissions to Lambda roles
- Update environment variables

### 2. Update Lambda Functions

- Replace Bhashini client with AWS Translate client
- Update translation logic
- Update error handling

### 3. Update Configuration (lib/config.ts)

- Remove Bhashini configuration
- Add AWS Translate configuration

### 4. Update Tests

- Update test cases to use AWS Translate
- Mock AWS Translate responses

## Migration Steps

1. **Backup Current Code**

   ```bash
   git checkout -b feature/replace-bhashini-with-aws-translate
   ```

2. **Install Dependencies**

   ```bash
   npm install @aws-sdk/client-translate @aws-sdk/client-comprehend
   ```

3. **Update Infrastructure Code**
   - Modify CDK stack to add Translate permissions
   - Remove Bhashini parameters

4. **Update Lambda Functions**
   - Create AWS Translate service wrapper
   - Replace Bhashini calls

5. **Test Locally**
   - Test with mock data
   - Verify language detection

6. **Deploy to AWS**

   ```bash
   cdk deploy
   ```

7. **Verify in Production**
   - Test with real user inputs
   - Monitor CloudWatch logs

## Comparison Matrix

| Feature          | Bhashini     | AWS Translate  | Google Translate | AI4Bharat           |
| ---------------- | ------------ | -------------- | ---------------- | ------------------- |
| Indian Languages | 22+          | 10             | 15+              | 22                  |
| Free Tier        | Unknown      | 2M chars/month | 500K chars/month | Unlimited           |
| Cost (per 1M)    | Unknown      | $15            | $20              | Free (hosting cost) |
| AWS Integration  | External API | Native         | External API     | Self-hosted         |
| Setup Complexity | Medium       | Low            | Medium           | High                |
| API Availability | Limited      | High           | High             | Self-managed        |
| Quality          | Good         | Good           | Excellent        | Good                |

## Recommendation

**Use AWS Translate** as the primary solution because:

1. ✅ Already using AWS infrastructure
2. ✅ No additional API keys or accounts needed
3. ✅ Covers 10 major Indian languages (80%+ of users)
4. ✅ Cost-effective with generous free tier
5. ✅ Easy to implement (minimal code changes)
6. ✅ High availability and reliability

For the remaining languages, you can:

- Add Google Translate as a fallback (covers additional languages)
- Or wait for Bhashini API access and add it later as an enhancement

## Next Steps

Would you like me to:

1. ✅ Implement AWS Translate integration (recommended)
2. Create a hybrid solution with AWS Translate + Google Translate
3. Set up AI4Bharat IndicTrans2 for self-hosted solution
4. Create a comparison demo with multiple providers

---

**Note**: This document provides alternatives to Bhashini API. The recommended approach is to use AWS Translate for immediate implementation, with the option to add Bhashini later when API access becomes available.
