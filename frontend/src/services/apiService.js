/**
 * API Service for connecting to backend Lambda functions
 * Integrates with AWS API Gateway, CloudFront, and Lambda functions
 *
 * Updated: 2026-03-03
 * - Integrated with conversation_manager.py for state-based conversations
 * - Added voice processing endpoints (upload, transcribe, synthesize)
 * - Enhanced scheme matching with eligibility scoring
 * - Added session management and context retention
 */

// API Gateway endpoint (will be set after deployment)
const API_BASE_URL =
  process.env.REACT_APP_API_URL ||
  process.env.REACT_APP_CLOUDFRONT_URL ||
  "http://localhost:3001";
const API_KEY = process.env.REACT_APP_API_KEY || "";
const USE_MOCK_DATA = process.env.REACT_APP_USE_MOCK_DATA === "true";

// Common headers for API requests
const getHeaders = () => ({
  "Content-Type": "application/json",
  ...(API_KEY && { "X-Api-Key": API_KEY }),
});

// Session storage key
const SESSION_STORAGE_KEY = "sarkari_saathi_session_id";

/**
 * Get or create session ID
 */
export const getSessionId = () => {
  let sessionId = sessionStorage.getItem(SESSION_STORAGE_KEY);
  if (!sessionId) {
    sessionId = `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    sessionStorage.setItem(SESSION_STORAGE_KEY, sessionId);
  }
  return sessionId;
};

/**
 * Clear session ID (for logout or reset)
 */
export const clearSession = () => {
  sessionStorage.removeItem(SESSION_STORAGE_KEY);
};

/**
 * Send a message through the conversation manager
 * Uses state machine for multi-turn conversations with context retention
 */
export const sendConversationMessage = async (
  message,
  sessionId = null,
  language = "en",
  userProfile = null,
) => {
  try {
    if (!sessionId) {
      sessionId = getSessionId();
    }

    const response = await fetch(`${API_BASE_URL}/conversation`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({
        action: "determineState",
        sessionId: sessionId,
        userMessage: message,
        language: language,
        context: userProfile ? { userProfile } : {},
      }),
    });

    if (!response.ok) {
      throw new Error("Failed to send conversation message");
    }

    return await response.json();
  } catch (error) {
    console.error("Send conversation message error:", error);
    throw error;
  }
};

/**
 * Upload audio file for transcription
 * Endpoint: POST /voice/upload
 */
export const uploadAudio = async (audioBlob, language = "en-IN") => {
  try {
    // Convert blob to base64
    const reader = new FileReader();
    const base64Audio = await new Promise((resolve, reject) => {
      reader.onloadend = () => resolve(reader.result.split(",")[1]);
      reader.onerror = reject;
      reader.readAsDataURL(audioBlob);
    });

    const response = await fetch(`${API_BASE_URL}/voice/upload`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({
        audio: base64Audio,
        language: language,
      }),
    });

    if (!response.ok) {
      throw new Error("Failed to upload audio");
    }

    return await response.json();
  } catch (error) {
    console.error("Upload audio error:", error);
    throw error;
  }
};

/**
 * Transcribe audio to text
 * Endpoint: POST /voice/transcribe
 */
export const transcribeAudio = async (audioId, language = "en-IN") => {
  try {
    const response = await fetch(`${API_BASE_URL}/voice/transcribe`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({
        audioId: audioId,
        language: language,
      }),
    });

    if (!response.ok) {
      throw new Error("Failed to transcribe audio");
    }

    return await response.json();
  } catch (error) {
    console.error("Transcribe audio error:", error);
    throw error;
  }
};

/**
 * Convert text to speech
 * Endpoint: POST /voice/synthesize
 */
export const synthesizeSpeech = async (text, language = "en-IN") => {
  try {
    const response = await fetch(`${API_BASE_URL}/voice/synthesize`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({
        text: text,
        language: language,
      }),
    });

    if (!response.ok) {
      throw new Error("Failed to synthesize speech");
    }

    return await response.json();
  } catch (error) {
    console.error("Synthesize speech error:", error);
    throw error;
  }
};

/**
 * Create a new chat session
 * Endpoint: POST /chat/session
 */
export const createSession = async (userId = "anonymous", language = "en") => {
  try {
    const response = await fetch(`${API_BASE_URL}/chat/session`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({
        userId: userId,
        language: language,
      }),
    });

    if (!response.ok) {
      throw new Error("Failed to create session");
    }

    return await response.json();
  } catch (error) {
    console.error("Create session error:", error);
    throw error;
  }
};

/**
 * Send a chat message and get AI response
 * Endpoint: POST /chat/message
 */
export const sendMessage = async (
  message,
  sessionId = null,
  userInfo = {},
  language = "en",
) => {
  try {
    if (!sessionId) {
      sessionId = getSessionId();
    }

    const response = await fetch(`${API_BASE_URL}/chat/message`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({
        message: message,
        sessionId: sessionId,
        userInfo: userInfo,
        language: language,
      }),
    });

    if (!response.ok) {
      throw new Error("Failed to send message");
    }

    return await response.json();
  } catch (error) {
    console.error("Send message error:", error);
    throw error;
  }
};

/**
 * Get all schemes
 * Endpoint: GET /schemes
 */
export const getAllSchemes = async (category = null, state = null) => {
  try {
    const params = new URLSearchParams();
    if (category) params.append("category", category);
    if (state) params.append("state", state);

    const url = `${API_BASE_URL}/schemes${params.toString() ? "?" + params.toString() : ""}`;

    const response = await fetch(url, {
      method: "GET",
      headers: getHeaders(),
    });

    if (!response.ok) {
      throw new Error("Failed to get schemes");
    }

    return await response.json();
  } catch (error) {
    console.error("Get schemes error:", error);
    throw error;
  }
};

/**
 * Get specific scheme by ID
 * Endpoint: GET /schemes/{schemeId}
 */
export const getScheme = async (schemeId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/schemes/${schemeId}`, {
      method: "GET",
      headers: getHeaders(),
    });

    if (!response.ok) {
      throw new Error("Failed to get scheme");
    }

    return await response.json();
  } catch (error) {
    console.error("Get scheme error:", error);
    throw error;
  }
};

