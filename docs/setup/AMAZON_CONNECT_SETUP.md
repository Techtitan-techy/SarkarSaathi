# Amazon Connect IVR Setup Guide for SarkariSaathi

This guide provides step-by-step instructions for setting up Amazon Connect for the SarkariSaathi IVR system with DTMF support, call recording, and callback functionality.

## Prerequisites

- AWS Account with appropriate permissions
- SarkariSaathi CDK stack deployed
- IVR Handler Lambda function deployed
- Phone number for testing

## Step 1: Create Amazon Connect Instance

### 1.1 Navigate to Amazon Connect Console

1. Open the AWS Console
2. Navigate to Amazon Connect service
3. Click "Create instance"

### 1.2 Configure Instance Identity Management

1. **Access URL**: Enter a unique subdomain (e.g., `sarkari-saathi-ivr`)
   - Full URL will be: `https://sarkari-saathi-ivr.my.connect.aws`
2. **Identity Management**: Select "Store users within Amazon Connect"
3. Click "Next"

### 1.3 Configure Administrator

1. **Add Administrator**:
   - First name: Admin
   - Last name: User
   - Username: admin
   - Email: your-email@example.com
   - Password: (set a strong password)
2. Click "Next"

### 1.4 Configure Telephony

1. **Incoming calls**: Enable "I want to handle incoming calls with Amazon Connect"
2. **Outgoing calls**: Enable "I want to make outbound calls with Amazon Connect"
3. Click "Next"

### 1.5 Configure Data Storage

1. **Call recordings**: Use default S3 bucket or specify custom bucket
2. **Exported reports**: Use default S3 bucket
3. **Enable encryption**: Check this option
4. Click "Next"

### 1.6 Review and Create

1. Review all settings
2. Click "Create instance"
3. Wait for instance creation (takes 2-3 minutes)
4. Note the **Instance ID** and **Instance ARN**

## Step 2: Claim Phone Number

### 2.1 Access Phone Numbers

1. In Amazon Connect console, select your instance
2. Click "Claim a phone number" or navigate to "Channels" > "Phone numbers"

### 2.2 Select Phone Number

1. **Country**: Select "India (+91)"
2. **Type**: Choose "DID (Direct Inward Dialing)"
3. **Phone number**: Select an available number or search for specific pattern
4. Click "Next"

### 2.3 Configure Phone Number

1. **Description**: "SarkariSaathi IVR Main Line"
2. **Contact flow**: Select "Sample inbound flow" (temporary - will update later)
3. Click "Save"
4. Note the **Phone Number** (e.g., +91-XXXXXXXXXX)

## Step 3: Configure Lambda Integration

### 3.1 Add Lambda Function to Amazon Connect

1. In Amazon Connect console, select your instance
2. Navigate to "Contact flows" > "AWS Lambda"
3. Click "Add Lambda Function"
4. Select the region where your Lambda is deployed
5. Find and select: `SarkariSaathi-IvrHandler`
6. Click "Add Lambda Function"

### 3.2 Grant Amazon Connect Permissions

The Lambda function already has permissions via the CDK stack. Verify by checking:

```bash
aws lambda get-policy --function-name SarkariSaathi-IvrHandler
```

You should see a policy allowing `connect.amazonaws.com` to invoke the function.

## Step 4: Create Contact Flow

### 4.1 Access Contact Flow Designer

1. In Amazon Connect console, select your instance
2. Click "Contact flows" in the left navigation
3. Click "Create contact flow"

### 4.2 Configure Contact Flow Basics

1. **Name**: "SarkariSaathi Main IVR Flow"
2. **Description**: "Main IVR flow with DTMF support for government schemes assistance"

### 4.3 Build Contact Flow

#### Entry Point

1. Drag "Set logging behavior" block to canvas
2. Connect from Entry point
3. Configure: Enable CloudWatch Logs

#### Enable Call Recording

1. Drag "Set recording and analytics behavior" block
2. Configure:
   - Call recording: Enable
   - Analytics: Enable
3. Connect from previous block

#### Welcome Message

1. Drag "Invoke AWS Lambda function" block
2. Configure:
   - Function ARN: Select `SarkariSaathi-IvrHandler`
   - Timeout: 8 seconds
   - Add parameter: `action` = `handleIncomingCall`
3. Connect from previous block

#### Play Welcome Prompt

1. Drag "Play prompt" block
2. Configure:
   - Type: Text-to-speech
   - Text: Use attribute `$.External.message`
   - Language: English (or Hindi based on `$.External.language`)
3. Connect from Lambda success

#### Get DTMF Input

1. Drag "Get customer input" block
2. Configure:
   - Type: User input
   - Audio prompt: "Please press a number"
   - Timeout: 10 seconds
   - Max digits: 1
   - Store customer input: Yes
   - Attribute name: `dtmfInput`
