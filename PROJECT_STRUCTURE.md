# SarkariSaathi Project Structure

## 📁 Root Directory

```
SarkariSaathi/
├── 📄 README.md                    # Main project documentation
├── 📄 package.json                 # Node.js dependencies
├── 📄 tsconfig.json                # TypeScript configuration
├── 📄 cdk.json                     # AWS CDK configuration
├── 📄 .gitignore                   # Git ignore rules
├── 📄 .env.example                 # Environment variables template
│
├── 📁 bin/                         # CDK app entry point
│   └── sarkari-saathi.ts
│
├── 📁 lib/                         # CDK infrastructure code
│   └── sarkari-saathi-stack.ts    # Main CDK stack definition
│
├── 📁 lambda/                      # Lambda function code
│   ├── audio_input_handler.py     # Audio upload handler
│   ├── speech_to_text.py          # Transcribe integration
│   ├── text_to_speech.py          # Polly integration
│   ├── conversation_manager.py    # Conversation orchestration
│   ├── sms_handler.py             # SMS processing
│   ├── ivr_handler.py             # IVR call handling
│   ├── eligibility_matcher.py     # Scheme matching logic
│   ├── bedrock_integration.py     # Claude AI integration
│   └── test_sms_ivr_integration.py # Integration tests
│
├── 📁 data/                        # Scheme data and seeds
│   ├── schemes_database.json      # Government schemes data
│   ├── seed_applications.json     # Sample applications
│   ├── seed_sessions.json         # Sample sessions
│   ├── SCHEMES_DATA_SOURCE.md     # Data sources documentation
│   ├── SCHEMES_UPDATE_2025.md     # Latest scheme updates
│   └── SCHEME_DATABASE_EXPANSION_PLAN.md
│
├── 📁 frontend/                    # React web interface
│   ├── public/                    # Static assets
│   ├── src/                       # React components
│   │   ├── components/            # UI components
│   │   ├── services/              # API services
│   │   └── App.tsx                # Main app component
│   ├── package.json               # Frontend dependencies
│   └── FRONTEND_UPDATE_SUMMARY.md # Frontend documentation
│
├── 📁 scripts/                     # Utility scripts
│   ├── setup-connect-ivr.sh      # Amazon Connect setup
│   └── seed-database.py          # Database seeding
│
├── 📁 test/                        # CDK tests
│   └── sarkari-saathi.test.ts
│
├── 📁 docs/                        # Documentation
│   ├── 📁 setup/                  # Setup guides
│   │   ├── AWS_COMPLETE_SETUP_GUIDE.md
│   │   ├── AMAZON_CONNECT_SETUP.md
│   │   ├── CLAUDE_SETUP_COMPLETE.md
│   │   ├── TRANSCRIBE_SETUP_GUIDE.md
│   │   └── BEDROCK_COST_CONTROL.md
│   │
│   ├── 📁 guides/                 # User guides
│   │   ├── RUN_APPLICATION.md
│   │   ├── QUICK_REFERENCE.md
│   │   ├── ERROR_HANDLING_GUIDE.md
│   │   └── COMPLETE_SCRAPING_GUIDE.md
│   │
│   ├── 📁 api/                    # API documentation
│   │   ├── INFRASTRUCTURE.md
│   │   ├── LAMBDA_FUNCTIONS.md
│   │   └── RAG_IMPLEMENTATION.md
│   │
│   └── REMAINING_TASKS_SUMMARY.md # Project status
│
├── 📁 .kiro/                       # Kiro AI specs
│   └── specs/sarkari-saathi/
│       ├── requirements.md        # Feature requirements
│       ├── design.md              # Technical design
│       └── tasks.md               # Implementation tasks
│
└── 📁 project-docs/                # Project submissions
    ├── Idea Submission.pdf
    └── Idea Submission.pptx
```

## 🗂️ Key Directories

### `/lib` - Infrastructure as Code

Contains AWS CDK stack definitions for:

- DynamoDB tables (Users, Sessions, Schemes, Applications)
- Lambda functions
- API Gateway
- S3 buckets
- OpenSearch domain
- Amazon Connect integration
- IAM roles and policies

### `/lambda` - Serverless Functions

Python Lambda functions for:

- **Voice Processing**: Audio upload, speech-to-text, text-to-speech
- **AI Integration**: Bedrock (Claude), conversation management
- **Communication**: SMS handler, IVR handler
- **Business Logic**: Eligibility matching, scheme discovery

### `/frontend` - Web Interface

React application with:

- Voice recording interface
- Text chat fallback
- Scheme browsing
- Application tracking
- Multilingual support

### `/data` - Scheme Database

Government scheme data including:

- 100+ schemes from various ministries
- Eligibility criteria
- Application procedures
- Multilingual content

### `/docs` - Documentation

Comprehensive guides for:

- **Setup**: AWS account creation to deployment
- **Guides**: Running, testing, troubleshooting
- **API**: Technical architecture and APIs

## 📝 Important Files

| File            | Purpose                          |
| --------------- | -------------------------------- |
| `README.md`     | Project overview and quick start |
| `cdk.json`      | CDK configuration and context    |
| `package.json`  | Node.js dependencies for CDK     |
| `.env.example`  | Environment variables template   |
| `tsconfig.json` | TypeScript compiler settings     |

## 🚀 Getting Started

1. **Setup AWS**: Follow `docs/setup/AWS_COMPLETE_SETUP_GUIDE.md`
2. **Install Dependencies**: `npm install`
3. **Deploy Infrastructure**: `cdk deploy`
4. **Run Frontend**: See `docs/guides/RUN_APPLICATION.md`

## 📊 Project Statistics

- **Lambda Functions**: 15+
- **DynamoDB Tables**: 5
- **Government Schemes**: 100+
- **Supported Languages**: 22+
- **Documentation Pages**: 20+
- **Test Coverage**: Integration tests for SMS/IVR

## 🔗 Related Links

- GitHub: https://github.com/Techtitan-techy/SarkarSaathi
- AWS CDK: https://aws.amazon.com/cdk/
- Amazon Bedrock: https://aws.amazon.com/bedrock/
- Amazon Connect: https://aws.amazon.com/connect/

## 📄 License

See LICENSE file for details.
