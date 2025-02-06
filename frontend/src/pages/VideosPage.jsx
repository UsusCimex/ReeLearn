import React, { useState, useEffect } from "react";
import { Box, Typography, Paper } from "@mui/material";
import VideoList from "../components/VideoList";
import LoadingSpinner from "../components/LoadingSpinner";
import AlertMessage from "../components/AlertMessage";
import { getVideos } from "../services/api"; // Реализуйте API‑запросы согласно вашему бэкенду
import { useTranslation } from "../hooks/useTranslation";

const VideosPage = () => {
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
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

  return (
    <Box sx={{ p: { xs: 2, md: 4 } }}>
      <Paper sx={{ p: 3, mb: 4 }}>
        <Typography variant="h4" sx={{ mb: 2 }}>
          {t("uploadedVideos")}
        </Typography>
        {loading ? <LoadingSpinner /> : <VideoList videos={videos} />}
      </Paper>
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
