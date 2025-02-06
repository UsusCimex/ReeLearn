// src/pages/HomePage.jsx
import React, { useState, useEffect, useRef, useCallback } from "react";
import {
  Box,
  Grid,
  Typography,
  IconButton,
  Paper,
  useMediaQuery
} from "@mui/material";
import { useTheme } from "@mui/material/styles";
import SearchBar from "../components/SearchBar";
import SearchResults from "../components/SearchResults";
import LoadingSpinner from "../components/LoadingSpinner";
import AlertMessage from "../components/AlertMessage";
import { searchVideos } from "../services/api";
import { useTranslation } from "../hooks/useTranslation";
import ArrowBackIosIcon from "@mui/icons-material/ArrowBackIos";
import ArrowForwardIosIcon from "@mui/icons-material/ArrowForwardIos";

const HomePage = () => {
  const [results, setResults] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [exactSearch, setExactSearch] = useState("false");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [queryHistory, setQueryHistory] = useState([]);
  const [submittedQuery, setSubmittedQuery] = useState(""); // новое состояние для зафиксированного запроса
  const { t } = useTranslation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));

  // Рефы для истории, результатов и поля поиска
  const historyRef = useRef(null);
  const resultsRef = useRef(null);
  const searchInputRef = useRef(null);
  const heroRef = useRef(null);

  useEffect(() => {
    const saved = JSON.parse(localStorage.getItem("queryHistory") || "[]");
    setQueryHistory(saved);
  }, []);

  useEffect(() => {
    const handleGlobalKeyDown = (e) => {
      if ((e.ctrlKey && e.key === "f") || (e.ctrlKey && e.key === "l")) {
        e.preventDefault();
        if (searchInputRef.current) {
          searchInputRef.current.focus();
          searchInputRef.current.select();
        }
      }
    };
    window.addEventListener("keydown", handleGlobalKeyDown);
    return () => window.removeEventListener("keydown", handleGlobalKeyDown);
  }, []);

  const scrollHistory = (direction) => {
    if (historyRef.current) {
      const scrollAmount = 150;
      historyRef.current.scrollBy({
        left: direction === "left" ? -scrollAmount : scrollAmount,
        behavior: "smooth"
      });
    }
  };

  // Функция поиска; при отправке устанавливаем submittedQuery
  const handleSearch = useCallback(async (query, exact) => {
    setLoading(true);
    setError("");
    try {
      const res = await searchVideos(query, exact);
      setResults(res.results || []);
      if (query.trim()) {
        let history = JSON.parse(localStorage.getItem("queryHistory") || "[]");
        if (history[0] !== query) {
          history = [query, ...history.filter((q) => q !== query)].slice(0, 5);
          localStorage.setItem("queryHistory", JSON.stringify(history));
          setQueryHistory(history);
        }
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
      setResults([]);
    } finally {
      setLoading(false);
      // Сохраняем отправленный запрос для прокрутки
      if (query.trim()) {
        setSubmittedQuery(query);
      }
    }
  }, []);

  // Эффект прокрутки: срабатывает только если submittedQuery установлен, загрузка завершена и есть результаты
  useEffect(() => {
    if (!loading && submittedQuery && results.length > 0) {
      // Прокрутка на 95% высоты окна
      const scrollTarget = window.innerHeight * 0.85;
      window.scrollTo({ top: scrollTarget, behavior: "smooth" });
      setSubmittedQuery(""); // сбрасываем после прокрутки
    }
  }, [loading, results, submittedQuery]);

  // При выборе элемента истории сразу вызываем поиск и фокусируем поле
  const handleSelectHistory = (query) => {
    setSearchQuery(query);
    handleSearch(query, exactSearch === "true");
    if (searchInputRef.current) {
      searchInputRef.current.focus();
      searchInputRef.current.select();
    }
  };

  const handleQueryChange = (e) => setSearchQuery(e.target.value);
  const handleExactChange = (e) => setExactSearch(e.target.value);

  return (
    <Box>
      {/* Hero section с тёмным фоном */}
      <Box
        ref={heroRef}
        sx={{
          position: "relative",
          height: { xs: "65vh", md: "75vh" },
          background: `linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.9)),
                       url('https://images.unsplash.com/photo-1518770660439-4636190af475?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80')`,
          backgroundSize: "cover",
          backgroundPosition: "center",
          display: "flex",
          alignItems: "center",
          justifyContent: "center"
        }}
      >
        <Box
          sx={{
            position: "relative",
            zIndex: 1,
            width: { xs: "90%", md: "60%" },
            p: 4,
            borderRadius: 2,
            bgcolor: "rgba(255, 255, 255, 0.95)",
            boxShadow: 3,
            textAlign: "center",
            color: "#000"
          }}
        >
          <Typography variant="h4" gutterBottom sx={{ fontWeight: "bold" }}>
            {t("welcome", "Welcome to ReeLearn!")}
          </Typography>
          <Typography variant="subtitle1" sx={{ mb: 3 }}>
            {t(
              "heroText",
              "Explore, upload, and share amazing video content with an intuitive and modern experience."
            )}
          </Typography>
          <SearchBar
            value={searchQuery}
            onChange={handleQueryChange}
            onSearch={handleSearch}
            exact={exactSearch}
            onExactChange={handleExactChange}
            inputRef={searchInputRef}
          />
        </Box>
      </Box>

      {/* История запросов */}
      {queryHistory && queryHistory.length > 0 && (
        <Box
          sx={{
            mt: 2,
            display: "flex",
            alignItems: "center",
            px: { xs: 2, md: 4 }
          }}
        >
          {!isMobile && (
            <IconButton onClick={() => scrollHistory("left")}>
              <ArrowBackIosIcon />
            </IconButton>
          )}
          <Box
            ref={historyRef}
            sx={{
              display: "flex",
              overflowX: "auto",
              flexGrow: 1,
              gap: 2,
              py: 1,
              "&::-webkit-scrollbar": { display: "none" }
            }}
          >
            {queryHistory.map((q, index) => (
              <Paper
                key={index}
                sx={{
                  px: 2,
                  py: 1,
                  cursor: "pointer",
                  flexShrink: 0,
                  bgcolor: "#f5f5f5",
                  transition: "transform 0.3s",
                  "&:hover": { transform: "scale(1.05)" }
                }}
                onClick={() => handleSelectHistory(q)}
              >
                <Typography variant="body2">{q}</Typography>
              </Paper>
            ))}
          </Box>
          {!isMobile && (
            <IconButton onClick={() => scrollHistory("right")}>
              <ArrowForwardIosIcon />
            </IconButton>
          )}
        </Box>
      )}

      {/* Результаты поиска */}
      <Box ref={resultsRef} sx={{ p: { xs: 2, md: 4 } }}>
        {loading ? (
          <LoadingSpinner />
        ) : (
          <SearchResults
            results={results}
            highlightWords={searchQuery.split(" ").filter((w) => w.trim() !== "")}
            exactSearch={exactSearch === "true"}
          />
        )}
      </Box>

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
