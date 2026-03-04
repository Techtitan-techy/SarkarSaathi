# RAG-Based Eligibility Engine Implementation

This document describes the implementation of the RAG (Retrieval-Augmented Generation) based eligibility engine for SarkariSaathi using Amazon OpenSearch and Amazon Bedrock.

## Architecture Overview

The RAG pipeline consists of three main components:

1. **Scheme Ingestion Pipeline** - Processes government scheme documents and indexes them in OpenSearch with vector embeddings
2. **Eligibility Matching Service** - Performs hybrid search to find relevant schemes based on user demographics
3. **Bedrock RAG Service** - Uses Claude 3.5 Sonnet to generate conversational responses with scheme context

## Components

### 1. OpenSearch Domain

**Infrastructure**: `lib/sarkari-saathi-stack.ts`

- **Instance Type**: t3.small.search (cost-optimized for hackathon)
- **Storage**: 10GB GP3 EBS volume
- **Security**: VPC-isolated with encryption at rest using KMS
- **Index**: `schemes` index with vector embeddings (1536 dimensions)

**Index Mapping**:

```json
{
  "schemeId": "keyword",
  "name": "text with keyword field",
  "description": "text",
  "category": "keyword",
  "state": "keyword",
  "eligibility": {
    "ageMin/Max": "integer",
    "incomeMin/Max": "long",
    "allowedStates": "keyword",
    "allowedCategories": "keyword"
  },
  "embedding": "knn_vector (1536 dimensions, cosine similarity)"
}
```

### 2. Scheme Ingestion Pipeline

**Lambda Function**: `lambda/scheme_ingestion_handler.py`

**Features**:

- Processes scheme documents from S3 or direct invocation
- Extracts metadata and eligibility criteria
- Generates embeddings using Amazon Titan Embeddings
- Indexes documents in OpenSearch with vector search support

**Usage**:

```bash
# Ingest schemes via API
curl -X POST https://api-endpoint/ingest \
  -H "Content-Type: application/json" \
  -d @data/sample_schemes.json

# Or use the seeding script
python scripts/seed_opensearch.py
```

### 3. Eligibility Matching Service

**Lambda Function**: `lambda/eligibility_matching_service.py`

**Features**:

- **Hybrid Search**: Combines keyword matching (40%) and semantic search (60%)
- **Eligibility Scoring**: Calculates match score based on:
  - Age range (20% weight)
  - Income range (25% weight)
  - State/location (15% weight)
  - Category (SC/ST/OBC/General) (15% weight)
  - Occupation (15% weight)
  - Disability status (10% weight)
- **Smart Filtering**: Pre-filters schemes by user demographics
- **Ranking**: Returns top 5 schemes sorted by combined relevance and eligibility score

**API Request**:

```json
{
  "query": "education schemes for farmers",
  "userProfile": {
    "age": 35,
    "income": 200000,
    "state": "Maharashtra",
    "category": "OBC",
    "occupation": "Farmer",
    "hasDisability": false
  },
  "category": "Education",
  "topK": 5
}
```

**API Response**:

```json
{
  "schemes": [
    {
      "schemeId": "sukanya-samriddhi-2024",
      "name": "Sukanya Samriddhi Yojana",
      "description": "...",
      "benefits": "...",
      "eligibilityScore": 0.85,
      "confidence": 0.85
    }
  ],
  "count": 5
}
```

### 4. Bedrock RAG Service

**Lambda Function**: `lambda/bedrock_rag_service.py`

**Features**:

- **Model**: Claude 3.5 Sonnet (anthropic.claude-3-5-sonnet-20240620-v1:0)
- **RAG Context Injection**: Injects scheme search results into prompts
- **Multilingual Support**: Responds in user's preferred language
- **Token Management**: Tracks token usage and estimates costs
- **Conversation History**: Maintains context across multiple turns

**System Prompt**:

- Positions assistant as SarkariSaathi helper
- Emphasizes simple, clear language
- Focuses on actionable guidance
- Culturally sensitive and empathetic

**API Request**:

```json
{
  "userMessage": "Tell me about education schemes for my daughter",
  "ragContext": "...",
  "userProfile": {
    "age": 35,
    "income": 300000,
    "state": "Karnataka"
  },
  "conversationHistory": [],
  "language": "en"
}
```

**API Response**:

```json
{
  "response": "Based on your profile, I recommend the Sukanya Samriddhi Yojana...",
  "inputTokens": 1250,
  "outputTokens": 450,
  "totalTokens": 1700,
  "estimatedCost": 0.0105,
  "model": "anthropic.claude-3-5-sonnet-20240620-v1:0"
}
```

## Sample Schemes Dataset

**File**: `data/sample_schemes.json`

Includes 10 popular government schemes:

1. PM-KISAN - Agriculture income support
2. Ayushman Bharat - Health insurance
3. PMAY-Urban - Housing assistance
4. Ujjwala Yojana - Free LPG connections
5. MUDRA Yojana - Micro-credit loans
6. Sukanya Samriddhi - Girl child savings
7. Atal Pension - Pension for unorganized sector
8. PMEGP - Employment generation
9. Jan Dhan Yojana - Financial inclusion
10. Fasal Bima - Crop insurance

Each scheme includes:

