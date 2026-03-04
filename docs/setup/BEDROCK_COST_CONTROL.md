# Amazon Bedrock Cost Control Guide

## Understanding Bedrock Costs

Amazon Bedrock charges based on:

- **Input tokens**: Text you send to the model
- **Output tokens**: Text the model generates

### Pricing (ap-south-1 Mumbai)

**Claude 3.5 Sonnet:**

- Input: $3.00 per 1M tokens
- Output: $15.00 per 1M tokens

**Claude 3 Haiku (cheaper alternative):**

- Input: $0.25 per 1M tokens
- Output: $1.25 per 1M tokens

## Cost Estimation

### Token Calculation

- 1 token ≈ 4 characters
- 1 token ≈ 0.75 words
- 100 words ≈ 133 tokens

### Example Costs

**Simple Query:**

```
User: "Tell me about PM-KISAN scheme"
Input: ~50 tokens = $0.00015
Output: ~150 tokens = $0.00225
Total: $0.0024 (0.24 cents)
```

**Complex Query with Context:**

```
User: "Am I eligible for this scheme?" + scheme details
Input: ~500 tokens = $0.0015
Output: ~300 tokens = $0.0045
Total: $0.006 (0.6 cents)
```

### Monthly Estimates

| Users/Month | Queries/User | Total Queries | Estimated Cost |
| ----------- | ------------ | ------------- | -------------- |
| 100         | 10           | 1,000         | $4-6           |
| 500         | 10           | 5,000         | $20-30         |
| 1,000       | 10           | 10,000        | $40-60         |
| 5,000       | 10           | 50,000        | $200-300       |

## Cost Control Strategies

### 1. Set AWS Budget Alerts

```bash
# Create a budget alert
aws budgets create-budget \
  --account-id YOUR_ACCOUNT_ID \
  --budget file://budget.json \
  --notifications-with-subscribers file://notifications.json
```

**budget.json:**

```json
{
  "BudgetName": "SarkariSaathi-Bedrock-Budget",
  "BudgetLimit": {
    "Amount": "50",
    "Unit": "USD"
  },
  "TimeUnit": "MONTHLY",
  "BudgetType": "COST",
  "CostFilters": {
    "Service": ["Amazon Bedrock"]
  }
}
```

**notifications.json:**

```json
[
  {
    "Notification": {
      "NotificationType": "ACTUAL",
      "ComparisonOperator": "GREATER_THAN",
      "Threshold": 80,
      "ThresholdType": "PERCENTAGE"
    },
    "Subscribers": [
      {
        "SubscriptionType": "EMAIL",
        "Address": "your-email@example.com"
      }
    ]
  }
]
```

### 2. Implement Token Limits in Code

Update your Lambda functions to limit token usage:

```python
# In your Bedrock integration code
import boto3

bedrock = boto3.client('bedrock-runtime', region_name='ap-south-1')

def call_bedrock_with_limits(prompt, max_input_tokens=1000, max_output_tokens=500):
    """Call Bedrock with token limits to control costs."""

    # Truncate input if too long
    if len(prompt) > max_input_tokens * 4:  # Rough estimate
        prompt = prompt[:max_input_tokens * 4]

    response = bedrock.invoke_model(
        modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
        body={
            'anthropic_version': 'bedrock-2023-05-31',
            'max_tokens': max_output_tokens,  # Limit output
            'messages': [
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'temperature': 0.7,
            'top_p': 0.9
        }
    )

    return response
```

### 3. Use Cheaper Models for Simple Tasks

```python
def get_model_for_task(task_complexity):
    """Choose model based on task complexity."""

    if task_complexity == 'simple':
        # Use Haiku for simple queries (12x cheaper)
        return 'anthropic.claude-3-haiku-20240307-v1:0'
    elif task_complexity == 'medium':
        # Use Sonnet for medium complexity
        return 'anthropic.claude-3-5-sonnet-20241022-v2:0'
    else:
        # Use Opus only for very complex tasks
        return 'anthropic.claude-3-opus-20240229-v1:0'

# Example usage
def process_query(user_query):
    # Classify query complexity
    if len(user_query.split()) < 10:
        model = get_model_for_task('simple')
    else:
        model = get_model_for_task('medium')

    # Call appropriate model
    response = call_bedrock(model, user_query)
    return response
```

### 4. Implement Response Caching

```python
import hashlib
import json
from datetime import datetime, timedelta

# Cache responses to avoid repeated API calls
response_cache = {}

def get_cached_response(prompt, cache_ttl_hours=24):
    """Check if we have a cached response."""

    # Create cache key from prompt
    cache_key = hashlib.md5(prompt.encode()).hexdigest()

    # Check if cached and not expired
    if cache_key in response_cache:
        cached_data = response_cache[cache_key]
        cache_time = datetime.fromisoformat(cached_data['timestamp'])

        if datetime.now() - cache_time < timedelta(hours=cache_ttl_hours):
            print(f"Cache hit! Saved API call.")
            return cached_data['response']

    return None

def cache_response(prompt, response):
    """Cache the response."""
    cache_key = hashlib.md5(prompt.encode()).hexdigest()
    response_cache[cache_key] = {
        'response': response,
        'timestamp': datetime.now().isoformat()
    }
```

