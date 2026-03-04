import React, { useEffect, useRef } from "react";

const ChatInterface = ({ messages }) => {
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  if (messages.length === 0) {
    return null;
  }

  const styles = {
    container: {
      background: "white",
      borderRadius: "20px",
      padding: "1.5rem",
      marginBottom: "2rem",
      boxShadow: "0 10px 30px rgba(0, 0, 0, 0.2)",
      maxHeight: "500px",
      overflowY: "auto",
    },
    messagesContainer: {
      display: "flex",
      flexDirection: "column",
      gap: "1rem",
    },
    message: (isUser) => ({
      display: "flex",
      gap: "1rem",
      flexDirection: isUser ? "row-reverse" : "row",
      animation: "slideIn 0.3s ease",
    }),
    avatar: {
      fontSize: "2rem",
      flexShrink: 0,
    },
    messageContent: (isUser) => ({
      background: isUser
        ? "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
        : "#f5f5f5",
      color: isUser ? "white" : "#333",
      padding: "1rem",
      borderRadius: "15px",
      maxWidth: "70%",
    }),
    messageText: {
      margin: "0 0 0.5rem 0",
      lineHeight: 1.5,
    },
    messageTime: (isUser) => ({
      fontSize: "0.75rem",
      opacity: 0.7,
      color: isUser ? "rgba(255, 255, 255, 0.8)" : "#666",
    }),
  };

  return (
    <div style={styles.container}>
      <style>{`
        @keyframes slideIn {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>

      <div style={styles.messagesContainer}>
        {messages.map((message, index) => {
          const isUser = message.type === "user";
          return (
            <div key={index} style={styles.message(isUser)}>
              <div style={styles.avatar}>{isUser ? "👤" : "🤖"}</div>
              <div style={styles.messageContent(isUser)}>
                <p style={styles.messageText}>{message.text}</p>
                <span style={styles.messageTime(isUser)}>
                  {new Date(message.timestamp).toLocaleTimeString("en-IN", {
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </span>
              </div>
            </div>
          );
        })}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
};

export default ChatInterface;
