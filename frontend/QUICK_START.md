# SarkariSaathi Frontend - Quick Start Guide

## 🚀 5-Minute Setup

### Prerequisites

```bash
node --version  # v16+ required
npm --version   # v8+ required
```

### Installation

```bash
# Clone and install
git clone <repository-url>
cd frontend
npm install
```

### Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env (use mock data for local development)
REACT_APP_USE_MOCK_DATA=true
REACT_APP_ENABLE_VOICE=true
```

### Run

```bash
npm start
# Open http://localhost:3000
```

## 📡 API Endpoints Quick Reference

### Conversation

```javascript
POST /conversation
{
  "action": "determineState",
  "sessionId": "session-123",
  "userMessage": "I am 30 years old",
  "language": "en",
  "context": { "userProfile": {...} }
}
```

### Voice Processing

```javascript
// Upload
POST /voice/upload
{ "audio": "base64...", "language": "en-IN" }

// Transcribe
POST /voice/transcribe
{ "audioId": "audio-123", "language": "en-IN" }

// Synthesize
POST /voice/synthesize
{ "text": "Hello", "language": "en-IN" }
```

### Schemes

```javascript
// Match schemes
POST /schemes/match
{ "userProfile": { "age": 30, "income": 200000, "state": "Karnataka" } }

// Get all schemes
GET /schemes?category=Agriculture&state=Karnataka

// Get specific scheme
GET /schemes/pm-kisan
```

## 🎨 Component Structure

```
src/
├── components/
│   ├── VoiceInput.jsx      # Voice recording UI
│   ├── ChatInterface.jsx   # Message display
│   ├── SchemeList.jsx      # Scheme cards
│   ├── SchemeCard.jsx      # Individual scheme
│   └── FilterPanel.jsx     # Scheme filters
├── services/
│   ├── apiService.js       # Backend API calls
│   └── schemeService.js    # Mock data & helpers
└── App.jsx                 # Main app component
```

## 🔧 Common Tasks

### Add New API Endpoint

```javascript
// In src/services/apiService.js
export const newEndpoint = async (params) => {
  const response = await fetch(`${API_BASE_URL}/new-endpoint`, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify(params),
  });
  return await response.json();
};
```

### Add New Component

```javascript
// src/components/NewComponent.jsx
import React from "react";

function NewComponent({ prop1, prop2 }) {
  return <div>{/* Your component */}</div>;
}

export default NewComponent;
```

### Update Styling

```javascript
// Inline styles in component
const styles = {
  container: {
    padding: "2rem",
    background: "white",
  },
};

<div style={styles.container}>Content</div>;
```

## 🐛 Debugging

### Check Backend Connection

```javascript
// In browser console
fetch("https://your-api-url/health")
  .then((r) => r.json())
  .then(console.log);
```

### View Session Data

```javascript
// In browser console
sessionStorage.getItem("sarkari_saathi_session_id");
```

### Enable Verbose Logging

```javascript
// In src/services/apiService.js
console.log("API Request:", url, body);
console.log("API Response:", response);
```

## 📦 Build & Deploy

### Development Build

```bash
npm start
```

### Production Build

```bash
npm run build
# Output in build/ directory
```

### Deploy to S3

```bash
aws s3 sync build/ s3://your-bucket --delete
aws cloudfront create-invalidation --distribution-id ID --paths "/*"
```

## 🧪 Testing

### Run Tests

```bash
npm test
```

### Test Specific File

```bash
npm test -- VoiceInput.test.js
```

### Coverage Report

```bash
npm test -- --coverage
```

## 🔑 Environment Variables

| Variable                     | Description                | Example                                                 |
| ---------------------------- | -------------------------- | ------------------------------------------------------- |
| `REACT_APP_API_URL`          | Backend API Gateway URL    | `https://abc.execute-api.ap-south-1.amazonaws.com/prod` |
| `REACT_APP_API_KEY`          | API Key for authentication | `your-api-key`                                          |
| `REACT_APP_USE_MOCK_DATA`    | Use mock data (dev mode)   | `true` or `false`                                       |
| `REACT_APP_ENABLE_VOICE`     | Enable voice input         | `true` or `false`                                       |
| `REACT_APP_DEFAULT_LANGUAGE` | Default language           | `hi-IN` or `en-IN`                                      |

## 🎯 Key Features

### Session Management

```javascript
import { getSessionId, clearSession } from "./services/apiService";

// Get current session
const sessionId = getSessionId();

// Reset session
clearSession();
```

### Voice Input

```javascript
// Handled by VoiceInput component
<VoiceInput
  onVoiceInput={handleVoiceInput}
  isListening={isListening}
  setIsListening={setIsListening}
/>
```

### Scheme Matching

```javascript
import { matchSchemes } from "./services/apiService";

const schemes = await matchSchemes({
  age: 30,
  income: 200000,
  state: "Karnataka",
  occupation: "farmer",
});
```

## 🚨 Troubleshooting

### Issue: Backend not connecting

```bash
# Check .env file
cat .env | grep REACT_APP_API_URL

# Test backend health
curl https://your-api-url/health
```

### Issue: Voice not working

- Check browser supports MediaRecorder API
- Verify HTTPS connection (required for microphone)
- Check microphone permissions

### Issue: Build fails

```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
npm run build
```

## 📚 Resources

- [Full Documentation](./README.md)
- [Deployment Guide](./DEPLOYMENT.md)
- [API Reference](./README.md#api-endpoints)
- [Updates Log](./UPDATES.md)

## 💡 Tips

1. **Use Mock Data for Development**
   - Set `REACT_APP_USE_MOCK_DATA=true` in `.env`
   - No backend required for frontend development

2. **Test Voice Input**
   - Use Chrome or Firefox (best support)
   - Requires HTTPS in production
   - Works on localhost without HTTPS

3. **Debug API Calls**
   - Open browser DevTools → Network tab
   - Filter by "XHR" to see API requests
   - Check request/response payloads

4. **Optimize Bundle Size**
   - Use code splitting for large components
   - Lazy load routes
   - Compress images before adding

5. **Mobile Testing**
   - Use Chrome DevTools device emulation
   - Test on actual devices
   - Check touch interactions

## 🤝 Contributing

1. Create feature branch
2. Make changes
3. Test locally
4. Submit pull request

## 📞 Quick Help

- **Backend Issues**: Check `DEPLOYMENT.md`
- **API Errors**: Check browser console
- **Build Errors**: Clear cache and reinstall
- **Voice Issues**: Check browser compatibility

---

**Need more help?** Check the full [README.md](./README.md) or [DEPLOYMENT.md](./DEPLOYMENT.md)
