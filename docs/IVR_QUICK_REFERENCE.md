# IVR Quick Reference Guide

## DTMF Menu Structure

### Main Menu

```
Press 1 - Discover government schemes
Press 2 - Check eligibility
Press 3 - Application guidance
Press 4 - Speak to agent
Press 9 - Repeat menu
Press 0 - End call
```

### Scheme Discovery Submenu

```
Press 1 - Age 18-30 years
Press 2 - Age 31-50 years
Press 3 - Age above 50 years
Press 9 - Return to main menu
```

### Category Selection

```
Press 1 - Education schemes
Press 2 - Healthcare schemes
Press 3 - Employment schemes
Press 4 - Agriculture schemes
Press 5 - All schemes
Press 9 - Main menu
```

### Application Help Submenu

```
Press 1 - Required documents
Press 2 - Application process
Press 3 - Schedule callback
Press 9 - Main menu
```

## Key Configuration Parameters

### SSM Parameters

- `/sarkari-saathi/connect/instance-id` - Amazon Connect instance ID
- `/sarkari-saathi/connect/contact-flow-id` - Main IVR contact flow ID
- `/sarkari-saathi/connect/queue-id` - Agent queue ID
- `/sarkari-saathi/connect/phone-number` - IVR phone number
- `/sarkari-saathi/ivr/enable-recording` - Enable call recording (true/false)
- `/sarkari-saathi/ivr/max-queue-time` - Max queue time in seconds (default: 300)
- `/sarkari-saathi/ivr/callback-window` - Callback window in minutes (default: 60)

### Lambda Environment Variables

- `CONNECT_INSTANCE_ID` - Amazon Connect instance ID
- `SESSIONS_TABLE` - DynamoDB sessions table name
- `IVR_CALLBACKS_TABLE` - DynamoDB callbacks table name
- `CONVERSATION_MANAGER_FUNCTION` - Conversation manager Lambda name
- `TTS_CACHE_BUCKET` - S3 bucket for cached TTS audio

## Common Commands

### Update Connect Configuration

```bash
# Update instance ID
aws ssm put-parameter \
  --name "/sarkari-saathi/connect/instance-id" \
  --value "YOUR_INSTANCE_ID" \
  --overwrite

# Update contact flow ID
aws ssm put-parameter \
  --name "/sarkari-saathi/connect/contact-flow-id" \
  --value "YOUR_FLOW_ID" \
  --overwrite
```

### Check Lambda Logs

```bash
# Tail IVR handler logs
aws logs tail /aws/lambda/SarkariSaathi-IvrHandler --follow

# Get recent errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/SarkariSaathi-IvrHandler \
  --filter-pattern "ERROR"
```

### Monitor Call Metrics

```bash
# Get call volume
aws cloudwatch get-metric-statistics \
  --namespace AWS/Connect \
  --metric-name CallsPerInterval \
  --dimensions Name=InstanceId,Value=YOUR_INSTANCE_ID \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-01T23:59:59Z \
  --period 3600 \
  --statistics Sum
```

### Query Callbacks

```bash
# List pending callbacks
aws dynamodb scan \
  --table-name SarkariSaathi-IvrCallbacks \
  --filter-expression "#status = :status" \
  --expression-attribute-names '{"#status":"status"}' \
  --expression-attribute-values '{":status":{"S":"pending"}}'
```

## Troubleshooting Quick Fixes

### Lambda Not Responding

```bash
# Check Lambda status
aws lambda get-function --function-name SarkariSaathi-IvrHandler

# Update timeout
aws lambda update-function-configuration \
  --function-name SarkariSaathi-IvrHandler \
  --timeout 30
```

### DTMF Not Working

1. Check contact flow "Get customer input" block
2. Increase timeout to 10 seconds
3. Verify max digits is set to 1
4. Test with different phone

### Call Recording Issues

1. Verify "Set recording behavior" block in contact flow
2. Check S3 bucket permissions
3. Verify KMS key access
4. Check Amazon Connect instance settings

### Callback Not Scheduled

1. Check DynamoDB table: `SarkariSaathi-IvrCallbacks`
2. Verify EventBridge rule is enabled
3. Check Lambda permissions
4. Review CloudWatch Logs

## Contact Flow Block Reference

### Essential Blocks

- **Set logging behavior** - Enable CloudWatch logging
- **Set recording behavior** - Enable call recording
- **Invoke AWS Lambda** - Call IVR handler
- **Play prompt** - Play TTS message
- **Get customer input** - Capture DTMF
- **Check contact attributes** - Conditional logic
- **Transfer to queue** - Agent transfer
- **Disconnect** - End call

### Lambda Invocation Parameters

```json
{
  "action": "handleIncomingCall|processDtmfInput|generateResponse|scheduleCallback",
  "dtmfInput": "$.StoredCustomerInput",
  "sessionId": "$.Attributes.sessionId",
  "language": "$.Attributes.language"
}
```

## Response Format

### Lambda Response to Connect

```json
{
  "message": "Welcome to SarkariSaathi...",
  "shouldEnd": false,
  "nextAction": "waitForDtmf|returnToMenu|transferToAgent",
  "language": "en|hi"
}
```

## Monitoring Checklist

Daily:

- [ ] Check call volume metrics
- [ ] Review error logs
- [ ] Monitor queue times
- [ ] Check callback processing

Weekly:

- [ ] Review call recordings
- [ ] Analyze user patterns
- [ ] Check cost metrics
- [ ] Update contact flows if needed

Monthly:

- [ ] Review and archive old recordings
- [ ] Analyze performance trends
- [ ] Update documentation
- [ ] Plan improvements

## Emergency Contacts

### AWS Support

- Console: https://console.aws.amazon.com/support/
- Phone: Available in AWS Console

### Internal Team

- DevOps: Check team documentation
- Product: Check team documentation

## Useful Links

- [Amazon Connect Console](https://console.aws.amazon.com/connect/)
- [CloudWatch Logs](https://console.aws.amazon.com/cloudwatch/home#logsV2:log-groups)
- [Lambda Console](https://console.aws.amazon.com/lambda/)
- [DynamoDB Console](https://console.aws.amazon.com/dynamodb/)
- [SSM Parameter Store](https://console.aws.amazon.com/systems-manager/parameters)

## Version History

- v1.0 (2024-01-XX) - Initial IVR implementation
  - DTMF menu navigation
  - Call recording
  - Callback system
  - Multilingual support
