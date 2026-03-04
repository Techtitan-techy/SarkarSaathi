# Error Handling and Fallback Mechanisms Guide

## Overview

This guide explains the centralized error handling and API fallback strategies implemented for the SarkariSaathi application. These mechanisms ensure robust, resilient operation even when external services fail.

## Components

### 1. Centralized Error Handler (`lambda/shared/error_handler.py`)

The error handler provides:

- **Custom error types** with multilingual messages
- **Severity levels** (INFO, WARNING, ERROR, CRITICAL)
- **CloudWatch logging** with structured logs
- **User-friendly error messages** in English and Hindi
- **Recovery suggestions** for common errors

#### Error Types

```python
from shared.error_handler import (
    TranscriptionError,      # Speech-to-text failures
    EligibilityError,        # User doesn't qualify for scheme
    APIError,                # External API failures
    DatabaseError,           # Database operation failures
    ValidationError,         # Input validation errors
    GovernmentAPIError       # Government service unavailable
)
```

#### Usage Example

```python
from shared.error_handler import ErrorHandler, TranscriptionError

handler = ErrorHandler()

try:
    # Your code that might fail
    result = transcribe_audio(audio_data)
except Exception as e:
    # Handle error with context
    context = {
        'user_id': user_id,
        'function': 'transcribe_audio',
        'session_id': session_id
    }
    return handler.handle_error(e, context, language='hi')
```

#### Using the Decorator

```python
from shared.error_handler import with_error_handling

@with_error_handling(language_field='preferredLanguage')
def lambda_handler(event, context):
    # Your Lambda function code
    # Errors are automatically caught and handled
    return {
        'statusCode': 200,
        'body': json.dumps({'result': 'success'})
    }
```

### 2. API Fallback Strategies (`lambda/shared/api_fallback.py`)

The fallback module provides:

- **Circuit Breaker Pattern** - Prevents cascading failures
- **Exponential Backoff** - Intelligent retry logic
- **Fallback Chains** - Primary → Secondary → Cached → Manual
- **Resilient API Clients** - Pre-configured for common services

#### Circuit Breaker

Protects against cascading failures by stopping requests to failing services:

```python
from shared.api_fallback import CircuitBreaker

# Create circuit breaker
cb = CircuitBreaker(
    name="BhashiniAPI",
    failure_threshold=5,      # Open after 5 failures
    recovery_timeout=60,      # Wait 60s before retry
    success_threshold=2       # Need 2 successes to close
)

# Use circuit breaker
try:
    result = cb.call(lambda: call_external_api())
except Exception as e:
    # Circuit is open or call failed
    print(f"Service unavailable: {e}")
```

**States:**

- **CLOSED**: Normal operation, all requests pass through
- **OPEN**: Service failing, reject all requests
- **HALF_OPEN**: Testing recovery, allow limited requests

#### Exponential Backoff

Implements intelligent retry logic with increasing delays:

```python
from shared.api_fallback import ExponentialBackoff

backoff = ExponentialBackoff(
    base_delay=1.0,           # Start with 1 second
    max_delay=60.0,           # Cap at 60 seconds
    max_retries=5,            # Try up to 5 times
    exponential_base=2.0      # Double delay each time
)

# Execute with retry
result = backoff.execute(
    lambda: call_unreliable_api(),
    retryable_exceptions=(ConnectionError, TimeoutError)
)
```

**Retry delays:** 1s → 2s → 4s → 8s → 16s → 32s (capped at max_delay)

#### Fallback Chain

Implements multi-level fallback strategy:

```python
from shared.api_fallback import FallbackChain

chain = FallbackChain("GetSchemeData")

# Add fallbacks in priority order
chain.add_fallback(
    func=lambda: get_from_government_api(),
    name="primary",
    priority=0
)
chain.add_fallback(
    func=lambda: get_from_cache(),
    name="cached",
    priority=1
)
chain.add_fallback(
    func=lambda: get_manual_instructions(),
    name="manual",
    priority=2
)

# Execute with automatic fallback
result = chain.execute()
if result['success']:
    print(f"Got data from: {result['fallbackUsed']}")
else:
    print(f"All fallbacks failed: {result['error']}")
```

