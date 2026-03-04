#!/bin/bash

# Amazon Connect IVR Setup Script for SarkariSaathi
# This script helps automate the configuration of Amazon Connect after manual setup

set -e

echo "========================================="
echo "SarkariSaathi Amazon Connect IVR Setup"
echo "========================================="
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "Error: AWS CLI is not installed. Please install it first."
    exit 1
fi

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo "Error: jq is not installed. Please install it first."
    exit 1
fi

# Get AWS region
AWS_REGION=$(aws configure get region)
if [ -z "$AWS_REGION" ]; then
    echo "Error: AWS region not configured. Please run 'aws configure' first."
    exit 1
fi

echo "Using AWS Region: $AWS_REGION"
echo ""

# Prompt for Amazon Connect details
echo "Please enter your Amazon Connect configuration details:"
echo ""

read -p "Amazon Connect Instance ID: " CONNECT_INSTANCE_ID
if [ -z "$CONNECT_INSTANCE_ID" ]; then
    echo "Error: Instance ID is required"
    exit 1
fi

read -p "Contact Flow ID (Main IVR Flow): " CONTACT_FLOW_ID
if [ -z "$CONTACT_FLOW_ID" ]; then
    echo "Error: Contact Flow ID is required"
    exit 1
fi

read -p "Queue ID (for agent transfers, optional): " QUEUE_ID

read -p "Phone Number (e.g., +91XXXXXXXXXX): " PHONE_NUMBER

echo ""
echo "========================================="
echo "Configuration Summary"
echo "========================================="
echo "Instance ID: $CONNECT_INSTANCE_ID"
echo "Contact Flow ID: $CONTACT_FLOW_ID"
echo "Queue ID: ${QUEUE_ID:-Not provided}"
echo "Phone Number: ${PHONE_NUMBER:-Not provided}"
echo ""

read -p "Is this correct? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "Setup cancelled."
    exit 0
fi

echo ""
echo "Updating SSM Parameters..."

# Update Connect Instance ID
aws ssm put-parameter \
    --name "/sarkari-saathi/connect/instance-id" \
    --value "$CONNECT_INSTANCE_ID" \
    --overwrite \
    --region "$AWS_REGION" \
    --no-cli-pager

echo "✓ Updated Connect Instance ID parameter"

# Update Contact Flow ID
aws ssm put-parameter \
    --name "/sarkari-saathi/connect/contact-flow-id" \
    --value "$CONTACT_FLOW_ID" \
    --overwrite \
    --region "$AWS_REGION" \
    --no-cli-pager

echo "✓ Updated Contact Flow ID parameter"

# Update Queue ID if provided
if [ -n "$QUEUE_ID" ]; then
    aws ssm put-parameter \
        --name "/sarkari-saathi/connect/queue-id" \
        --value "$QUEUE_ID" \
        --overwrite \
        --region "$AWS_REGION" \
        --no-cli-pager
    echo "✓ Updated Queue ID parameter"
fi

# Update Phone Number if provided
if [ -n "$PHONE_NUMBER" ]; then
    aws ssm put-parameter \
        --name "/sarkari-saathi/connect/phone-number" \
        --value "$PHONE_NUMBER" \
        --overwrite \
        --region "$AWS_REGION" \
        --no-cli-pager
    echo "✓ Updated Phone Number parameter"
fi

echo ""
echo "Updating Lambda Environment Variables..."

# Get current Lambda environment variables
CURRENT_ENV=$(aws lambda get-function-configuration \
    --function-name SarkariSaathi-IvrHandler \
    --region "$AWS_REGION" \
    --query 'Environment.Variables' \
    --output json)

# Update CONNECT_INSTANCE_ID
UPDATED_ENV=$(echo "$CURRENT_ENV" | jq --arg id "$CONNECT_INSTANCE_ID" '. + {CONNECT_INSTANCE_ID: $id}')

# Update Lambda function
aws lambda update-function-configuration \
    --function-name SarkariSaathi-IvrHandler \
    --environment "Variables=$UPDATED_ENV" \
    --region "$AWS_REGION" \
    --no-cli-pager > /dev/null

echo "✓ Updated IVR Handler Lambda environment variables"

echo ""
echo "Granting Amazon Connect permission to invoke Lambda..."

