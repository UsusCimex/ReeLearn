// src/pages/HomePage.jsx
import React, { useState } from "react";
import { Typography, Box } from "@mui/material";
import SearchBar from "../components/SearchBar";
import SearchResults from "../components/SearchResults";
import LoadingSpinner from "../components/LoadingSpinner";
import AlertMessage from "../components/AlertMessage";
import { searchVideos } from "../services/api";

const HomePage = () => {
  const [results, setResults] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [exactSearch, setExactSearch] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSearch = async (query, exact) => {
    setSearchQuery(query);
    setExactSearch(exact);
    setLoading(true);
    setError("");
    try {
      const res = await searchVideos(query, exact);
      setResults(res.results || []);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 2 }}>Search Videos</Typography>
      <SearchBar onSearch={handleSearch} />
      {loading ? (
        <LoadingSpinner />
      ) : (
        <SearchResults
          results={results}
          highlightWords={searchQuery.split(" ").filter((w) => w.trim() !== "")}
          exactSearch={exactSearch}
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