#### Resilient API Client

Pre-configured client combining all strategies:

```python
from shared.api_fallback import ResilientAPIClient

client = ResilientAPIClient("MyService")

# Call with full fallback support
result = client.call_with_fallback(
    primary_func=lambda: call_primary_api(),
    cache_key="schemes/pm-kisan.json",
    manual_instructions={
        'en': "Visit government office for manual submission",
        'hi': "मैनुअल सबमिशन के लिए सरकारी कार्यालय जाएं"
    }
)

if result['success']:
    data = result['data']
    source = result['source']  # 'primary', 'cache', or 'manual'
else:
    print(f"Service unavailable: {result['error']}")
```

### 3. Service-Specific Clients

#### Bhashini Client

```python
from shared.api_fallback import bhashini_client

# Transcribe with automatic fallback
result = bhashini_client.transcribe(
    audio_data=audio_bytes,
    language='hi'
)

if result['success']:
    transcription = result['data']
    if result.get('source') == 'cache':
        print("Warning: Using cached transcription")
else:
    # Show manual instructions to user
    instructions = result['manualInstructions']
```

#### Government API Client

```python
from shared.api_fallback import government_api_client

# Submit application with fallback to manual instructions
result = government_api_client.submit_application(
    scheme_id='pm-kisan',
    application_data=form_data
)

if result['success']:
    tracking_number = result['data']['trackingNumber']
else:
    # Provide manual submission instructions
    manual_steps = result['manualInstructions']
    # Show to user in their language
```

## Error Response Format

All errors return a consistent format:

```json
{
  "success": false,
  "error": {
    "errorCode": "TRANSCRIPTION_ERROR",
    "errorMessage": "I couldn't understand your speech clearly. Could you please repeat that?",
    "severity": "WARNING",
    "retryable": true,
    "recoverySuggestion": "Please speak clearly and reduce background noise",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

## Multilingual Support

All error messages and recovery suggestions support multiple languages:

```python
from shared.error_handler import get_user_friendly_message, get_recovery_suggestion

# Get message in user's language
message_en = get_user_friendly_message('ELIGIBILITY_ERROR', 'en')
message_hi = get_user_friendly_message('ELIGIBILITY_ERROR', 'hi')

# Get recovery suggestion
suggestion_en = get_recovery_suggestion('API_ERROR', 'en')
suggestion_hi = get_recovery_suggestion('API_ERROR', 'hi')
```

**Supported Languages:**

- English (en)
- Hindi (hi)

## CloudWatch Logging

All errors are automatically logged to CloudWatch with structured format:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "severity": "ERROR",
  "errorType": "TranscriptionError",
  "errorMessage": "Low audio quality",
  "errorCode": "TRANSCRIPTION_ERROR",
  "retryable": true,
  "context": {
    "user_id": "user_123",
    "session_id": "session_456",
    "function": "speech_to_text_service"
  },
  "stackTrace": "..."
}
```

## Best Practices

### 1. Use Specific Error Types

```python
# Good - Specific error with context
raise EligibilityError(
    "Age criteria not met",
    reason={
        'en': "You must be between 18 and 60 years old",
        'hi': "आपकी आयु 18 से 60 वर्ष के बीच होनी चाहिए"
    }
)

# Avoid - Generic error
raise Exception("Not eligible")
```

### 2. Always Provide Context

```python
# Good - Rich context for debugging
context = {
    'user_id': user_id,
    'session_id': session_id,
    'function': 'check_eligibility',
    'scheme_id': scheme_id,
    'user_age': user_age
}
handler.handle_error(error, context, language)

# Avoid - No context
handler.handle_error(error, {}, language)
```

### 3. Cache Successful API Responses

