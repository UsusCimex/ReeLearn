// src/pages/VideosPage.jsx
import React, { useState, useEffect } from "react";
import {
  Box,
  Typography,
  Paper,
  TextField,
  InputAdornment
} from "@mui/material";
import SearchIcon from "@mui/icons-material/Search";
import VideoList from "../components/VideoList";
import LoadingSpinner from "../components/LoadingSpinner";
import AlertMessage from "../components/AlertMessage";
import { getVideos } from "../services/api"; // Реализуйте API‑запросы согласно вашему бэкенду
import { useTranslation } from "../hooks/useTranslation";
import { motion } from "framer-motion";

const VideosPage = () => {
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const { t } = useTranslation();

  useEffect(() => {
    const fetchVideos = async () => {
      setLoading(true);
      setError("");
      try {
        const res = await getVideos();
        setVideos(res || []);
      } catch (err) {
        setError(err.response?.data?.detail || err.message);
        setVideos([]);
      } finally {
        setLoading(false);
      }
    };
    fetchVideos();
  }, []);

  // Фильтрация видео по названию
  const filteredVideos = videos.filter((video) =>
    video.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <Box sx={{ p: { xs: 2, md: 4 } }}>
      {/* Заголовок страницы с поисковым полем */}
      <Paper
        sx={{
          p: 3,
          mb: 4,
          background: "linear-gradient(135deg, #1976d2, #0d47a1)",
          color: "#fff",
          borderRadius: 2,
          boxShadow: 3,
          textAlign: "center"
        }}
      >
        <Typography variant="h4" sx={{ mb: 1, fontWeight: "bold", color: "#fff" }}>
          {t("uploadedVideos")}
        </Typography>
        <Typography variant="subtitle1" sx={{ mb: 2 }}>
          {t("viewAllVideos", "Browse and enjoy all uploaded videos.")}
        </Typography>
        <TextField
          variant="outlined"
          size="small"
          placeholder={t("searchVideos", "Search videos...")}
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          sx={{
            backgroundColor: "#fff",
            borderRadius: 1,
            width: { xs: "90%", md: "40%" }
          }}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon color="primary" />
              </InputAdornment>
            )
          }}
        />
      </Paper>

      {/* Секция со списком видео */}
      {loading ? (
        <LoadingSpinner />
      ) : (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <VideoList videos={filteredVideos} />
        </motion.div>
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

export default VideosPage;
