# IVR Implementation for SarkariSaathi

## Overview

The SarkariSaathi IVR (Interactive Voice Response) system provides voice-based access to government schemes information for users with basic feature phones. The system uses Amazon Connect for call handling, DTMF (touch-tone) input for navigation, and integrates with the existing conversation manager for dynamic responses.

## Architecture

```
┌─────────────────┐
│  User's Phone   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│   Amazon Connect        │
│   - Phone Number        │
│   - Contact Flow        │
│   - Call Recording      │
│   - Queue Management    │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  IVR Handler Lambda     │
│  - DTMF Processing      │
│  - Session Management   │
│  - Callback Scheduling  │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Conversation Manager    │
│  - Intent Classification│
│  - State Management     │
│  - Response Generation  │
└─────────────────────────┘
```

## Features

### 1. DTMF Menu Navigation

The IVR supports touch-tone input for users with basic phones:

- **1** - Discover government schemes
- **2** - Check eligibility
- **3** - Application guidance
- **4** - Speak to agent
- **9** - Repeat menu
- **0** - End call

### 2. Multilingual Support

- English and Hindi prompts
- Language detection and switching
- Text-to-speech using Amazon Polly

### 3. Call Recording

- All calls are recorded for quality assurance
- Recordings stored in encrypted S3 bucket
- Configurable retention policies

### 4. Callback System

- Users can schedule callbacks when agents are busy
- Automatic callback processing via EventBridge
- Callback status tracking in DynamoDB

### 5. Queue Management

- Intelligent call routing
- Queue time monitoring
- Automatic callback offer for long waits

## Components

### 1. IVR Handler Lambda (`lambda/ivr_handler.py`)

Main Lambda function that handles all IVR interactions:

**Functions:**

- `handle_incoming_call()` - Presents main menu
- `process_dtmf_input()` - Processes touch-tone input
- `generate_response()` - Creates dynamic responses
- `schedule_callback()` - Schedules user callbacks
- `get_callback_status()` - Retrieves callback information

**Environment Variables:**

- `SESSIONS_TABLE` - DynamoDB sessions table
- `IVR_CALLBACKS_TABLE` - DynamoDB callbacks table
- `CONVERSATION_MANAGER_FUNCTION` - Conversation manager Lambda ARN
- `CONNECT_INSTANCE_ID` - Amazon Connect instance ID
- `TTS_CACHE_BUCKET` - S3 bucket for cached audio

### 2. Contact Flow (`lambda/connect_contact_flow.json`)

Amazon Connect contact flow configuration:

**Flow Steps:**

1. Enable logging and recording
2. Invoke welcome Lambda
3. Play welcome message
4. Get DTMF input
5. Process input via Lambda
6. Check if call should end
7. Play response
8. Loop or transfer as needed

### 3. DynamoDB Tables

**IVR Callbacks Table:**

- Partition Key: `callbackId`
- GSI: `phoneNumber-index` (for user lookups)
- GSI: `status-index` (for processing pending callbacks)
- TTL: 7 days

**Sessions Table:**

- Stores IVR session state
- Tracks conversation context
- Links to user profiles

### 4. EventBridge Rule

Processes pending callbacks every 5 minutes:

- Rule: `sarkari-saathi-process-callbacks`
- Schedule: `rate(5 minutes)`
- Target: IVR Handler Lambda

## Setup Instructions

### Quick Setup

1. Deploy the CDK stack:

```bash
cd AI_for_bharat
npm run build
cdk deploy
```

2. Follow the manual Amazon Connect setup in `AMAZON_CONNECT_SETUP.md`

3. Run the automated configuration script:

```bash
chmod +x scripts/setup-connect-ivr.sh
./scripts/setup-connect-ivr.sh
```

4. Test the IVR by calling the phone number

### Manual Setup

See detailed instructions in `AMAZON_CONNECT_SETUP.md`

## Integration with Conversation Manager

The IVR system integrates seamlessly with the existing conversation manager:

```python
# IVR Handler invokes Conversation Manager
conversation_event = {
    'action': 'determineState',
    'sessionId': session_id,
    'userMessage': f"User selected: {action}",
    'language': language,
    'channel': 'ivr',
    'dtmfAction': action
}

response = lambda_client.invoke(
    FunctionName=CONVERSATION_MANAGER_FUNCTION,
    InvocationType='RequestResponse',
    Payload=json.dumps(conversation_event)
)
```

The conversation manager:

1. Classifies user intent
2. Determines next conversation state
3. Generates appropriate response
4. Returns response to IVR handler

## Call Flow Examples

### Example 1: Scheme Discovery

```
User calls → Welcome message
User presses 1 → Scheme discovery selected
System: "To discover schemes, I need information about you"
System: "Press 1 for age 18-30, 2 for 31-50, 3 for above 50"
User presses 2 → Age range selected
System: "Select category: 1-Education, 2-Healthcare, 3-Employment..."
User presses 1 → Education schemes
System: "I found 5 education schemes for you..."
```

### Example 2: Callback Request

```
User calls → Welcome message
User presses 3 → Application guidance
System: "For application help, press 1 for documents, 2 for process, 3 for callback"
User presses 3 → Callback requested
System: "Your callback has been scheduled for 2:00 PM. Thank you!"
Call ends
```

### Example 3: Agent Transfer

```
User calls → Welcome message
User presses 4 → Speak to agent
System: "Please wait while I connect you to an agent"
System transfers to queue
Agent answers → Human conversation
```

## Monitoring and Metrics

### CloudWatch Metrics

Monitor these key metrics:

