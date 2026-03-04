# Lambda Functions - Implementation Summary

## Overview

Three Python Lambda functions have been created to handle the backend logic for SarkariSaathi:

1. **Voice Handler** - Audio processing, transcription, and text-to-speech
2. **Chat Handler** - Conversation management and AI responses
3. **Scheme Handler** - Scheme matching and eligibility checking

---

## 1. Voice Handler (`lambda/voice_handler.py`)

### Purpose

Handles all voice-related operations including audio upload, transcription, and text-to-speech synthesis.

### Endpoints

#### POST /voice/upload

Upload audio file to S3 for processing.

**Request:**

```json
{
  "audio": "base64_encoded_audio_data",
  "language": "en-IN"
}
```

**Response:**

```json
{
  "audioId": "audio_abc123",
  "filename": "uploads/audio_abc123.wav",
  "language": "en-IN"
}
```

#### POST /voice/transcribe

Transcribe audio to text using Amazon Transcribe.

**Request:**

```json
{
  "audioId": "audio_abc123",
  "language": "en-IN"
}
```

**Response:**

```json
{
  "transcript": "मुझे किसान योजना के बारे में बताएं",
  "language": "hi-IN",
  "confidence": 0.95
}
```

#### POST /voice/synthesize

Convert text to speech using Amazon Polly.

**Request:**

```json
{
  "text": "आप PM-KISAN योजना के लिए पात्र हैं",
  "language": "hi-IN"
}
```

**Response:**

```json
{
  "audioUrl": "https://s3.amazonaws.com/...",
  "audioId": "tts_xyz789",
  "language": "hi-IN"
}
```

### AWS Services Used

- Amazon S3 (audio storage)
- Amazon Transcribe (speech-to-text)
- Amazon Polly (text-to-speech)

---

## 2. Chat Handler (`lambda/chat_handler.py`)

### Purpose

Manages chat sessions and generates AI responses using Amazon Bedrock (Claude 3.5 Sonnet).

### Endpoints

#### POST /chat/session

Create a new chat session.

**Request:**

```json
{
  "userId": "user123",
  "language": "hi"
}
```

**Response:**

```json
{
  "sessionId": "session_abc123",
  "userId": "user123",
  "language": "hi"
}
```

#### GET /chat/session/{sessionId}

Get session history.

**Response:**

```json
{
  "sessionId": "session_abc123",
  "userId": "user123",
  "language": "hi",
  "messages": [
    {
      "role": "user",
      "content": "मेरी उम्र 35 है",
      "timestamp": "2026-02-28T10:00:00Z"
    },
    {
      "role": "assistant",
      "content": "धन्यवाद। आपकी आय कितनी है?",
      "timestamp": "2026-02-28T10:00:01Z"
    }
  ]
}
```

#### POST /chat/message

Send a message and get AI response.

**Request:**

```json
{
  "sessionId": "session_abc123",
  "message": "मैं किसान हूं और मेरी आय 2 लाख है",
  "userInfo": {
    "age": 35,
    "occupation": "farmer",
    "income": 200000
  },
  "language": "hi"
}
```

**Response:**

```json
{
  "response": "बढ़िया! आप PM-KISAN और किसान क्रेडिट कार्ड योजना के लिए पात्र हैं...",
  "sessionId": "session_abc123",
  "timestamp": "2026-02-28T10:00:02Z"
}
```

### Features

- Session management with DynamoDB
- Conversation context retention
- Bilingual system prompts (English/Hindi)
- Amazon Bedrock (Claude 3.5 Sonnet) integration
- Automatic language detection

### AWS Services Used

- Amazon DynamoDB (session storage)
- Amazon Bedrock (AI responses)

---

## 3. Scheme Handler (`lambda/scheme_handler.py`)

### Purpose

Handles scheme operations including listing, filtering, and eligibility matching.

### Endpoints

#### GET /schemes

Get all available schemes.

**Query Parameters:**

- `category` (optional) - Filter by category (Agriculture, Healthcare, etc.)
- `state` (optional) - Filter by state

**Response:**

```json
{
  "schemes": [
    {
      "id": "pm-kisan",
      "name": "PM-KISAN",
      "nameHi": "प्रधानमंत्री किसान सम्मान निधि",
      "category": "Agriculture",
      "description": "Financial support of ₹6000 per year",
      "descriptionHi": "किसान परिवारों को प्रति वर्ष ₹6000",
      "benefits": ["₹6000 per year", "Direct bank transfer"],
      "benefitsHi": ["प्रति वर्ष ₹6000", "सीधे बैंक खाते में"],
      "eligibility": {
        "minAge": 18,
        "maxAge": 100,
        "minIncome": 0,
        "maxIncome": 500000,
        "states": ["all"],
        "occupation": ["farmer", "agriculture"]
      }
    }
  ],
  "count": 4
}
```