- Multilingual names (English, Hindi)
- Detailed descriptions
- Eligibility criteria (age, income, state, category, occupation)
- Benefits and application process
- Required documents
- Contact information

## Deployment

### Prerequisites

```bash
# Install dependencies
npm install
pip install -r lambda/requirements.txt

# Configure AWS credentials
aws configure
```

### Deploy Infrastructure

```bash
# Bootstrap CDK (first time only)
cdk bootstrap

# Deploy stack
cdk deploy

# Note the outputs:
# - OpenSearchEndpoint
# - ApiEndpoint
```

### Seed OpenSearch

```bash
# Wait for OpenSearch domain to be ready (10-15 minutes)
# Then seed with sample schemes
python scripts/seed_opensearch.py
```

## Testing

### Test Eligibility Matching

```bash
aws lambda invoke \
  --function-name SarkariSaathi-EligibilityMatching \
  --payload '{
    "query": "schemes for farmers",
    "userProfile": {
      "age": 40,
      "income": 150000,
      "state": "Maharashtra",
      "category": "General",
      "occupation": "Farmer"
    }
  }' \
  response.json

cat response.json | jq .
```

### Test Bedrock RAG

```bash
aws lambda invoke \
  --function-name SarkariSaathi-BedrockRAG \
  --payload '{
    "userMessage": "What schemes can help me with farming?",
    "ragContext": "PM-KISAN provides ₹6000 per year...",
    "userProfile": {
      "age": 40,
      "income": 150000,
      "state": "Maharashtra",
      "occupation": "Farmer"
    },
    "language": "en"
  }' \
  response.json

cat response.json | jq .
```

### Test via API Gateway

```bash
# Get API endpoint from CDK outputs
API_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name SarkariSaathiStack \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text)

# Test eligibility matching
curl -X POST ${API_ENDPOINT}schemes \
  -H "Content-Type: application/json" \
  -d '{
    "query": "education schemes",
    "userProfile": {
      "age": 8,
      "income": 400000,
      "state": "Karnataka",
      "category": "General"
    }
  }'

# Test chat
curl -X POST ${API_ENDPOINT}chat \
  -H "Content-Type: application/json" \
  -d '{
    "userMessage": "Tell me about Sukanya Samriddhi Yojana",
    "ragContext": "...",
    "userProfile": {
      "age": 35,
      "income": 400000,
      "state": "Karnataka"
    }
  }'
```

## Cost Optimization

### OpenSearch

- **Instance**: t3.small.search (~$30/month)
- **Storage**: 10GB GP3 (~$1/month)
- **Total**: ~$31/month

### Lambda

- **Free Tier**: 1M requests/month, 400K GB-seconds
- **Estimated**: $5-10/month for moderate usage

### Bedrock

- **Claude 3.5 Sonnet**:
  - Input: $0.003 per 1K tokens
  - Output: $0.015 per 1K tokens
- **Titan Embeddings**: $0.0001 per 1K tokens
- **Estimated**: $50-100/month for 1000-5000 queries

### Total Estimated Cost

- **Development**: ~$90/month
- **Production** (10K users): ~$300-500/month

## Performance Metrics

### Latency Targets

- **Scheme Ingestion**: < 5 seconds per scheme
- **Eligibility Matching**: < 2 seconds
- **Bedrock Response**: < 3 seconds
- **End-to-End**: < 5 seconds

### Accuracy Targets

- **Eligibility Matching**: > 90% precision
- **Semantic Search**: > 85% relevance
- **Response Quality**: > 90% user satisfaction

## Monitoring

### CloudWatch Metrics

- Lambda invocations and errors
- Lambda duration and memory usage
- OpenSearch cluster health
- Bedrock token usage and costs

### Custom Metrics

- Eligibility match accuracy
- User satisfaction scores
- Scheme discovery rate
- Application completion rate

## Next Steps

1. **Add More Schemes**: Expand from 10 to 100+ schemes
2. **Improve Embeddings**: Fine-tune embeddings for Indian context
3. **Add Caching**: Cache frequent queries in ElastiCache
4. **Implement Feedback Loop**: Learn from user interactions
5. **Add Analytics**: Track scheme popularity and user patterns

## Troubleshooting

### OpenSearch Connection Issues

```bash
# Check security group rules
aws ec2 describe-security-groups \
  --filters "Name=group-name,Values=*OpenSearch*"

# Check VPC endpoints
aws ec2 describe-vpc-endpoints
```

### Lambda Timeout Issues

```bash
# Increase timeout in CDK stack
timeout: cdk.Duration.minutes(5)

# Check CloudWatch logs
aws logs tail /aws/lambda/SarkariSaathi-EligibilityMatching --follow
```

### Bedrock Access Issues

```bash
# Verify model access in Bedrock console
aws bedrock list-foundation-models \
  --region ap-south-1 \
  --query 'modelSummaries[?contains(modelId, `claude-3-5-sonnet`)]'
```

## References

- [Amazon OpenSearch Service](https://docs.aws.amazon.com/opensearch-service/)
- [Amazon Bedrock](https://docs.aws.amazon.com/bedrock/)
- [Claude 3.5 Sonnet](https://www.anthropic.com/claude)
- [AWS CDK](https://docs.aws.amazon.com/cdk/)
