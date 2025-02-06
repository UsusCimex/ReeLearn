// src/pages/HomePage.jsx
import React, { useState, useEffect } from "react";
import { Typography, Box } from "@mui/material";
import SearchBar from "../components/SearchBar";
import QueryHistory from "../components/QueryHistory";
import SearchResults from "../components/SearchResults";
import LoadingSpinner from "../components/LoadingSpinner";
import AlertMessage from "../components/AlertMessage";
import { searchVideos } from "../services/api";
import { useTranslation } from "../hooks/useTranslation";

const HomePage = () => {
  const [results, setResults] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [exactSearch, setExactSearch] = useState("false");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [queryHistory, setQueryHistory] = useState([]);
  const { t } = useTranslation();

  // Загружаем историю запросов при монтировании
  useEffect(() => {
    const saved = JSON.parse(localStorage.getItem("queryHistory") || "[]");
    setQueryHistory(saved);
  }, []);

  const handleSearch = async (query, exact) => {
    setLoading(true);
    setError("");
    try {
      const res = await searchVideos(query, exact);
      setResults(res.results || []);
      // Обновляем историю только при отправке запроса (Enter)
      if (query.trim()) {
        let history = JSON.parse(localStorage.getItem("queryHistory") || "[]");
        if (history[0] !== query) {
          history = [query, ...history.filter((q) => q !== query)].slice(0, 10);
          localStorage.setItem("queryHistory", JSON.stringify(history));
          setQueryHistory(history);
        }
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleQueryChange = (e) => {
    setSearchQuery(e.target.value);
  };

  const handleExactChange = (e) => {
    setExactSearch(e.target.value);
  };

  const handleSelectHistory = (query) => {
    setSearchQuery(query);
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" sx={{ mb: 2 }}>
        {t("searchVideos")}
      </Typography>
      <SearchBar
        value={searchQuery}
        onChange={handleQueryChange}
        onSearch={handleSearch}
        exact={exactSearch}
        onExactChange={handleExactChange}
      />
      <QueryHistory history={queryHistory} onSelect={handleSelectHistory} />
      {loading ? (
        <LoadingSpinner />
      ) : (
        <SearchResults
          results={results}
          highlightWords={searchQuery.split(" ").filter((w) => w.trim() !== "")}
          exactSearch={exactSearch === "true"}
        />
      )}
      <AlertMessage
        open={!!error}
        onClose={() => setError("")}
        severity="error"
        message={error}
      />
    </Box>
  );
};

export default HomePage;