# Add permission for Amazon Connect to invoke Lambda
aws lambda add-permission \
    --function-name SarkariSaathi-IvrHandler \
    --statement-id AllowConnectInvoke \
    --action lambda:InvokeFunction \
    --principal connect.amazonaws.com \
    --source-account $(aws sts get-caller-identity --query Account --output text) \
    --source-arn "arn:aws:connect:$AWS_REGION:$(aws sts get-caller-identity --query Account --output text):instance/$CONNECT_INSTANCE_ID" \
    --region "$AWS_REGION" \
    --no-cli-pager 2>/dev/null || echo "✓ Permission already exists"

echo "✓ Lambda permissions configured"

echo ""
echo "Setting up EventBridge rule for callback processing..."

# Create EventBridge rule for processing callbacks
aws events put-rule \
    --name sarkari-saathi-process-callbacks \
    --description "Process pending IVR callbacks every 5 minutes" \
    --schedule-expression "rate(5 minutes)" \
    --state ENABLED \
    --region "$AWS_REGION" \
    --no-cli-pager > /dev/null

echo "✓ Created EventBridge rule"

# Get Lambda ARN
LAMBDA_ARN=$(aws lambda get-function \
    --function-name SarkariSaathi-IvrHandler \
    --region "$AWS_REGION" \
    --query 'Configuration.FunctionArn' \
    --output text)

# Add Lambda as target
aws events put-targets \
    --rule sarkari-saathi-process-callbacks \
    --targets "Id"="1","Arn"="$LAMBDA_ARN","Input"='{"action":"processCallbacks"}' \
    --region "$AWS_REGION" \
    --no-cli-pager > /dev/null

echo "✓ Added Lambda target to EventBridge rule"

# Grant EventBridge permission to invoke Lambda
aws lambda add-permission \
    --function-name SarkariSaathi-IvrHandler \
    --statement-id AllowEventBridgeInvoke \
    --action lambda:InvokeFunction \
    --principal events.amazonaws.com \
    --source-arn "arn:aws:events:$AWS_REGION:$(aws sts get-caller-identity --query Account --output text):rule/sarkari-saathi-process-callbacks" \
    --region "$AWS_REGION" \
    --no-cli-pager 2>/dev/null || echo "✓ Permission already exists"

echo "✓ EventBridge permissions configured"

echo ""
echo "Setting up CloudWatch alarms..."

# High call volume alarm
aws cloudwatch put-metric-alarm \
    --alarm-name sarkari-saathi-high-call-volume \
    --alarm-description "Alert when call volume exceeds threshold" \
    --metric-name CallsPerInterval \
    --namespace AWS/Connect \
    --statistic Sum \
    --period 300 \
    --threshold 100 \
    --comparison-operator GreaterThanThreshold \
    --evaluation-periods 1 \
    --dimensions Name=InstanceId,Value="$CONNECT_INSTANCE_ID" \
    --region "$AWS_REGION" \
    --no-cli-pager 2>/dev/null || echo "✓ Alarm already exists"

echo "✓ Created high call volume alarm"

# Long queue time alarm
aws cloudwatch put-metric-alarm \
    --alarm-name sarkari-saathi-long-queue-time \
    --alarm-description "Alert when queue time exceeds 5 minutes" \
    --metric-name QueueTime \
    --namespace AWS/Connect \
    --statistic Average \
    --period 300 \
    --threshold 300 \
    --comparison-operator GreaterThanThreshold \
    --evaluation-periods 1 \
    --dimensions Name=InstanceId,Value="$CONNECT_INSTANCE_ID" \
    --region "$AWS_REGION" \
    --no-cli-pager 2>/dev/null || echo "✓ Alarm already exists"

echo "✓ Created long queue time alarm"

echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Test the IVR by calling: ${PHONE_NUMBER:-your phone number}"
echo "2. Monitor CloudWatch Logs: /aws/lambda/SarkariSaathi-IvrHandler"
echo "3. Check Amazon Connect metrics dashboard"
echo "4. Review call recordings in S3"
echo ""
echo "Configuration stored in SSM Parameter Store:"
echo "  - /sarkari-saathi/connect/instance-id"
echo "  - /sarkari-saathi/connect/contact-flow-id"
echo "  - /sarkari-saathi/connect/queue-id"
echo "  - /sarkari-saathi/connect/phone-number"
echo ""
echo "For detailed setup instructions, see: AMAZON_CONNECT_SETUP.md"
echo ""