### 5. Monitor Usage with CloudWatch

Create a Lambda function to track token usage:

```python
import boto3

cloudwatch = boto3.client('cloudwatch')

def log_token_usage(input_tokens, output_tokens, model_id):
    """Log token usage to CloudWatch for monitoring."""

    cloudwatch.put_metric_data(
        Namespace='SarkariSaathi/Bedrock',
        MetricData=[
            {
                'MetricName': 'InputTokens',
                'Value': input_tokens,
                'Unit': 'Count',
                'Dimensions': [
                    {'Name': 'ModelId', 'Value': model_id}
                ]
            },
            {
                'MetricName': 'OutputTokens',
                'Value': output_tokens,
                'Unit': 'Count',
                'Dimensions': [
                    {'Name': 'ModelId', 'Value': model_id}
                ]
            },
            {
                'MetricName': 'EstimatedCost',
                'Value': (input_tokens * 0.000003) + (output_tokens * 0.000015),
                'Unit': 'None',
                'Dimensions': [
                    {'Name': 'ModelId', 'Value': model_id}
                ]
            }
        ]
    )
```

### 6. Set Up Cost Alarms

```bash
# Create alarm for daily Bedrock costs
aws cloudwatch put-metric-alarm \
  --alarm-name SarkariSaathi-Bedrock-Daily-Cost \
  --alarm-description "Alert when daily Bedrock cost exceeds $5" \
  --metric-name EstimatedCharges \
  --namespace AWS/Billing \
  --statistic Maximum \
  --period 86400 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1 \
  --dimensions Name=ServiceName,Value=AmazonBedrock
```

## Development Without Bedrock

If you want to develop without incurring Bedrock costs:

### Option 1: Mock Responses

```python
def mock_bedrock_response(prompt):
    """Return mock responses during development."""

    if 'PM-KISAN' in prompt:
        return {
            'response': 'PM-KISAN is a scheme for farmers...',
            'tokens': {'input': 50, 'output': 100}
        }
    elif 'eligibility' in prompt:
        return {
            'response': 'To check eligibility, I need your age, income...',
            'tokens': {'input': 50, 'output': 80}
        }
    else:
        return {
            'response': 'I can help you with government schemes.',
            'tokens': {'input': 50, 'output': 60}
        }

# Use environment variable to toggle
import os
USE_MOCK = os.environ.get('USE_MOCK_BEDROCK', 'false') == 'true'

def call_ai_model(prompt):
    if USE_MOCK:
        return mock_bedrock_response(prompt)
    else:
        return call_bedrock(prompt)
```

### Option 2: Use OpenAI API (Cheaper for Testing)

```python
import openai

def call_openai_instead(prompt):
    """Use OpenAI as cheaper alternative for development."""

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # Much cheaper than Bedrock
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500
    )

    return response.choices[0].message.content
```

### Option 3: Use Local Models (Free)

```python
# Use Ollama with local models
import requests

def call_local_model(prompt):
    """Use free local model via Ollama."""

    response = requests.post('http://localhost:11434/api/generate', json={
        'model': 'llama2',
        'prompt': prompt,
        'stream': False
    })

    return response.json()['response']
```

## Best Practices

1. **Always set max_tokens** to prevent runaway costs
2. **Cache common responses** (scheme descriptions, FAQs)
3. **Use Haiku for simple tasks** (12x cheaper than Sonnet)
4. **Monitor daily** via CloudWatch dashboard
5. **Set budget alerts** at 50%, 80%, and 100%
6. **Test with mocks** during development
7. **Optimize prompts** to be concise
8. **Batch requests** when possible
9. **Use streaming** only when necessary
10. **Review usage weekly** and optimize

## Emergency Cost Control

If costs are too high:

1. **Disable Bedrock temporarily**:

   ```python
   # Set environment variable
   BEDROCK_ENABLED=false
   ```

2. **Switch to fallback responses**:

   ```python
   # Use pre-written responses
   return get_template_response(query_type)
   ```

3. **Reduce max_tokens**:

   ```python
   max_tokens=200  # Instead of 500
   ```

4. **Increase cache TTL**:
   ```python
   cache_ttl_hours=72  # Instead of 24
   ```

## Conclusion

Bedrock costs are manageable with proper controls:

- Start small (100-500 users)
- Monitor closely
- Optimize continuously
- Scale gradually

Expected costs for hackathon/demo: **$5-20/month**
Expected costs for production (1000 users): **$40-60/month**
