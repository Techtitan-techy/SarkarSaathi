import React, { useState, useEffect } from "react";
import VoiceInput from "./components/VoiceInput.jsx";
import SchemeList from "./components/SchemeList.jsx";
import ChatInterface from "./components/ChatInterface.jsx";
import {
  sendConversationMessage,
  matchSchemes as apiMatchSchemes,
  checkBackendHealth,
  getSessionId,
  clearSession,
} from "./services/apiService";
import {
  extractUserInfo,
  generateResponse,
  detectLanguage,
  matchSchemes as mockMatchSchemes,
  mockSchemes,
} from "./services/schemeService";

function App() {
  const [schemes, setSchemes] = useState([]);
  const [allSchemes, setAllSchemes] = useState(mockSchemes);
  const [messages, setMessages] = useState([]);
  const [isListening, setIsListening] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [backendAvailable, setBackendAvailable] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [showAllSchemes, setShowAllSchemes] = useState(false);
  const [userInfo, setUserInfo] = useState({
    age: null,
    state: null,
    income: null,
    occupation: null,
  });

  // Check backend health on mount
  useEffect(() => {
    const checkBackend = async () => {
      const isAvailable = await checkBackendHealth();
      setBackendAvailable(isAvailable);

      if (!isAvailable) {
        console.log("Backend unavailable, using mock data");
        // Add welcome message
        setMessages([
          {
            type: "assistant",
            text: "नमस्ते! मैं SarkariSaathi हूं। मैं आपको सरकारी योजनाओं के बारे में जानकारी देने में मदद कर सकता हूं। कृपया अपनी उम्र, राज्य और आय बताएं।\n\nHello! I am SarkariSaathi. I can help you find information about government schemes. Please tell me your age, state, and income.",
            timestamp: new Date().toISOString(),
          },
        ]);
      }
    };

    checkBackend();

    // Get or create session ID
    const sid = getSessionId();
    setSessionId(sid);
    console.log("Session ID:", sid);
  }, []);

  const handleVoiceInput = async (transcript) => {
    // Add user message
    setMessages((prev) => [
      ...prev,
      {
        type: "user",
        text: transcript,
        timestamp: new Date().toISOString(),
      },
    ]);

    setIsLoading(true);

    try {
      // Extract user information
      const extractedInfo = extractUserInfo(transcript);
      const updatedUserInfo = { ...userInfo, ...extractedInfo };
      setUserInfo(updatedUserInfo);

      // Detect language
      const language = detectLanguage(transcript);

      if (backendAvailable) {
        // Use backend API with conversation manager
        try {
          const response = await sendConversationMessage(
            transcript,
            sessionId,
            language,
            updatedUserInfo,
          );

          // Add assistant response
          setMessages((prev) => [
            ...prev,
            {
              type: "assistant",
              text:
                response.response ||
                response.message ||
                "I'm processing your request...",
              timestamp: new Date().toISOString(),
            },
          ]);

          // Update context if provided
          if (response.context) {
            const contextUserProfile = response.context.userProfile || {};
            setUserInfo((prev) => ({ ...prev, ...contextUserProfile }));
          }

          // If user profile is complete, fetch matching schemes
          if (updatedUserInfo.age && updatedUserInfo.income) {
            const schemesResult = await apiMatchSchemes(updatedUserInfo);
            if (schemesResult.schemes && schemesResult.schemes.length > 0) {
              setSchemes(schemesResult.schemes);
            }
          }
        } catch (apiError) {
          console.error("API error, falling back to mock:", apiError);
          // Fall back to mock data
          useMockResponse(transcript, updatedUserInfo, language);
        }
      } else {
        // Use mock data
        useMockResponse(transcript, updatedUserInfo, language);
      }
    } catch (error) {
      console.error("Error handling voice input:", error);
      setMessages((prev) => [
        ...prev,
        {
          type: "assistant",
          text: "क्षमा करें, कुछ गलत हो गया। कृपया पुनः प्रयास करें। / Sorry, something went wrong. Please try again.",
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const useMockResponse = (transcript, updatedUserInfo, language) => {
    // Generate intelligent response using mock service
    setTimeout(() => {
      const response = generateResponse(transcript, updatedUserInfo, language);

      setMessages((prev) => [
        ...prev,
        {
          type: "assistant",
          text: response,
          timestamp: new Date().toISOString(),
        },
      ]);

      // If user has provided enough info (age OR income), show matching schemes
      if (
        updatedUserInfo.age ||
        updatedUserInfo.income ||
        updatedUserInfo.occupation
      ) {
        const matchingSchemes = mockMatchSchemes(updatedUserInfo);
        if (matchingSchemes.length > 0) {
          setSchemes(matchingSchemes);
        }
      }
    }, 1000);
  };

  const styles = {
    app: {
      minHeight: "100vh",
      display: "flex",
      flexDirection: "column",
      background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
    },
    header: {
      background: "rgba(255, 255, 255, 0.98)",
      padding: "2rem",
      textAlign: "center",
      boxShadow: "0 4px 20px rgba(0, 0, 0, 0.15)",
      borderBottom: "3px solid #667eea",
    },
    title: {
      background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
      WebkitBackgroundClip: "text",
      WebkitTextFillColor: "transparent",
      backgroundClip: "text",
      fontSize: "3rem",
      marginBottom: "0.5rem",
      fontWeight: "bold",
    },
    subtitle: {
      color: "#666",
      fontSize: "1.3rem",
      marginBottom: "1rem",
    },
    headerActions: {
      display: "flex",
      justifyContent: "center",
      gap: "1rem",
      flexWrap: "wrap",
      marginTop: "1rem",
    },
    statusBadge: {
      display: "inline-block",
      padding: "0.5rem 1.5rem",
      borderRadius: "25px",
      fontSize: "0.9rem",
      background: backendAvailable
        ? "linear-gradient(135deg, #11998e 0%, #38ef7d 100%)"
        : "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
      color: "white",
      fontWeight: 600,
      boxShadow: "0 3px 10px rgba(0,0,0,0.2)",
    },
    browseBtn: {
      padding: "0.5rem 1.5rem",
      borderRadius: "25px",
      fontSize: "0.9rem",
      background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
      color: "white",
      border: "none",
      fontWeight: 600,
      cursor: "pointer",
      boxShadow: "0 3px 10px rgba(0,0,0,0.2)",
      transition: "all 0.3s ease",
    },
    main: {
      flex: 1,
      padding: "2rem",
      display: "flex",
      justifyContent: "center",
      alignItems: "flex-start",
    },
    container: {
      maxWidth: "1200px",
      width: "100%",
    },
    loadingIndicator: {
      textAlign: "center",
      padding: "1rem",
      color: "white",
      fontWeight: 600,
      fontSize: "1.1rem",
      textShadow: "2px 2px 4px rgba(0,0,0,0.3)",
    },
    footer: {
      background: "rgba(0, 0, 0, 0.3)",
      color: "white",
      textAlign: "center",
      padding: "1.5rem",
      borderTop: "2px solid rgba(255,255,255,0.1)",
    },
    statsBar: {
      display: "flex",
      justifyContent: "center",
      gap: "2rem",
      marginTop: "1rem",
      flexWrap: "wrap",
    },
    stat: {
      textAlign: "center",
    },
    statNumber: {
      fontSize: "1.5rem",
      fontWeight: "bold",
      color: "#667eea",
      display: "block",
    },
    statLabel: {
      fontSize: "0.85rem",
      color: "#999",
    },
  };

  return (
    <div style={styles.app}>
      <header style={styles.header}>
        <h1 style={styles.title}>🇮🇳 SarkariSaathi</h1>
        <p style={styles.subtitle}>
          सरकारी योजना नेविगेटर | Your Government Scheme Navigator
        </p>

        <div style={styles.headerActions}>
          <div style={styles.statusBadge}>
            {backendAvailable
              ? "🟢 Connected to Backend"
              : "🟡 Using Mock Data"}
          </div>
          <button
            style={styles.browseBtn}
            onClick={() => {
              setShowAllSchemes(!showAllSchemes);
              if (!showAllSchemes) {
                setSchemes(allSchemes);
              } else {
                setSchemes([]);
              }
            }}
            onMouseEnter={(e) => {
              e.target.style.transform = "translateY(-2px)";
              e.target.style.boxShadow = "0 5px 15px rgba(102, 126, 234, 0.4)";
            }}
            onMouseLeave={(e) => {
              e.target.style.transform = "translateY(0)";
              e.target.style.boxShadow = "0 3px 10px rgba(0,0,0,0.2)";
            }}
          >
            {showAllSchemes ? "🔍 Find My Schemes" : "📚 Browse All Schemes"}
          </button>
          <button
            style={{
              ...styles.browseBtn,
              background: "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
            }}
            onClick={() => {
              clearSession();
              setSessionId(getSessionId());
              setMessages([]);
              setSchemes([]);
              setUserInfo({
                age: null,
                state: null,
                income: null,
                occupation: null,
              });
              setShowAllSchemes(false);
              window.location.reload();
            }}
            onMouseEnter={(e) => {
              e.target.style.transform = "translateY(-2px)";
              e.target.style.boxShadow = "0 5px 15px rgba(245, 87, 108, 0.4)";
            }}
            onMouseLeave={(e) => {
              e.target.style.transform = "translateY(0)";
              e.target.style.boxShadow = "0 3px 10px rgba(0,0,0,0.2)";
            }}
          >
            🔄 New Session
          </button>
        </div>

        <div style={styles.statsBar}>
          <div style={styles.stat}>
            <span style={styles.statNumber}>{allSchemes.length}</span>
            <span style={styles.statLabel}>Total Schemes</span>
          </div>
          <div style={styles.stat}>
            <span style={styles.statNumber}>
              {new Set(allSchemes.map((s) => s.category)).size}
            </span>
            <span style={styles.statLabel}>Categories</span>
          </div>
          <div style={styles.stat}>
            <span style={styles.statNumber}>
              {allSchemes.filter((s) => s.type === "Central").length}
            </span>
            <span style={styles.statLabel}>Central Schemes</span>
          </div>
          <div style={styles.stat}>
            <span style={styles.statNumber}>29</span>
            <span style={styles.statLabel}>States Covered</span>
          </div>
        </div>
      </header>

      <main style={styles.main}>
        <div style={styles.container}>
          {!showAllSchemes && (
            <>
              <VoiceInput
                onVoiceInput={handleVoiceInput}
                isListening={isListening}
                setIsListening={setIsListening}
              />

              {isLoading && (
                <div style={styles.loadingIndicator}>
                  <p>⏳ Processing your request...</p>
                </div>
              )}

              <ChatInterface messages={messages} />
            </>
          )}

          {schemes.length > 0 && <SchemeList schemes={schemes} />}
        </div>
      </main>

      <footer style={styles.footer}>
        <p style={{ fontSize: "1.1rem", marginBottom: "0.5rem" }}>
          Built for AI for Bharat Hackathon 2026 🚀
        </p>
        <p style={{ fontSize: "0.9rem", opacity: 0.9 }}>
          {backendAvailable
            ? "Powered by AWS Lambda, Bedrock Claude 3.5 Sonnet, OpenSearch, DynamoDB, Transcribe, Polly & Bhashini"
            : "Demo Mode - Deploy backend to enable full AI features"}
        </p>
        <p style={{ fontSize: "0.85rem", marginTop: "0.5rem", opacity: 0.8 }}>
          Real 2025 Government Scheme Data | 10+ Schemes | 29 States | 10+
          Languages
        </p>
        <p style={{ fontSize: "0.8rem", marginTop: "0.5rem", opacity: 0.7 }}>
          Session ID:{" "}
          {sessionId ? sessionId.substring(0, 20) + "..." : "Loading..."}
        </p>
      </footer>
    </div>
  );
}

export default App;
