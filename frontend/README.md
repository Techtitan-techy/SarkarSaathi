# SarkariSaathi Frontend

Voice-first AI assistant for discovering and applying to Indian government schemes. Built with React and integrated with AWS serverless backend.

## 🚀 Features

- **Voice-First Interface**: Record voice queries in 10+ Indian languages
- **Intelligent Conversation**: State-based conversation management with context retention
- **Scheme Discovery**: AI-powered matching based on user demographics
- **Multi-Language Support**: Hindi, English, Tamil, Telugu, Bengali, Marathi, Gujarati, Kannada, Malayalam, Punjabi
- **Real-Time Updates**: Live scheme data from government sources
- **Responsive Design**: Works on desktop, mobile, and tablets

## 🏗️ Architecture

### Frontend Stack

- **React 18**: Modern UI framework
- **JavaScript (ES6+)**: Core language
- **CSS-in-JS**: Inline styling for component isolation
- **Browser APIs**: MediaRecorder for voice input

### Backend Integration

- **AWS API Gateway**: RESTful API endpoints
- **AWS Lambda**: Serverless compute
  - `conversation_manager.py`: State-based conversation orchestration
  - `voice_handler.py`: Voice processing (upload, transcribe, synthesize)
  - `chat_handler.py`: Chat message handling with Bedrock
  - `scheme_handler.py`: Scheme matching and eligibility
- **Amazon Bedrock**: Claude 3.5 Sonnet for conversational AI
- **Amazon Transcribe**: Speech-to-text (English, Hindi)
- **Bhashini API**: Speech-to-text for 22+ Indian languages
- **Amazon Polly**: Text-to-speech with neural voices
- **Amazon OpenSearch**: Vector search for scheme matching
- **Amazon DynamoDB**: Session and user data storage

## 📋 Prerequisites

- Node.js 16+ and npm
- AWS Account (for backend deployment)
- AWS CDK CLI (for infrastructure deployment)

## 🛠️ Installation

```bash
# Install dependencies
npm install

# Copy environment template
cp .env.example .env

# Update .env with your API Gateway URL after backend deployment
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the frontend directory:

```env
# API Gateway URL (update after CDK deployment)
REACT_APP_API_URL=https://your-api-gateway-url.execute-api.ap-south-1.amazonaws.com/prod

# API Key (update after CDK deployment)
REACT_APP_API_KEY=your-api-key-here

# CloudFront Distribution URL (optional, for faster API access)
REACT_APP_CLOUDFRONT_URL=https://your-cloudfront-distribution.cloudfront.net

# Feature Flags
REACT_APP_USE_MOCK_DATA=false
REACT_APP_ENABLE_VOICE=true
REACT_APP_ENABLE_SMS=false

# Default Language
REACT_APP_DEFAULT_LANGUAGE=hi-IN
```

### API Endpoints

The frontend integrates with these backend endpoints:

| Endpoint             | Method | Description                               |
| -------------------- | ------ | ----------------------------------------- |
| `/conversation`      | POST   | Send message through conversation manager |
| `/voice/upload`      | POST   | Upload audio file for transcription       |
| `/voice/transcribe`  | POST   | Transcribe audio to text                  |
| `/voice/synthesize`  | POST   | Convert text to speech                    |
| `/chat/session`      | POST   | Create new chat session                   |
| `/chat/message`      | POST   | Send chat message                         |
| `/chat/session/{id}` | GET    | Get session history                       |
| `/schemes`           | GET    | Get all schemes                           |
| `/schemes/{id}`      | GET    | Get specific scheme                       |
| `/schemes/match`     | POST   | Match schemes to user profile             |
| `/health`            | GET    | Backend health check                      |

## 🚀 Development

```bash
# Start development server
npm start

# Open browser to http://localhost:3000
```

The app will run in mock data mode if the backend is not available. This allows frontend development without deploying the backend.

## 🏭 Production Build

```bash
# Create optimized production build
npm run build

# The build folder contains static files ready for deployment
```

## 📦 Deployment Options

### Option 1: AWS S3 + CloudFront (Recommended)

```bash
# Build the app
npm run build

# Deploy to S3 (using AWS CLI)
aws s3 sync build/ s3://your-bucket-name --delete

# Invalidate CloudFront cache
aws cloudfront create-invalidation --distribution-id YOUR_DIST_ID --paths "/*"
```

### Option 2: AWS Amplify

```bash
# Install Amplify CLI
npm install -g @aws-amplify/cli

# Initialize Amplify
amplify init

# Add hosting
amplify add hosting

# Publish
amplify publish
```

### Option 3: Vercel/Netlify

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
vercel --prod
```

## 🧪 Testing

```bash
# Run tests
npm test

# Run tests with coverage
npm test -- --coverage
```

## 📱 Features in Detail

### Voice Input

- Browser-based voice recording using MediaRecorder API
- Automatic language detection
- Real-time transcription feedback
- Fallback to text input if voice not supported

### Conversation Management

- State-based conversation flow (Welcome → Profile Collection → Scheme Discovery → Eligibility Check → Application Guidance)
- Context retention across multiple turns
- Language switching mid-conversation
- Session persistence

### Scheme Matching

- AI-powered eligibility scoring
- Multi-criteria matching (age, income, state, occupation, category)
- Real-time scheme recommendations
- Detailed scheme information with benefits and documents

### Accessibility

- Voice-first design for low-literacy users
- Multi-language support for regional languages
- Simple, clear UI with large buttons
- Mobile-responsive design

## 🔒 Security

- API key authentication for backend requests
- Session-based user tracking (no PII in frontend)
- HTTPS-only communication
- CORS configuration for API Gateway
- No sensitive data stored in browser localStorage

## 🐛 Troubleshooting

### Backend Not Available

- Check if `REACT_APP_API_URL` is set correctly in `.env`
- Verify API Gateway is deployed and accessible
- Check browser console for CORS errors
- App will fall back to mock data automatically

### Voice Input Not Working

- Ensure browser supports MediaRecorder API (Chrome, Firefox, Edge)
- Check microphone permissions in browser
- Verify HTTPS connection (required for microphone access)
- Try text input as fallback

### Scheme Matching Not Working

- Verify user profile is complete (age, state, income)
- Check backend logs for eligibility matching errors
- Ensure OpenSearch domain is running
- Verify scheme data is indexed

## 📊 Performance

- Initial load: < 2s
- Voice transcription: 2-5s
- Scheme matching: 1-3s
- TTS generation: 1-2s
- Conversation response: 2-4s

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- AWS for serverless infrastructure
- Anthropic for Claude 3.5 Sonnet
- Bhashini for Indian language support
- Government of India for scheme data
- AI for Bharat Hackathon 2026

## 📞 Support

For issues and questions:

- Open an issue on GitHub
- Contact: [your-email@example.com]
- Documentation: [link-to-docs]

---

Built with ❤️ for AI for Bharat Hackathon 2026