/**
 * Match schemes based on user profile using eligibility engine
 * Endpoint: POST /schemes/match
 *
 * Returns schemes with eligibility scores based on:
 * - Age matching
 * - Income matching
 * - State/location matching
 * - Occupation matching
 * - Category matching (General, OBC, SC, ST, etc.)
 */
export const matchSchemes = async (userProfile) => {
  try {
    const response = await fetch(`${API_BASE_URL}/schemes/match`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({
        userProfile: userProfile,
      }),
    });

    if (!response.ok) {
      throw new Error("Failed to match schemes");
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Match schemes error:", error);

    // Fallback to mock data if backend is unavailable
    if (USE_MOCK_DATA) {
      const { matchSchemes: mockMatch } = await import("./schemeService");
      return {
        schemes: mockMatch(userProfile),
        count: mockMatch(userProfile).length,
      };
    }

    throw error;
  }
};

/**
 * Check if backend API is available
 * Endpoint: GET /health
 */
export const checkBackendHealth = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/health`, {
      method: "GET",
      timeout: 5000,
    });
    return response.ok;
  } catch (error) {
    console.log("Backend health check failed:", error.message);
    return false;
  }
};

/**
 * Get session history
 * Endpoint: GET /chat/session/{sessionId}
 */
export const getSessionHistory = async (sessionId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/chat/session/${sessionId}`, {
      method: "GET",
      headers: getHeaders(),
    });

    if (!response.ok) {
      throw new Error("Failed to get session history");
    }

    return await response.json();
  } catch (error) {
    console.error("Get session history error:", error);
    throw error;
  }
};
