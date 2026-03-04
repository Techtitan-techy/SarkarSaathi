import React, { useState, useEffect } from "react";
import SchemeCard from "./SchemeCard";
import FilterPanel from "./FilterPanel";

const SchemeList = ({ schemes }) => {
  const [filteredSchemes, setFilteredSchemes] = useState(schemes);
  const [filters, setFilters] = useState({
    category: "all",
    state: "all",
    scope: "all",
  });

  useEffect(() => {
    setFilteredSchemes(schemes);
  }, [schemes]);

  if (!schemes || schemes.length === 0) {
    return null;
  }

  const handleFilterChange = (newFilters) => {
    setFilters(newFilters);

    let filtered = [...schemes];

    // Filter by category
    if (newFilters.category !== "all") {
      filtered = filtered.filter((s) => s.category === newFilters.category);
    }

    // Filter by state
    if (newFilters.state !== "all") {
      filtered = filtered.filter(
        (s) =>
          s.state === newFilters.state ||
          s.state === "All India" ||
          s.eligibility?.allowedStates?.includes(newFilters.state) ||
          s.eligibility?.allowedStates?.includes("all") ||
          s.eligibility?.allowedStates?.includes("All India"),
      );
    }

    // Filter by scope
    if (newFilters.scope !== "all") {
      if (newFilters.scope === "central") {
        filtered = filtered.filter((s) => s.type === "Central");
      } else if (newFilters.scope === "state") {
        filtered = filtered.filter((s) => s.type === "State");
      }
    }

    setFilteredSchemes(filtered);
  };

  const styles = {
    container: {
      marginTop: "2rem",
    },
    title: {
      color: "white",
      textAlign: "center",
      marginBottom: "1.5rem",
      fontSize: "2rem",
      textShadow: "2px 2px 4px rgba(0,0,0,0.3)",
    },
    grid: {
      display: "grid",
      gridTemplateColumns: "repeat(auto-fill, minmax(350px, 1fr))",
      gap: "1.5rem",
    },
    noResults: {
      textAlign: "center",
      padding: "3rem",
      background: "rgba(255, 255, 255, 0.95)",
      borderRadius: "15px",
      color: "#666",
    },
    noResultsIcon: {
      fontSize: "4rem",
      marginBottom: "1rem",
    },
    noResultsText: {
      fontSize: "1.2rem",
      marginBottom: "0.5rem",
    },
  };

  return (
    <div style={styles.container}>
      <h2 style={styles.title}>आपके लिए योजनाएं (Schemes for You) 🎯</h2>

      <FilterPanel onFilterChange={handleFilterChange} schemes={schemes} />

      {filteredSchemes.length === 0 ? (
        <div style={styles.noResults}>
          <div style={styles.noResultsIcon}>🔍</div>
          <div style={styles.noResultsText}>
            No schemes found matching your filters
          </div>
          <div>Try adjusting your filter criteria</div>
        </div>
      ) : (
        <div style={styles.grid}>
          {filteredSchemes.map((scheme, index) => (
            <SchemeCard key={scheme.id || index} scheme={scheme} />
          ))}
        </div>
      )}
    </div>
  );
};

export default SchemeList;
