# SarkariSaathi - Government Scheme Navigator

> Voice-first AI assistant helping Indian citizens discover and apply for government schemes

[![AWS](https://img.shields.io/badge/AWS-Serverless-orange)](https://aws.amazon.com/)
[![Bedrock](https://img.shields.io/badge/Amazon-Bedrock-blue)](https://aws.amazon.com/bedrock/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.3-blue)](https://www.typescriptlang.org/)
[![CDK](https://img.shields.io/badge/AWS_CDK-2.118-green)](https://aws.amazon.com/cdk/)

## 🎯 Problem Statement

**70% of eligible citizens don't claim government benefits due to lack of awareness.**

SarkariSaathi bridges this gap by providing a voice-first, multilingual AI assistant that helps citizens:

- Discover schemes they're eligible for
- Understand complex eligibility criteria
- Navigate the application process
- Track application status

## 🏗️ Architecture

### Serverless AWS Stack

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interfaces                          │
│  Voice │ SMS │ IVR │ Web                                    │
└────┬────────┬──────┬──────────────────────────────────────┘
     │        │      │
     ▼        ▼      ▼
┌─────────────────────────────────────────────────────────────┐
│              API Gateway + Lambda Functions                  │
└────┬────────┬──────┬──────────────────────────────────────┘
     │        │      │
     ▼        ▼      ▼
┌─────────────────────────────────────────────────────────────┐
│  AI/ML Services                                             │
│  • Amazon Bedrock (Claude 3.5 Sonnet)                       │
│  • Amazon Transcribe (Speech-to-Text)                       │
│  • Amazon Polly (Text-to-Speech)                            │
│  • Amazon OpenSearch (RAG Vector Store)                     │
│  • Bhashini API (22+ Indian Languages)                      │
└─────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│  Data Layer                                                 │
│  • DynamoDB (Users, Schemes, Applications, Sessions)        │
│  • S3 (Audio Files, Documents, Cache)                       │
│  • ElastiCache (Session Management)                         │
└─────────────────────────────────────────────────────────────┘
```

### Key Features

✅ **Voice-First Interaction** - Natural conversation in 22+ Indian languages  
✅ **RAG-Based Eligibility Matching** - Semantic search across government schemes  
✅ **Multi-Channel Support** - Voice, SMS, IVR, and Web interfaces  
✅ **Feature Phone Compatible** - SMS/IVR bridge for basic phones  
✅ **Secure & Compliant** - KMS encryption, data residency in India  
✅ **Cost-Optimized** - Leverages AWS Free Tier, serverless architecture

## 🚀 Quick Start

### Prerequisites

- Node.js 20.x or higher
- AWS Account with credits
- AWS CLI configured
- AWS CDK installed globally

### Installation

```bash
# Clone the repository
git clone https://github.com/Techtitan-techy/SarkariSaathi.git
cd SarkariSaathi

# Install dependencies
npm install

# Configure AWS credentials
aws configure
# Region: ap-south-1 (Mumbai)

# Bootstrap CDK (first time only)
cdk bootstrap

# Deploy the stack
cdk deploy
```

### Project Structure

```
sarkari-saathi/
├── bin/
│   └── sarkari-saathi.ts          # CDK app entry point
├── lib/
│   └── sarkari-saathi-stack.ts    # Main CDK stack definition
├── lambda/
│   ├── shared/
│   │   └── types.ts               # TypeScript interfaces
│   ├── voice-processing/          # Voice input/output handlers
│   ├── eligibility-engine/        # RAG-based matching
│   ├── conversation-manager/      # Dialogue orchestration
│   └── sms-ivr-handlers/          # SMS/IVR integration
├── test/                          # Unit and integration tests
├── data/                          # Sample scheme documents
├── .kiro/specs/                   # Technical specifications
│   └── sarkari-saathi/
│       ├── requirements.md        # Detailed requirements
│       ├── design.md              # Architecture & design
│       └── tasks.md               # Implementation plan
├── cdk.json                       # CDK configuration
├── package.json                   # Dependencies
├── tsconfig.json                  # TypeScript config
└── PROGRESS.md                    # Implementation tracker
```

## 📋 Implementation Status

See [PROGRESS.md](./PROGRESS.md) for detailed implementation tracking.

**Current Phase:** Infrastructure Setup (Task 1)

- ✅ Project structure created
- ✅ CDK stack with DynamoDB tables
- ✅ S3 buckets with encryption
- ✅ IAM roles and permissions
- ✅ TypeScript interfaces defined
- ⏳ Lambda functions (in progress)

## 🛠️ Technology Stack

### Infrastructure

- **AWS CDK** - Infrastructure as Code
- **AWS Lambda** - Serverless compute
- **Amazon API Gateway** - REST APIs
- **Amazon CloudWatch** - Monitoring & logging

### AI/ML Services

- **Amazon Bedrock** - Claude 3.5 Sonnet for conversational AI
- **Amazon Transcribe** - Speech-to-text (English/Hindi)
- **Amazon Polly** - Text-to-speech
- **Amazon OpenSearch** - Vector store for RAG
- **Amazon Titan Embeddings** - Document vectorization
- **Amazon Translate** - 10+ Indian language support (Hindi, Bengali, Tamil, Telugu, Marathi, Gujarati, Kannada, Malayalam, Punjabi, Urdu)

### Data & Storage

- **Amazon DynamoDB** - NoSQL database
- **Amazon S3** - Object storage
- **Amazon ElastiCache** - Redis for caching
- **AWS KMS** - Encryption key management

### Communication

- **Amazon Connect** - IVR for voice calls
- **Amazon Pinpoint** - SMS gateway

## 📊 Supported Languages

- English (en)
- Hindi (hi)
- Tamil (ta)
- Telugu (te)
- Bengali (bn)
- Marathi (mr)
- Gujarati (gu)
- Kannada (kn)
- Malayalam (ml)
- Punjabi (pa)

## 🔒 Security

- **Encryption at Rest** - KMS-managed keys for all sensitive data
- **Encryption in Transit** - TLS 1.3 for all API communications
- **Data Residency** - All data stored in ap-south-1 (Mumbai) region
- **IAM Least Privilege** - Minimal permissions for all services
- **AWS WAF** - Protection against common web exploits

## 💰 Cost Optimization

- **AWS Free Tier** - Lambda, Transcribe, Polly, DynamoDB
- **On-Demand Billing** - Pay only for what you use
- **Intelligent Caching** - Reduce API calls with S3/ElastiCache
- **Lifecycle Policies** - Auto-delete old audio files
- **Right-Sizing** - Optimized Lambda memory allocation

**Estimated Cost:** $200-550/month for 1000-5000 users

## 📖 Documentation

- [Requirements Document](./.kiro/specs/sarkari-saathi/requirements.md)
- [Design Document](./.kiro/specs/sarkari-saathi/design.md)
- [Implementation Plan](./.kiro/specs/sarkari-saathi/tasks.md)
- [Progress Tracker](./PROGRESS.md)

## 🤝 Contributing

This project was built for the AWS AI for Bharat Hackathon. Contributions are welcome!

## 📄 License

MIT License - see LICENSE file for details

## 👥 Team

Built with ❤️ for the AI for Bharat Hackathon

## 🙏 Acknowledgments

- AWS for providing cloud infrastructure
- Bhashini for Indian language support
- Government of India for open scheme data

---

**Status:** 🚧 Under Active Development  
**Hackathon:** AWS AI for Bharat 2026  
**Repository:** https://github.com/Techtitan-techy/SarkariSaathi