```python
# Cache data for fallback
client = ResilientAPIClient("SchemeService")

# After successful API call
result = call_government_api()
client.cache_data(
    cache_key=f"schemes/{scheme_id}.json",
    data=result,
    ttl_hours=24
)
```

### 4. Provide Manual Instructions

```python
# Always have manual fallback
manual_instructions = {
    'en': "To apply manually:\n1. Visit nearest office\n2. Fill form\n3. Submit documents",
    'hi': "मैन्युअल रूप से आवेदन करने के लिए:\n1. निकटतम कार्यालय जाएं\n2. फॉर्म भरें\n3. दस्तावेज जमा करें"
}

result = client.call_with_fallback(
    primary_func=submit_online,
    manual_instructions=manual_instructions
)
```

### 5. Monitor Circuit Breaker State

```python
# Check circuit breaker health
cb = CircuitBreaker("CriticalService")
state = cb.get_state()

if state['state'] == 'OPEN':
    # Alert operations team
    send_alert(f"Circuit breaker {state['name']} is OPEN")
```

## Testing

Run the test suite to verify error handling:

```bash
python -m pytest lambda/test_error_handling.py -v
```

**Test Coverage:**

- ✅ Custom error types
- ✅ Error handler responses
- ✅ Circuit breaker states
- ✅ Exponential backoff retry
- ✅ Fallback chain execution
- ✅ Multilingual messages
- ✅ Integration scenarios

## Requirements Mapping

This implementation satisfies the following requirements:

- **Requirement 1.5**: Speech recognition failure handling with retry prompts
- **Requirement 4.3**: Eligibility failure explanations with alternative suggestions
- **Requirement 7.2**: Government API fallback to cached data with staleness warnings
- **Requirement 7.4**: API failure fallback to manual submission instructions
- **Requirement 10.4**: Critical error graceful degradation with alternatives

## Example: Complete Lambda Function

```python
from shared.error_handler import with_error_handling, TranscriptionError
from shared.api_fallback import bhashini_client, government_api_client

@with_error_handling(language_field='language')
def lambda_handler(event, context):
    """
    Example Lambda function with complete error handling
    """
    body = json.loads(event['body'])
    language = body.get('language', 'en')

    # Transcribe audio with fallback
    transcription_result = bhashini_client.transcribe(
        audio_data=body['audioData'],
        language=language
    )

    if not transcription_result['success']:
        # Return manual instructions
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': False,
                'message': transcription_result['manualInstructions'][language]
            })
        }

    # Get scheme data with fallback to cache
    scheme_result = government_api_client.get_scheme_data(
        scheme_id=body['schemeId'],
        use_cache=True
    )

    if scheme_result.get('source') == 'cache':
        # Warn user about potentially stale data
        warning = scheme_result['warning'][language]

    return {
        'statusCode': 200,
        'body': json.dumps({
            'success': True,
            'transcription': transcription_result['data'],
            'scheme': scheme_result['data'],
            'warning': warning if 'warning' in locals() else None
        })
    }
```

## Monitoring and Alerts

### CloudWatch Metrics

Monitor these metrics:

- Circuit breaker state changes
- Error rates by severity
- Fallback usage (primary vs cache vs manual)
- Retry attempts and success rates

### Recommended Alarms

1. **Critical Error Rate**: Alert if ERROR/CRITICAL > 5% of requests
2. **Circuit Breaker Open**: Alert when any circuit opens
3. **Cache Hit Rate**: Alert if cache hit rate < 50%
4. **API Failure Rate**: Alert if primary API failures > 20%

## Summary

The error handling and fallback mechanisms provide:

✅ **Resilience**: Services continue operating even when dependencies fail  
✅ **User Experience**: Clear, actionable error messages in user's language  
✅ **Observability**: Structured logging for debugging and monitoring  
✅ **Graceful Degradation**: Automatic fallback to cached data or manual instructions  
✅ **Self-Healing**: Circuit breakers prevent cascading failures and allow recovery

This ensures SarkariSaathi remains accessible and helpful even under adverse conditions.
