import React, { useState, useEffect } from "react";

const VoiceInput = ({ onVoiceInput, isListening, setIsListening }) => {
  const [transcript, setTranscript] = useState("");
  const [recognition, setRecognition] = useState(null);
  const [useTextInput, setUseTextInput] = useState(false);
  const [textValue, setTextValue] = useState("");

  useEffect(() => {
    if ("webkitSpeechRecognition" in window || "SpeechRecognition" in window) {
      const SpeechRecognition =
        window.SpeechRecognition || window.webkitSpeechRecognition;
      const recognitionInstance = new SpeechRecognition();

      recognitionInstance.continuous = true;
      recognitionInstance.interimResults = true;
      recognitionInstance.lang = "hi-IN";
      recognitionInstance.maxAlternatives = 1;

      recognitionInstance.onstart = () => {
        console.log("Speech recognition started");
        setIsListening(true);
      };

      recognitionInstance.onresult = (event) => {
        let interimTranscript = "";
        let finalTranscript = "";

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript + " ";
          } else {
            interimTranscript += transcript;
          }
        }

        setTranscript(interimTranscript);

        if (finalTranscript) {
          console.log("Final transcript:", finalTranscript);
          onVoiceInput(finalTranscript.trim());
        }
      };

      recognitionInstance.onerror = (event) => {
        console.error("Speech recognition error:", event.error);
        if (event.error === "network") {
          alert(
            "Network error: Web Speech API requires internet connection. Switching to text input mode.",
          );
          setUseTextInput(true);
          setIsListening(false);
        } else if (event.error === "no-speech") {
          console.log("No speech detected, continuing...");
        } else if (event.error === "aborted") {
          console.log("Speech recognition aborted");
          setIsListening(false);
        } else {
          alert(
            `Speech recognition error: ${event.error}. Try text input instead.`,
          );
          setIsListening(false);
        }
      };

      recognitionInstance.onend = () => {
        console.log("Speech recognition ended");
        setIsListening(false);
        setTranscript("");
      };

      setRecognition(recognitionInstance);
    } else {
      // Browser doesn't support speech recognition
      setUseTextInput(true);
    }
  }, [onVoiceInput, setIsListening]);

  const toggleListening = () => {
    if (!recognition) {
      alert(
        "Speech recognition is not supported in your browser. Please use text input below.",
      );
      setUseTextInput(true);
      return;
    }

    if (isListening) {
      console.log("Stopping speech recognition");
      recognition.stop();
      setIsListening(false);
    } else {
      console.log("Starting speech recognition");
      try {
        recognition.start();
        setIsListening(true);
      } catch (error) {
        console.error("Error starting recognition:", error);
        alert("Could not start speech recognition. Using text input instead.");
        setUseTextInput(true);
      }
    }
  };

  const handleTextSubmit = (e) => {
    e.preventDefault();
    if (textValue.trim()) {
      onVoiceInput(textValue.trim());
      setTextValue("");
    }
  };

  const changeLanguage = (lang) => {
    if (recognition) {
      recognition.lang = lang;
    }
  };

  const styles = {
    container: {
      background: "white",
      borderRadius: "20px",
      padding: "2rem",
      marginBottom: "2rem",
      boxShadow: "0 10px 30px rgba(0, 0, 0, 0.2)",
    },
    controls: {
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      gap: "1rem",
    },
    micButton: {
      width: "100px",
      height: "100px",
      borderRadius: "50%",
      border: "none",
      background: isListening
        ? "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)"
        : "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
      color: "white",
      fontSize: "3rem",
      cursor: "pointer",
      transition: "all 0.3s ease",
      boxShadow: isListening
        ? "0 5px 15px rgba(240, 147, 251, 0.4)"
        : "0 5px 15px rgba(102, 126, 234, 0.4)",
      animation: isListening ? "pulse 1.5s infinite" : "none",
    },
    micIcon: {
      display: "inline-block",
      animation: isListening ? "pulse-icon 1s infinite" : "none",
    },
    languageSelector: {
      padding: "0.75rem 1.5rem",
      borderRadius: "10px",
      border: "2px solid #667eea",
      fontSize: "1rem",
      background: "white",
      cursor: "pointer",
      transition: "all 0.3s ease",
    },
    listeningIndicator: {
      marginTop: "1.5rem",
      textAlign: "center",
      padding: "1rem",
      background: "rgba(240, 147, 251, 0.1)",
      borderRadius: "10px",
    },
    listeningText: {
      color: "#f5576c",
      fontWeight: 600,
      margin: "0.5rem 0",
    },
    interimTranscript: {
      color: "#666",
      fontStyle: "italic",
      marginTop: "0.5rem",
    },
    instructions: {
      marginTop: "1.5rem",
      textAlign: "center",
      color: "#666",
    },
    instructionText: {
      margin: "0.5rem 0",
      fontSize: "0.95rem",
    },
    textInputForm: {
      marginTop: "1.5rem",
      display: "flex",
      gap: "0.5rem",
    },
    textInput: {
      flex: 1,
      padding: "0.75rem 1rem",
      borderRadius: "10px",
      border: "2px solid #667eea",
      fontSize: "1rem",
      outline: "none",
    },
    sendButton: {
      padding: "0.75rem 1.5rem",
      borderRadius: "10px",
      border: "none",
      background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
      color: "white",
      fontSize: "1rem",
      fontWeight: 600,
      cursor: "pointer",
      transition: "all 0.3s ease",
    },
    switchButton: {
      marginTop: "1rem",
      padding: "0.5rem 1rem",
      borderRadius: "8px",
      border: "2px solid #667eea",
      background: "white",
      color: "#667eea",
      fontSize: "0.9rem",
      cursor: "pointer",
      transition: "all 0.3s ease",
    },
  };

  return (
    <div style={styles.container}>
      <style>{`
        @keyframes pulse {
          0%, 100% { box-shadow: 0 5px 15px rgba(240, 147, 251, 0.4); }
          50% { box-shadow: 0 5px 30px rgba(240, 147, 251, 0.8); }
        }
        @keyframes pulse-icon {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.1); }
        }
      `}</style>

      <div style={styles.controls}>
        {!useTextInput ? (
          <>
            <button
              style={styles.micButton}
              onClick={toggleListening}
              onMouseEnter={(e) => (e.target.style.transform = "scale(1.05)")}
              onMouseLeave={(e) => (e.target.style.transform = "scale(1)")}
              aria-label={isListening ? "Stop listening" : "Start listening"}
            >
              <span style={styles.micIcon}>🎤</span>
            </button>

            <select
              style={styles.languageSelector}
              onChange={(e) => changeLanguage(e.target.value)}
              defaultValue="hi-IN"
            >
              <option value="hi-IN">हिंदी (Hindi)</option>
              <option value="en-IN">English</option>
              <option value="ta-IN">தமிழ் (Tamil)</option>
              <option value="te-IN">తెలుగు (Telugu)</option>
              <option value="bn-IN">বাংলা (Bengali)</option>
              <option value="mr-IN">मराठी (Marathi)</option>
              <option value="gu-IN">ગુજરાતી (Gujarati)</option>
              <option value="kn-IN">ಕನ್ನಡ (Kannada)</option>
              <option value="ml-IN">മലയാളം (Malayalam)</option>
              <option value="pa-IN">ਪੰਜਾਬੀ (Punjabi)</option>
            </select>

            <button
              style={styles.switchButton}
              onClick={() => setUseTextInput(true)}
              onMouseEnter={(e) => {
                e.target.style.background = "#667eea";
                e.target.style.color = "white";
              }}
              onMouseLeave={(e) => {
                e.target.style.background = "white";
                e.target.style.color = "#667eea";
              }}
            >
              Switch to Text Input
            </button>
          </>
        ) : (
          <>
            <form style={styles.textInputForm} onSubmit={handleTextSubmit}>
              <input
                type="text"
                style={styles.textInput}
                value={textValue}
                onChange={(e) => setTextValue(e.target.value)}
                placeholder="Type your message here... (अपना संदेश यहाँ लिखें)"
              />
              <button
                type="submit"
                style={styles.sendButton}
                onMouseEnter={(e) => {
                  e.target.style.transform = "translateY(-2px)";
                  e.target.style.boxShadow =
                    "0 5px 15px rgba(102, 126, 234, 0.4)";
                }}
                onMouseLeave={(e) => {
                  e.target.style.transform = "translateY(0)";
                  e.target.style.boxShadow = "none";
                }}
              >
                Send
              </button>
            </form>

            {recognition && (
              <button
                style={styles.switchButton}
                onClick={() => setUseTextInput(false)}
                onMouseEnter={(e) => {
                  e.target.style.background = "#667eea";
                  e.target.style.color = "white";
                }}
                onMouseLeave={(e) => {
                  e.target.style.background = "white";
                  e.target.style.color = "#667eea";
                }}
              >
                Switch to Voice Input
              </button>
            )}
          </>
        )}
      </div>

      {isListening && (
        <div style={styles.listeningIndicator}>
          <p style={styles.listeningText}>सुन रहा हूँ... (Listening...)</p>
          {transcript && <p style={styles.interimTranscript}>{transcript}</p>}
        </div>
      )}

      <div style={styles.instructions}>
        {!useTextInput ? (
          <>
            <p style={styles.instructionText}>
              🎙️ माइक बटन दबाएं और बोलना शुरू करें
            </p>
            <p style={styles.instructionText}>
              Click the microphone and start speaking
            </p>
            <p style={{ fontSize: "0.85rem", color: "#999" }}>
              Note: Voice input requires internet connection
            </p>
          </>
        ) : (
          <>
            <p style={styles.instructionText}>
              💬 Type your message and press Send
            </p>
            <p style={styles.instructionText}>
              अपना संदेश टाइप करें और Send दबाएं
            </p>
          </>
        )}
      </div>
    </div>
  );
};

export default VoiceInput;