3. Connect from Play prompt

#### Process DTMF

1. Drag "Invoke AWS Lambda function" block
2. Configure:
   - Function ARN: Select `SarkariSaathi-IvrHandler`
   - Timeout: 8 seconds
   - Add parameter: `action` = `processDtmfInput`
   - Add parameter: `dtmfInput` = `$.StoredCustomerInput`
3. Connect from Get customer input

#### Check Should End

1. Drag "Check contact attributes" block
2. Configure:
   - Attribute: `$.External.shouldEnd`
   - Condition: Equals `true`
3. Connect from Lambda success
4. If true: Connect to "Disconnect" block
5. If false: Continue to next action

#### Play Response

1. Drag "Play prompt" block
2. Configure:
   - Type: Text-to-speech
   - Text: Use attribute `$.External.message`
3. Connect from Check Should End (false branch)

#### Check Next Action

1. Drag "Check contact attributes" block
2. Configure:
   - Attribute: `$.External.nextAction`
   - Conditions:
     - Equals `waitForDtmf`: Loop back to "Get DTMF Input"
     - Equals `returnToMenu`: Loop back to "Welcome Message"
     - Equals `transferToAgent`: Go to "Transfer to Queue"
3. Connect appropriately

#### Transfer to Agent Queue

1. Drag "Set working queue" block
2. Configure: Select "BasicQueue" (or create custom queue)
3. Drag "Transfer to queue" block
4. Connect Set working queue → Transfer to queue
5. Connect Transfer to queue → Disconnect

#### Error Handling

1. Drag "Play prompt" block for errors
2. Configure: "We're experiencing technical difficulties"
3. Connect all error branches to this block
4. Connect to Disconnect

#### Disconnect

1. Drag "Disconnect / hang up" block
2. Connect all end paths here

### 4.4 Save and Publish

1. Click "Save" button (top right)
2. Click "Publish" button
3. Note the **Contact Flow ID** from the URL or ARN

## Step 5: Create Agent Queue (Optional)

### 5.1 Create Queue

1. Navigate to "Routing" > "Queues"
2. Click "Add new queue"
3. Configure:
   - Name: "SarkariSaathi Support Queue"
   - Description: "Queue for agent transfers"
   - Hours of operation: 24/7 or custom
   - Maximum contacts in queue: 50
4. Click "Add new queue"
5. Note the **Queue ID**

### 5.2 Create Routing Profile

1. Navigate to "Users" > "Routing profiles"
2. Click "Add new profile"
3. Configure:
   - Name: "SarkariSaathi Agent Profile"
   - Queues: Add "SarkariSaathi Support Queue"
   - Channels: Voice
4. Click "Add new profile"

## Step 6: Update Configuration Parameters

### 6.1 Update SSM Parameters

Update the placeholder values in AWS Systems Manager Parameter Store:

```bash
# Update Connect Instance ID
aws ssm put-parameter \
  --name "/sarkari-saathi/connect/instance-id" \
  --value "YOUR_INSTANCE_ID" \
  --overwrite

# Update Contact Flow ID
aws ssm put-parameter \
  --name "/sarkari-saathi/connect/contact-flow-id" \
  --value "YOUR_CONTACT_FLOW_ID" \
  --overwrite

# Update Queue ID (if using agent transfer)
aws ssm put-parameter \
  --name "/sarkari-saathi/connect/queue-id" \
  --value "YOUR_QUEUE_ID" \
  --overwrite
```

### 6.2 Update Lambda Environment Variable

```bash
aws lambda update-function-configuration \
  --function-name SarkariSaathi-IvrHandler \
  --environment Variables="{
    CONNECT_INSTANCE_ID=YOUR_INSTANCE_ID,
    ...other variables...
  }"
```

## Step 7: Associate Contact Flow with Phone Number

### 7.1 Update Phone Number

1. Navigate to "Channels" > "Phone numbers"
2. Click on your claimed phone number
3. Update:
   - Contact flow: Select "SarkariSaathi Main IVR Flow"
4. Click "Save"

## Step 8: Configure Call Recording Storage

### 8.1 Access S3 Bucket

1. Navigate to S3 console
2. Find the bucket created by Amazon Connect (e.g., `amazon-connect-xxxxx`)
3. Note the bucket name

### 8.2 Configure Lifecycle Policy (Optional)

1. Click on the bucket
2. Go to "Management" tab
3. Create lifecycle rule:
   - Name: "Archive old recordings"
   - Transition to Glacier after 90 days
   - Delete after 365 days (or per compliance requirements)

### 8.3 Enable Encryption

1. Go to "Properties" tab
2. Enable "Default encryption"
3. Select AWS KMS key (use SarkariSaathi data encryption key)

## Step 9: Set Up Callback System

### 9.1 Create Callback Contact Flow

