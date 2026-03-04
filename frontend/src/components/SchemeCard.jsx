import React, { useState } from "react";

const SchemeCard = ({ scheme }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const getCategoryIcon = (category) => {
    const icons = {
      Agriculture: "🌾",
      Healthcare: "🏥",
      Housing: "🏠",
      Employment: "💼",
      Education: "📚",
      "Women & Child": "👩‍👧",
      "Social Security": "🛡️",
      Energy: "⚡",
      "Financial Inclusion": "💰",
    };
    return icons[category] || "📋";
  };

  const getScopeColor = (type) => {
    return type === "Central"
      ? "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
      : "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)";
  };

  const handleApplyNow = () => {
    const message =
      `Application Process for ${scheme.name}:\n\n` +
      `📍 Visit: ${scheme.officialWebsite || "myScheme.gov.in"}\n` +
      `📞 Helpline: ${scheme.helpline || "Contact your nearest CSC"}\n\n` +
      `Required Documents:\n` +
      scheme.documents.map((doc) => `   ✓ ${doc}`).join("\n") +
      `\n\nSteps:\n` +
      `1. Visit official website or nearest Common Service Centre\n` +
      `2. Carry all required documents\n` +
      `3. Fill application form\n` +
      `4. Submit and get acknowledgment\n\n` +
      `Would you like to visit the official website?`;

    if (window.confirm(message) && scheme.officialWebsite) {
      window.open(scheme.officialWebsite, "_blank");
    }
  };

  const styles = {
    card: {
      background: "white",
      borderRadius: "15px",
      padding: "1.5rem",
      boxShadow: "0 5px 15px rgba(0, 0, 0, 0.1)",
      transition: "all 0.3s ease",
      cursor: "pointer",
      border: "2px solid transparent",
      position: "relative",
      overflow: "hidden",
    },
    cardHover: {
      transform: "translateY(-5px)",
      boxShadow: "0 10px 30px rgba(102, 126, 234, 0.3)",
      borderColor: "#667eea",
    },
    ribbon: {
      position: "absolute",
      top: "15px",
      right: "-35px",
      background: getScopeColor(scheme.type),
      color: "white",
      padding: "5px 40px",
      fontSize: "0.75rem",
      fontWeight: "bold",
      transform: "rotate(45deg)",
      boxShadow: "0 2px 5px rgba(0,0,0,0.2)",
    },
    header: {
      display: "flex",
      alignItems: "flex-start",
      gap: "1rem",
      marginBottom: "1rem",
    },
    icon: {
      fontSize: "2.5rem",
      flexShrink: 0,
    },
    titleSection: {
      flex: 1,
    },
    schemeName: {
      color: "#667eea",
      fontSize: "1.2rem",
      margin: "0 0 0.25rem 0",
      fontWeight: "bold",
    },
    schemeNameHi: {
      color: "#999",
      fontSize: "0.9rem",
      margin: 0,
      fontStyle: "italic",
    },
    tags: {
      display: "flex",
      gap: "0.5rem",
      flexWrap: "wrap",
      marginBottom: "1rem",
    },
    tag: {
      padding: "0.25rem 0.75rem",
      borderRadius: "15px",
      fontSize: "0.75rem",
      fontWeight: 600,
      background: "#f0f0f0",
      color: "#666",
    },
    categoryTag: {
      background: "linear-gradient(135deg, #11998e 0%, #38ef7d 100%)",
      color: "white",
    },
    description: {
      color: "#666",
      lineHeight: 1.6,
      marginBottom: "1rem",
      fontSize: "0.95rem",
    },
    benefitsSection: {
      marginBottom: "1rem",
    },
    benefitsTitle: {
      color: "#333",
      fontWeight: "bold",
      marginBottom: "0.5rem",
      display: "flex",
      alignItems: "center",
      gap: "0.5rem",
    },
    benefitsList: {
      listStyle: "none",
      padding: 0,
      margin: 0,
    },
    benefitItem: {
      padding: "0.4rem 0",
      paddingLeft: "1.5rem",
      position: "relative",
      fontSize: "0.9rem",
      color: "#555",
    },
    checkmark: {
      position: "absolute",
      left: 0,
      color: "#38ef7d",
      fontWeight: "bold",
    },
    expandedSection: {
      marginTop: "1rem",
      padding: "1rem",
      background: "#f9f9f9",
      borderRadius: "10px",
      fontSize: "0.9rem",
    },
    infoGrid: {
      display: "grid",
      gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))",
      gap: "1rem",
      marginBottom: "1rem",
    },
    infoItem: {
      display: "flex",
      flexDirection: "column",
      gap: "0.25rem",
    },
    infoLabel: {
      color: "#999",
      fontSize: "0.75rem",
      textTransform: "uppercase",
      fontWeight: 600,
    },
    infoValue: {
      color: "#333",
      fontWeight: "bold",
    },
    actions: {
      display: "flex",
      gap: "0.75rem",
      marginTop: "1rem",
    },
    btnPrimary: {
      flex: 1,
      padding: "0.75rem",
      border: "none",
      borderRadius: "10px",
      fontSize: "0.95rem",
      fontWeight: 600,
      cursor: "pointer",
      background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
      color: "white",
      transition: "all 0.3s ease",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      gap: "0.5rem",
    },
    btnSecondary: {
      flex: 1,
      padding: "0.75rem",
      borderRadius: "10px",
      fontSize: "0.95rem",
      fontWeight: 600,
      cursor: "pointer",
      background: "white",
      color: "#667eea",
      border: "2px solid #667eea",
      transition: "all 0.3s ease",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      gap: "0.5rem",
    },
  };

  const [isHovered, setIsHovered] = useState(false);

  return (
    <div
      style={{
        ...styles.card,
        ...(isHovered ? styles.cardHover : {}),
      }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={() => setIsExpanded(!isExpanded)}
    >
      <div style={styles.ribbon}>{scheme.type || "Central"}</div>

      <div style={styles.header}>
        <div style={styles.icon}>{getCategoryIcon(scheme.category)}</div>
        <div style={styles.titleSection}>
          <h3 style={styles.schemeName}>{scheme.nameEn || scheme.name}</h3>
          <p style={styles.schemeNameHi}>{scheme.nameHi}</p>
        </div>
      </div>

      <div style={styles.tags}>
        <span style={{ ...styles.tag, ...styles.categoryTag }}>
          {scheme.category}
        </span>
        <span style={styles.tag}>
          {scheme.state === "All India" ? "🇮🇳 All India" : `📍 ${scheme.state}`}
        </span>
        {scheme.helpline && (
          <span style={styles.tag}>📞 {scheme.helpline}</span>
        )}
      </div>

      <p style={styles.description}>{scheme.description}</p>

      <div style={styles.benefitsSection}>
        <div style={styles.benefitsTitle}>
          <span>✨</span>
          <span>Key Benefits</span>
        </div>
        <ul style={styles.benefitsList}>
          {scheme.benefits
            .slice(0, isExpanded ? undefined : 3)
            .map((benefit, idx) => (
              <li key={idx} style={styles.benefitItem}>
                <span style={styles.checkmark}>✓</span>
                {benefit}
              </li>
            ))}
        </ul>
        {!isExpanded && scheme.benefits.length > 3 && (
          <p
            style={{
              color: "#667eea",
              fontSize: "0.85rem",
              marginTop: "0.5rem",
            }}
          >
            +{scheme.benefits.length - 3} more benefits...
          </p>
        )}
      </div>

      {isExpanded && (
        <div style={styles.expandedSection}>
          <div style={styles.infoGrid}>
            <div style={styles.infoItem}>
              <span style={styles.infoLabel}>Age Range</span>
              <span style={styles.infoValue}>
                {scheme.eligibility.minAge}-
                {scheme.eligibility.maxAge === 999
                  ? "∞"
                  : scheme.eligibility.maxAge}{" "}
                years
              </span>
            </div>
            <div style={styles.infoItem}>
              <span style={styles.infoLabel}>Income Range</span>
              <span style={styles.infoValue}>
                ₹{scheme.eligibility.minIncome.toLocaleString()}-
                {scheme.eligibility.maxIncome === 999999999
                  ? "No Limit"
                  : `₹${scheme.eligibility.maxIncome.toLocaleString()}`}
              </span>
            </div>
            <div style={styles.infoItem}>
              <span style={styles.infoLabel}>Ministry</span>
              <span style={styles.infoValue}>{scheme.ministry}</span>
            </div>
          </div>

          <div style={{ marginTop: "1rem" }}>
            <div style={styles.benefitsTitle}>
              <span>📄</span>
              <span>Required Documents</span>
            </div>
            <ul style={styles.benefitsList}>
              {scheme.documents.map((doc, idx) => (
                <li key={idx} style={styles.benefitItem}>
                  <span style={styles.checkmark}>📎</span>
                  {doc}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      <div style={styles.actions} onClick={(e) => e.stopPropagation()}>
        <button
          style={styles.btnPrimary}
          onClick={handleApplyNow}
          onMouseEnter={(e) => {
            e.target.style.transform = "translateY(-2px)";
            e.target.style.boxShadow = "0 5px 15px rgba(102, 126, 234, 0.4)";
          }}
          onMouseLeave={(e) => {
            e.target.style.transform = "translateY(0)";
            e.target.style.boxShadow = "none";
          }}
        >
          <span>🚀</span>
          <span>Apply Now</span>
        </button>
        <button
          style={styles.btnSecondary}
          onClick={() => setIsExpanded(!isExpanded)}
          onMouseEnter={(e) => {
            e.target.style.background = "#667eea";
            e.target.style.color = "white";
          }}
          onMouseLeave={(e) => {
            e.target.style.background = "white";
            e.target.style.color = "#667eea";
          }}
        >
          <span>{isExpanded ? "▲" : "▼"}</span>
          <span>{isExpanded ? "Show Less" : "Learn More"}</span>
        </button>
      </div>
    </div>
  );
};

export default SchemeCard;
