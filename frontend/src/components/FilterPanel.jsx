import React, { useState } from "react";

const FilterPanel = ({ onFilterChange, schemes }) => {
  const [filters, setFilters] = useState({
    category: "all",
    state: "all",
    scope: "all", // all, central, state
  });

  // Extract unique categories from schemes
  const categories = [
    "all",
    ...new Set(schemes.map((s) => s.category).filter(Boolean)),
  ];

  // Indian states list
  const states = [
    "all",
    "All India",
    "Andhra Pradesh",
    "Arunachal Pradesh",
    "Assam",
    "Bihar",
    "Chhattisgarh",
    "Goa",
    "Gujarat",
    "Haryana",
    "Himachal Pradesh",
    "Jharkhand",
    "Karnataka",
    "Kerala",
    "Madhya Pradesh",
    "Maharashtra",
    "Manipur",
    "Meghalaya",
    "Mizoram",
    "Nagaland",
    "Odisha",
    "Punjab",
    "Rajasthan",
    "Sikkim",
    "Tamil Nadu",
    "Telangana",
    "Tripura",
    "Uttar Pradesh",
    "Uttarakhand",
    "West Bengal",
  ];

  const handleFilterChange = (filterType, value) => {
    const newFilters = { ...filters, [filterType]: value };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  const styles = {
    panel: {
      background: "rgba(255, 255, 255, 0.95)",
      borderRadius: "15px",
      padding: "1.5rem",
      marginBottom: "2rem",
      boxShadow: "0 5px 15px rgba(0, 0, 0, 0.1)",
    },
    title: {
      color: "#667eea",
      fontSize: "1.3rem",
      marginBottom: "1rem",
      display: "flex",
      alignItems: "center",
      gap: "0.5rem",
    },
    filterGrid: {
      display: "grid",
      gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
      gap: "1rem",
    },
    filterGroup: {
      display: "flex",
      flexDirection: "column",
      gap: "0.5rem",
    },
    label: {
      color: "#333",
      fontWeight: 600,
      fontSize: "0.9rem",
      display: "flex",
      alignItems: "center",
      gap: "0.5rem",
    },
    select: {
      padding: "0.75rem",
      borderRadius: "10px",
      border: "2px solid #e0e0e0",
      fontSize: "0.95rem",
      background: "white",
      cursor: "pointer",
      transition: "all 0.3s ease",
      outline: "none",
    },
    statsBar: {
      marginTop: "1rem",
      padding: "1rem",
      background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
      borderRadius: "10px",
      color: "white",
      display: "flex",
      justifyContent: "space-around",
      flexWrap: "wrap",
      gap: "1rem",
    },
    stat: {
      textAlign: "center",
    },
    statNumber: {
      fontSize: "1.8rem",
      fontWeight: "bold",
      display: "block",
    },
    statLabel: {
      fontSize: "0.85rem",
      opacity: 0.9,
    },
  };

  return (
    <div style={styles.panel}>
      <h3 style={styles.title}>
        <span>🔍</span>
        Filter Schemes / योजनाएं फ़िल्टर करें
      </h3>

      <div style={styles.filterGrid}>
        <div style={styles.filterGroup}>
          <label style={styles.label}>
            <span>📂</span>
            Category / श्रेणी
          </label>
          <select
            style={styles.select}
            value={filters.category}
            onChange={(e) => handleFilterChange("category", e.target.value)}
            onFocus={(e) => (e.target.style.borderColor = "#667eea")}
            onBlur={(e) => (e.target.style.borderColor = "#e0e0e0")}
          >
            {categories.map((cat) => (
              <option key={cat} value={cat}>
                {cat === "all" ? "All Categories" : cat}
              </option>
            ))}
          </select>
        </div>

        <div style={styles.filterGroup}>
          <label style={styles.label}>
            <span>📍</span>
            State / राज्य
          </label>
          <select
            style={styles.select}
            value={filters.state}
            onChange={(e) => handleFilterChange("state", e.target.value)}
            onFocus={(e) => (e.target.style.borderColor = "#667eea")}
            onBlur={(e) => (e.target.style.borderColor = "#e0e0e0")}
          >
            {states.map((state) => (
              <option key={state} value={state}>
                {state === "all" ? "All States" : state}
              </option>
            ))}
          </select>
        </div>

        <div style={styles.filterGroup}>
          <label style={styles.label}>
            <span>🏛️</span>
            Scope / दायरा
          </label>
          <select
            style={styles.select}
            value={filters.scope}
            onChange={(e) => handleFilterChange("scope", e.target.value)}
            onFocus={(e) => (e.target.style.borderColor = "#667eea")}
            onBlur={(e) => (e.target.style.borderColor = "#e0e0e0")}
          >
            <option value="all">All Schemes</option>
            <option value="central">Central Schemes</option>
            <option value="state">State Schemes</option>
          </select>
        </div>
      </div>

      <div style={styles.statsBar}>
        <div style={styles.stat}>
          <span style={styles.statNumber}>{schemes.length}</span>
          <span style={styles.statLabel}>Total Schemes</span>
        </div>
        <div style={styles.stat}>
          <span style={styles.statNumber}>{categories.length - 1}</span>
          <span style={styles.statLabel}>Categories</span>
        </div>
        <div style={styles.stat}>
          <span style={styles.statNumber}>
            {schemes.filter((s) => s.type === "Central").length}
          </span>
          <span style={styles.statLabel}>Central</span>
        </div>
        <div style={styles.stat}>
          <span style={styles.statNumber}>
            {schemes.filter((s) => s.state !== "All India").length}
          </span>
          <span style={styles.statLabel}>State-Specific</span>
        </div>
      </div>
    </div>
  );
};

export default FilterPanel;