1. Create new contact flow: "SarkariSaathi Callback Flow"
2. Add blocks:
   - Set logging behavior
   - Invoke Lambda (action: `scheduleCallback`)
   - Play confirmation message
   - Disconnect

### 9.2 Create EventBridge Rule for Callbacks

```bash
aws events put-rule \
  --name sarkari-saathi-process-callbacks \
  --schedule-expression "rate(5 minutes)" \
  --state ENABLED

aws events put-targets \
  --rule sarkari-saathi-process-callbacks \
  --targets "Id"="1","Arn"="arn:aws:lambda:REGION:ACCOUNT:function:SarkariSaathi-IvrHandler"
```

## Step 10: Testing

### 10.1 Test Call Flow

1. Call the claimed phone number from your mobile
2. Verify:
   - Welcome message plays correctly
   - DTMF input is recognized
   - Menu navigation works
   - Call recording is enabled
   - Callback scheduling works

### 10.2 Test Lambda Integration

1. Check CloudWatch Logs for IVR Handler
2. Verify DynamoDB tables are being updated:
   - Sessions table
   - IVR Callbacks table
3. Test conversation manager integration

### 10.3 Test Different Languages

1. Call and select language option
2. Verify Hindi prompts play correctly
3. Test language switching

## Step 11: Monitoring and Metrics

### 11.1 Enable CloudWatch Metrics

1. Navigate to Amazon Connect console
2. Go to "Metrics and quality" > "Real-time metrics"
3. Monitor:
   - Calls in queue
   - Average handle time
   - Abandoned calls
   - Service level

### 11.2 Set Up Alarms

```bash
# High call volume alarm
aws cloudwatch put-metric-alarm \
  --alarm-name sarkari-saathi-high-call-volume \
  --alarm-description "Alert when call volume exceeds threshold" \
  --metric-name CallsPerInterval \
  --namespace AWS/Connect \
  --statistic Sum \
  --period 300 \
  --threshold 100 \
  --comparison-operator GreaterThanThreshold

# Long queue time alarm
aws cloudwatch put-metric-alarm \
  --alarm-name sarkari-saathi-long-queue-time \
  --alarm-description "Alert when queue time exceeds 5 minutes" \
  --metric-name QueueTime \
  --namespace AWS/Connect \
  --statistic Average \
  --period 300 \
  --threshold 300 \
  --comparison-operator GreaterThanThreshold
```

## Step 12: Cost Optimization

### 12.1 Monitor Usage

- Amazon Connect charges per minute of usage
- Review monthly usage in AWS Cost Explorer
- Set up budget alerts

### 12.2 Optimize Call Flows

- Keep prompts concise to reduce call duration
- Use efficient DTMF menus
- Implement callback system to reduce queue time

### 12.3 Review Call Recordings

- Implement retention policy
- Archive old recordings to Glacier
- Delete recordings after compliance period

## Troubleshooting

### Issue: Lambda Not Invoked

**Solution:**

1. Check Lambda permissions in Amazon Connect
2. Verify Lambda function is in same region
3. Check CloudWatch Logs for errors

### Issue: DTMF Not Recognized

**Solution:**

1. Verify "Get customer input" block configuration
2. Check timeout settings (increase if needed)
3. Test with different phones (some VoIP may have issues)

### Issue: Call Recording Not Working

**Solution:**

1. Verify "Set recording behavior" block is in flow
2. Check S3 bucket permissions
3. Verify encryption key access

### Issue: Callback Not Scheduled

**Solution:**

1. Check IVR Callbacks DynamoDB table
2. Verify Lambda has write permissions
3. Check EventBridge rule is enabled

## Security Best Practices

1. **Encryption**: Enable encryption for all call recordings
2. **Access Control**: Use IAM roles with least privilege
3. **Monitoring**: Enable CloudTrail for audit logging
4. **Data Retention**: Implement appropriate retention policies
5. **PCI Compliance**: If collecting payment info, enable PCI compliance features

## Next Steps

1. Create additional contact flows for specific use cases
2. Set up agent workspace for human support
3. Implement advanced routing based on user profile
4. Add multilingual support with Amazon Polly
5. Integrate with CRM for ticket management

## Resources

- [Amazon Connect Documentation](https://docs.aws.amazon.com/connect/)
- [Contact Flow Best Practices](https://docs.aws.amazon.com/connect/latest/adminguide/best-practices.html)
- [Lambda Integration Guide](https://docs.aws.amazon.com/connect/latest/adminguide/connect-lambda-functions.html)
- [Call Recording Guide](https://docs.aws.amazon.com/connect/latest/adminguide/set-up-recordings.html)

## Support

For issues or questions:

- Check CloudWatch Logs: `/aws/lambda/SarkariSaathi-IvrHandler`
- Review Amazon Connect metrics dashboard
- Contact AWS Support for Connect-specific issues
