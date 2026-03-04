# ✅ Claude Setup Complete!

## Your Claude is Now Working!

I just tested it and got a successful response about government schemes in India.

## What Just Happened

1. ✅ AWS Bedrock is enabled in your account
2. ✅ Claude 3 Haiku is working (cheaper model, great for most tasks)
3. ✅ No manual activation needed - models auto-enable on first use
4. ✅ Your AWS CLI is properly configured

## Available Claude Models in Your Region (ap-south-1)

| Model                 | Model ID                                    | Best For                       | Cost     |
| --------------------- | ------------------------------------------- | ------------------------------ | -------- |
| **Claude 3 Haiku** ✅ | `anthropic.claude-3-haiku-20240307-v1:0`    | Simple queries, fast responses | Cheapest |
| **Claude 3 Sonnet**   | `anthropic.claude-3-sonnet-20240229-v1:0`   | Balanced performance           | Medium   |
| **Claude 3.5 Sonnet** | Requires inference profile                  | Complex reasoning              | Higher   |
| **Claude 4.5 Sonnet** | `anthropic.claude-sonnet-4-5-20250929-v1:0` | Latest, most capable           | Highest  |

## Test Response You Just Got

Claude successfully responded with information about:

- PM Awas Yojana (housing)
- MGNREGA (rural employment)
- Ayushman Bharat (health insurance)
- PM-KISAN (farmer income support)
- And 6 more schemes!

**Tokens used**: 19 input + 437 output = 456 total
**Cost**: ~$0.0006 (less than 1 cent)

## How to Use Claude in Your Project

### Method 1: AWS CLI (for testing)

```bash
# Test Claude
aws bedrock-runtime invoke-model \
  --model-id "anthropic.claude-3-haiku-20240307-v1:0" \
  --region ap-south-1 \
  --body file://test-bedrock.json \
  --cli-binary-format raw-in-base64-out \
  output.json

# View response
cat output.json
```

### Method 2: Python (for your Lambda functions)

```python
import boto3
import json

# Create Bedrock client
bedrock = boto3.client('bedrock-runtime', region_name='ap-south-1')

def call_claude(user_message):
    """Call Claude with a user message."""

    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1024,
        "messages": [
            {
                "role": "user",
                "content": user_message
            }
        ]
    })

    response = bedrock.invoke_model(
        modelId='anthropic.claude-3-haiku-20240307-v1:0',
        body=body
    )

    response_body = json.loads(response['body'].read())
    return response_body['content'][0]['text']

# Example usage
result = call_claude("Tell me about PM-KISAN scheme")
print(result)
```

### Method 3: In Your Existing Lambda Functions

Update your `lambda/bedrock_integration.py` or similar file:

```python
import boto3
import json
import os

class BedrockClient:
    def __init__(self):
        self.client = boto3.client('bedrock-runtime', region_name='ap-south-1')
        self.model_id = os.environ.get(
            'BEDROCK_MODEL_ID',
            'anthropic.claude-3-haiku-20240307-v1:0'
        )

    def generate_response(self, prompt, max_tokens=1024):
        """Generate AI response using Claude."""

        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "top_p": 0.9
        })

        try:
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=body
            )

            response_body = json.loads(response['body'].read())

            # Extract text and token usage
            text = response_body['content'][0]['text']
            usage = response_body['usage']

            print(f"Tokens used - Input: {usage['input_tokens']}, Output: {usage['output_tokens']}")

            return text

        except Exception as e:
            print(f"Error calling Bedrock: {str(e)}")
            raise
```

## Next Steps

### 1. Update Your CDK Stack

Make sure your Lambda functions have Bedrock permissions:

```typescript
// In lib/sarkari-saathi-stack.ts

// Add Bedrock permissions to Lambda execution role
conversationManagerFunction.addToRolePolicy(
  new iam.PolicyStatement({
    effect: iam.Effect.ALLOW,
    actions: ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
    resources: ["*"],
  }),
);
```

### 2. Set Environment Variables

```bash
# Add to your Lambda functions
aws lambda update-function-configuration \
  --function-name SarkariSaathi-ConversationManager \
  --environment Variables="{
    BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0,
    BEDROCK_REGION=ap-south-1,
    MAX_TOKENS=1024
  }"
```

### 3. Deploy Your Changes

```bash
# Build and deploy
npm run build
cdk deploy
```

### 4. Test End-to-End

```bash
# Test your API with Claude integration
curl -X POST https://YOUR-API-ID.execute-api.ap-south-1.amazonaws.com/prod/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Tell me about schemes for farmers",
    "userId": "test-user-123"
  }'
```

## Cost Monitoring

Your test just now cost: **$0.0006** (0.06 cents)

For 1000 similar queries: **~$0.60**

### Set Up Cost Alert

```bash
# Create CloudWatch alarm for Bedrock costs
aws cloudwatch put-metric-alarm \
  --alarm-name SarkariSaathi-Bedrock-Daily-Cost \
  --alarm-description "Alert when daily Bedrock cost exceeds $2" \
  --metric-name EstimatedCharges \
  --namespace AWS/Billing \
  --statistic Maximum \
  --period 86400 \
  --threshold 2 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=ServiceName,Value=AmazonBedrock
```

## Troubleshooting

### If You Get "Access Denied"

```bash
# Add Bedrock permissions to your IAM user
aws iam attach-user-policy \
  --user-name sarkari-saathi-admin \
  --policy-arn arn:aws:iam::aws:policy/AmazonBedrockFullAccess
```

### If Model Not Available

Some newer models require inference profiles. Stick with:

- ✅ `anthropic.claude-3-haiku-20240307-v1:0` (recommended)
- ✅ `anthropic.claude-3-sonnet-20240229-v1:0` (if you need more power)

### Check Available Models Anytime

```bash
aws bedrock list-foundation-models \
  --region ap-south-1 \
  --query "modelSummaries[?contains(modelId, 'claude')]" \
  --output table
```

## Summary

✅ **Claude is working in your AWS account**
✅ **No additional setup needed**
✅ **Ready to integrate into your Lambda functions**
✅ **Cost: ~$0.0006 per conversation**

You can now proceed with deploying your SarkariSaathi application with full AI capabilities!

## Quick Test Commands

```bash
# Test Claude Haiku (cheapest, fast)
aws bedrock-runtime invoke-model \
  --model-id "anthropic.claude-3-haiku-20240307-v1:0" \
  --region ap-south-1 \
  --body '{"anthropic_version":"bedrock-2023-05-31","max_tokens":1024,"messages":[{"role":"user","content":"Hello"}]}' \
  --cli-binary-format raw-in-base64-out \
  output.json && cat output.json

# Test Claude 3 Sonnet (more capable)
aws bedrock-runtime invoke-model \
  --model-id "anthropic.claude-3-sonnet-20240229-v1:0" \
  --region ap-south-1 \
  --body '{"anthropic_version":"bedrock-2023-05-31","max_tokens":1024,"messages":[{"role":"user","content":"Hello"}]}' \
  --cli-binary-format raw-in-base64-out \
  output.json && cat output.json
```

Happy building! 🚀