#### GET /schemes/{schemeId}

Get specific scheme by ID.

**Response:**

```json
{
  "id": "pm-kisan",
  "name": "PM-KISAN",
  ...
}
```

#### POST /schemes/match

Match schemes based on user profile.

**Request:**

```json
{
  "userProfile": {
    "age": 35,
    "income": 200000,
    "state": "punjab",
    "occupation": "farmer"
  }
}
```

**Response:**

```json
{
  "schemes": [
    {
      "id": "pm-kisan",
      "name": "PM-KISAN",
      "matchScore": 100,
      ...
    },
    {
      "id": "kisan-credit-card",
      "name": "Kisan Credit Card",
      "matchScore": 100,
      ...
    }
  ],
  "count": 2,
  "userProfile": {
    "age": 35,
    "income": 200000,
    "state": "punjab",
    "occupation": "farmer"
  }
}
```

### Matching Algorithm

The eligibility matching uses a scoring system:

- Age match: +25 points
- Income match: +25 points
- State match: +25 points
- Occupation match: +25 points
- Maximum score: 100 points

Schemes are sorted by match score (highest first).

### AWS Services Used

- Amazon DynamoDB (scheme storage - future)
- Amazon OpenSearch (semantic search - future)

---

## Frontend Integration

### API Service (`frontend/src/services/apiService.js`)

A complete API service layer has been created to connect the frontend to these Lambda functions:

```javascript
import {
  sendMessage,
  matchSchemes,
  synthesizeSpeech,
} from "./services/apiService";

// Send a chat message
const response = await sendMessage(
  "मुझे किसान योजना बताएं",
  sessionId,
  { age: 35, occupation: "farmer" },
  "hi",
);

// Match schemes
const matches = await matchSchemes({
  age: 35,
  income: 200000,
  occupation: "farmer",
});

// Convert text to speech
const audio = await synthesizeSpeech("आप PM-KISAN के लिए पात्र हैं", "hi-IN");
```

---

## Environment Variables

Each Lambda function requires these environment variables:

### Voice Handler

- `AUDIO_BUCKET` - S3 bucket for audio files
- `AWS_REGION` - AWS region (default: ap-south-1)

### Chat Handler

- `SESSIONS_TABLE` - DynamoDB table for sessions
- `AWS_REGION` - AWS region

### Scheme Handler

- `SCHEMES_TABLE` - DynamoDB table for schemes
- `AWS_REGION` - AWS region

---

## Deployment

### Prerequisites

1. AWS account with appropriate permissions
2. AWS CLI configured
3. Python 3.11 installed
4. AWS CDK installed

### Steps

1. **Install Python dependencies:**

```bash
cd lambda
pip install -r requirements.txt
```

2. **Deploy infrastructure with CDK:**

```bash
npm install
cdk bootstrap
cdk deploy
```

3. **Update frontend API URL:**

```bash
# In frontend/.env
REACT_APP_API_URL=https://your-api-gateway-url
```

4. **Test endpoints:**

```bash
# Test voice upload
curl -X POST https://your-api/voice/upload \
  -H "Content-Type: application/json" \
  -d '{"audio": "base64data", "language": "en-IN"}'
```

---

## Testing

### Local Testing

You can test Lambda functions locally using the AWS SAM CLI or by creating test scripts:

```python
# test_voice_handler.py
from lambda.voice_handler import lambda_handler

event = {
    'httpMethod': 'POST',
    'path': '/voice/upload',
    'body': '{"audio": "...", "language": "en-IN"}'
}

response = lambda_handler(event, None)
print(response)
```

### Integration Testing

Once deployed, test the full flow:

1. Upload audio → Get audio ID
2. Transcribe audio → Get transcript
3. Send message to chat → Get AI response
4. Match schemes → Get eligible schemes
5. Synthesize response → Get audio URL

---

## Current Status

✅ All three Lambda handlers implemented
✅ Error handling and logging
✅ Bilingual support (English/Hindi)
✅ Frontend API service layer
⏳ AWS infrastructure deployment (CDK)
⏳ DynamoDB tables creation
⏳ S3 buckets setup
⏳ API Gateway configuration

---

## Next Steps

1. Create AWS CDK stack for infrastructure
2. Deploy Lambda functions to AWS
3. Set up DynamoDB tables
4. Configure S3 buckets
5. Create API Gateway endpoints
6. Update frontend with deployed API URL
7. Test end-to-end flow
8. Add monitoring and logging

---

**Last Updated:** February 28, 2026
