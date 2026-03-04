# SarkariSaathi Infrastructure Setup

This document describes the AWS infrastructure foundation for SarkariSaathi, a voice-first AI assistant for Indian government schemes.

## Architecture Overview

The infrastructure is built using AWS CDK (Cloud Development Kit) with TypeScript and follows serverless best practices for cost optimization, security, and scalability.

### Key Components

1. **VPC and Networking**
   - Multi-AZ VPC with public and private subnets
   - VPC endpoints for DynamoDB and S3 (cost optimization)
   - Security groups for Lambda functions

2. **Data Storage**
   - **DynamoDB Tables**: Users, Applications, Schemes, Sessions
   - **S3 Buckets**: Audio files, scheme documents, TTS cache
   - **Encryption**: Customer-managed KMS keys with automatic rotation

3. **Security**
   - AWS KMS for encryption at rest
   - IAM roles with least privilege access
   - AWS Systems Manager Parameter Store for secrets
   - VPC isolation for Lambda functions

4. **API Layer**
   - API Gateway REST API with CORS enabled
   - CloudWatch logging and metrics
   - Request validation and transformation

## Region Configuration

**Primary Region**: `ap-south-1` (Mumbai, India)

This region is chosen for:

- Proximity to target users (Indian citizens)
- Lower latency for voice processing
- Compliance with data residency requirements
- Availability of all required AWS services (Bedrock, Transcribe, Polly)

## Prerequisites

1. **AWS Account**: Active AWS account with appropriate permissions
2. **AWS CLI**: Configured with credentials
3. **Node.js**: Version 18.x or higher
4. **TypeScript**: Version 5.x or higher
5. **AWS CDK**: Version 2.118.0 or higher

## Installation

### 1. Install Dependencies

```bash
npm install
```

### 2. Bootstrap CDK (First Time Only)

```bash
npm run bootstrap
```

This creates the necessary CDK resources in your AWS account.

### 3. Configure Environment Variables

Set your AWS account and region:

```bash
export CDK_DEFAULT_ACCOUNT=<your-account-id>
export CDK_DEFAULT_REGION=ap-south-1
```

### 4. Synthesize CloudFormation Template

```bash
npm run synth
```

This generates the CloudFormation template without deploying.

### 5. Deploy Infrastructure

```bash
npm run deploy
```

This deploys all infrastructure to your AWS account.

## Infrastructure Components

### DynamoDB Tables

| Table Name                 | Partition Key | GSIs                        | Purpose                          |
| -------------------------- | ------------- | --------------------------- | -------------------------------- |
| SarkariSaathi-Users        | userId        | phoneNumber-index           | User profiles and demographics   |
| SarkariSaathi-Applications | applicationId | userId-index, status-index  | Application tracking             |
| SarkariSaathi-Schemes      | schemeId      | category-index, state-index | Government schemes database      |
| SarkariSaathi-Sessions     | sessionId     | -                           | Conversation sessions (with TTL) |

### S3 Buckets

| Bucket                      | Purpose                | Lifecycle | Encryption |
| --------------------------- | ---------------------- | --------- | ---------- |
| sarkari-saathi-audio-\*     | Voice recordings       | 7 days    | KMS        |
| sarkari-saathi-schemes-\*   | Scheme documents       | Retained  | KMS        |
| sarkari-saathi-tts-cache-\* | Cached audio responses | 7 days    | S3-managed |

### IAM Permissions

The Lambda execution role has permissions for:

- DynamoDB read/write operations
- S3 read/write operations
- KMS encrypt/decrypt operations
- Amazon Bedrock model invocation (Claude 3.5 Sonnet)
- Amazon Transcribe transcription jobs
- Amazon Polly speech synthesis
- SSM Parameter Store read access

### Systems Manager Parameters

Configuration stored in Parameter Store:

| Parameter                                     | Purpose                     |
| --------------------------------------------- | --------------------------- |
| /sarkari-saathi/bhashini/api-key              | Bhashini API authentication |
| /sarkari-saathi/bhashini/api-url              | Bhashini API endpoint       |
| /sarkari-saathi/features/enable-bhashini      | Feature flag for Bhashini   |
| /sarkari-saathi/features/enable-debug-logging | Debug logging flag          |

**Note**: Update the Bhashini API key after deployment:

```bash
aws ssm put-parameter \
  --name /sarkari-saathi/bhashini/api-key \
  --value "YOUR_API_KEY" \
  --overwrite \
  --region ap-south-1
```

## Security Best Practices

1. **Encryption at Rest**: All data encrypted using customer-managed KMS keys
2. **Encryption in Transit**: TLS 1.3 for all API communications
3. **Least Privilege**: IAM roles follow principle of least privilege
4. **Secrets Management**: API keys stored in SSM Parameter Store
5. **Network Isolation**: Lambda functions in VPC with security groups
6. **Key Rotation**: Automatic KMS key rotation enabled

## Cost Optimization

The infrastructure is designed to maximize AWS Free Tier usage:

1. **DynamoDB**: On-demand billing mode (pay per request)
2. **Lambda**: Optimized memory allocation and execution time
3. **S3**: Lifecycle policies for automatic cleanup
4. **VPC**: No NAT gateways (using VPC endpoints instead)
5. **CloudWatch**: 7-day log retention for development

**Estimated Monthly Cost** (after Free Tier): $50-100 for moderate usage

## Monitoring and Logging

### CloudWatch Dashboards

- System health metrics (Lambda errors, API latency)
- Business metrics (user registrations, applications)
- Cost tracking and budget alerts

### CloudWatch Logs

- API Gateway access logs
- Lambda function logs
- VPC flow logs (optional)

**Log Retention**: 7 days (configurable)

## Testing

Run infrastructure tests:

```bash
npm test
```

Run tests with coverage:

```bash
npm run test:coverage
```

## Deployment Outputs

After deployment, the following outputs are available:

- **ApiEndpoint**: API Gateway URL
- **UsersTableName**: DynamoDB Users table name
- **AudioBucketName**: S3 audio bucket name
- **KMSKeyId**: KMS key ID for encryption
- **VPCId**: VPC ID for networking
- **BhashiniApiKeyParameter**: SSM parameter name for Bhashini API key

View outputs:

```bash
aws cloudformation describe-stacks \
  --stack-name SarkariSaathiStack \
  --query 'Stacks[0].Outputs' \
  --region ap-south-1
```

## Cleanup

To delete all infrastructure:

```bash
cdk destroy
```

**Warning**: This will delete all data. Ensure you have backups if needed.

## Troubleshooting

### CDK Bootstrap Issues

If bootstrap fails, ensure you have the required permissions:

```bash
aws sts get-caller-identity
```

### Deployment Failures

Check CloudFormation events:

```bash
aws cloudformation describe-stack-events \
  --stack-name SarkariSaathiStack \
  --region ap-south-1
```

### Permission Errors

Verify IAM role policies:

```bash
aws iam get-role-policy \
  --role-name SarkariSaathiStack-LambdaExecutionRole* \
  --policy-name default
```

## Next Steps

After infrastructure setup:

1. Deploy Lambda functions (Task 2)
2. Seed DynamoDB with scheme data (Task 16)
3. Configure Bhashini API credentials
4. Set up monitoring and alerting
5. Deploy frontend application

## Support

For issues or questions:

- Check AWS CloudWatch logs
- Review CDK synthesis output
- Consult AWS documentation
- Contact the development team

## References

- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- [AWS Free Tier](https://aws.amazon.com/free/)
- [Bhashini API Documentation](https://bhashini.gov.in/en/developers)