1. **Call Volume**
   - Metric: `CallsPerInterval`
   - Namespace: `AWS/Connect`
   - Alarm threshold: 100 calls per 5 minutes

2. **Queue Time**
   - Metric: `QueueTime`
   - Namespace: `AWS/Connect`
   - Alarm threshold: 300 seconds (5 minutes)

3. **Lambda Errors**
   - Metric: `Errors`
   - Namespace: `AWS/Lambda`
   - Function: `SarkariSaathi-IvrHandler`

4. **Lambda Duration**
   - Metric: `Duration`
   - Namespace: `AWS/Lambda`
   - Target: < 3000ms

### CloudWatch Logs

Check these log groups:

- `/aws/lambda/SarkariSaathi-IvrHandler` - Lambda execution logs
- `/aws/connect/sarkari-saathi` - Amazon Connect logs
- `/aws/events/sarkari-saathi-callbacks` - EventBridge logs

### Amazon Connect Metrics Dashboard

Monitor in real-time:

- Calls in queue
- Average handle time
- Abandoned calls
- Service level
- Agent availability

## Cost Optimization

### Amazon Connect Pricing

- **Per-minute charges**: ~$0.018 per minute for voice
- **Phone number**: ~$0.03 per day
- **Call recording**: S3 storage costs

### Optimization Strategies

1. **Keep prompts concise** - Reduce call duration
2. **Use efficient menus** - Minimize navigation time
3. **Implement callbacks** - Reduce queue time
4. **Cache TTS audio** - Reduce Polly costs
5. **Archive old recordings** - Use S3 Glacier

### Estimated Costs

For 1000 calls/month with 3-minute average duration:

- Amazon Connect: ~$54/month
- Lambda: ~$2/month (within free tier)
- S3 Storage: ~$5/month
- **Total: ~$61/month**

## Testing

### Unit Testing

Test individual functions:

```python
# Test DTMF processing
event = {
    'Details': {
        'Parameters': {
            'dtmfInput': '1',
            'action': 'processDtmfInput'
        },
        'ContactData': {
            'CustomerEndpoint': {'Address': '+919876543210'},
            'ContactId': 'test-contact-123'
        }
    }
}

result = lambda_handler(event, None)
assert result['message'] is not None
```

### Integration Testing

Test with Amazon Connect:

1. Call the phone number
2. Test each menu option
3. Verify DTMF recognition
4. Check call recording
5. Test callback scheduling

### Load Testing

Simulate high call volume:

```bash
# Use Amazon Connect test utility
aws connect start-outbound-voice-contact \
  --instance-id YOUR_INSTANCE_ID \
  --contact-flow-id YOUR_FLOW_ID \
  --destination-phone-number +919876543210 \
  --source-phone-number +911234567890
```

## Troubleshooting

### Common Issues

#### 1. Lambda Not Invoked

**Symptoms:** Contact flow fails at Lambda invocation

**Solutions:**

- Check Lambda permissions in Amazon Connect
- Verify Lambda is in same region
- Check CloudWatch Logs for errors
- Verify Lambda timeout is sufficient (8 seconds)

#### 2. DTMF Not Recognized

**Symptoms:** User input not processed

**Solutions:**

- Increase timeout in "Get customer input" block
- Check DTMF settings on user's phone
- Test with different phones
- Verify contact flow configuration

#### 3. Call Recording Not Working

**Symptoms:** No recordings in S3

**Solutions:**

- Verify "Set recording behavior" block in flow
- Check S3 bucket permissions
- Verify KMS key access
- Check Amazon Connect instance settings

#### 4. Callback Not Scheduled

**Symptoms:** Callback not created in DynamoDB

**Solutions:**

- Check IVR Callbacks table
- Verify Lambda has write permissions
- Check EventBridge rule is enabled
- Review Lambda logs for errors

### Debug Mode

Enable debug logging:

```bash
aws ssm put-parameter \
  --name "/sarkari-saathi/features/enable-debug-logging" \
  --value "true" \
  --overwrite
```

## Security Considerations

### 1. Data Protection

- All call recordings encrypted with KMS
- PII masked in logs
- Secure parameter storage in SSM

### 2. Access Control

- IAM roles with least privilege
- Amazon Connect user permissions
- Lambda execution role restrictions

### 3. Compliance

- Call recording for quality assurance
- Data retention policies
- Audit logging with CloudTrail

### 4. Network Security

- VPC endpoints for AWS services
- Security groups for Lambda
- Private subnets for sensitive operations

## Future Enhancements

### Planned Features

1. **Voice Input Support**
   - Amazon Lex integration
   - Natural language understanding
   - Voice-to-text for complex queries

2. **Advanced Routing**
   - Skills-based routing
   - Priority queuing
   - Intelligent call distribution

3. **Analytics Dashboard**
   - Call analytics
   - User journey mapping
   - Performance metrics

4. **Multi-channel Integration**
   - SMS fallback
   - WhatsApp integration
   - Web chat support

5. **AI-Powered Features**
   - Sentiment analysis
   - Automatic summarization
   - Predictive routing

## References

- [Amazon Connect Documentation](https://docs.aws.amazon.com/connect/)
- [Lambda Integration Guide](https://docs.aws.amazon.com/connect/latest/adminguide/connect-lambda-functions.html)
- [Contact Flow Best Practices](https://docs.aws.amazon.com/connect/latest/adminguide/best-practices.html)
- [DTMF Configuration](https://docs.aws.amazon.com/connect/latest/adminguide/get-customer-input.html)

## Support

For issues or questions:

- Check CloudWatch Logs
- Review Amazon Connect metrics
- Consult `AMAZON_CONNECT_SETUP.md`
- Contact AWS Support for Connect-specific issues
