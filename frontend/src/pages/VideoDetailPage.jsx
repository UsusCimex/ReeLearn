// src/pages/VideoDetailPage.jsx
import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import {
  Box,
  Typography,
  TextField,
  Grid,
  Paper,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  IconButton
} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import { motion } from "framer-motion";
import VideoPlayer from "../components/VideoPlayer";
import LoadingSpinner from "../components/LoadingSpinner";
import AlertMessage from "../components/AlertMessage";
import { getVideoFragments } from "../services/api"; // API‑функция для получения деталей видео
import { useTranslation } from "../hooks/useTranslation";

const VideoDetailPage = () => {
  const { id } = useParams();
  const [allFragments, setAllFragments] = useState([]);
  const [filteredFragments, setFilteredFragments] = useState([]);
  const [videoUrl, setVideoUrl] = useState("");
  const [videoTitle, setVideoTitle] = useState("");
  const [videoDescription, setVideoDescription] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [openFullVideo, setOpenFullVideo] = useState(false);
  const { t } = useTranslation();

  const fetchVideoDetails = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await getVideoFragments(id);
      setAllFragments(res.fragments || []);
      setFilteredFragments(res.fragments || []);
      setVideoUrl(res.video_url || "");
      setVideoTitle(res.title || "");
      setVideoDescription(res.description || "");
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchVideoDetails();
  }, [id]);

  useEffect(() => {
    if (!searchQuery.trim()) {
      setFilteredFragments(allFragments);
      return;
    }
    const query = searchQuery.toLowerCase();
    const filtered = allFragments.filter((frag) =>
      frag.text.toLowerCase().includes(query)
    );
    setFilteredFragments(filtered);
  }, [searchQuery, allFragments]);

  return (
    <Box sx={{ p: { xs: 2, md: 4 } }}>
      {loading ? (
        <LoadingSpinner />
      ) : (
        <>
          {/* Информационный блок с названием и описанием видео */}
          <Paper
            sx={{
              p: 3,
              mb: 3,
              backgroundColor: "#f0f0f0",
              borderRadius: 2,
              boxShadow: 1
            }}
          >
            <Typography variant="h5" sx={{ mb: 1 }}>
              {videoTitle || t("videoDetail")}
            </Typography>
            <Typography variant="body1" sx={{ color: "text.secondary" }}>
              {videoDescription}
            </Typography>
          </Paper>

          {/* Компактный заголовок с кнопкой для открытия полного видео */}
          <Box
            sx={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              mb: 2
            }}
          >
            <Typography variant="h6" sx={{ fontWeight: "bold" }}>
              {t("videoFragments", "Фрагменты видео")}
            </Typography>
            <Button
              variant="contained"
              onClick={() => setOpenFullVideo(true)}
              sx={{ textTransform: "none" }}
            >
              {t("fullVideo", "Полное видео")}
            </Button>
          </Box>

          {/* Блок с фрагментами видео и поиском */}
          <Paper sx={{ p: 3, mb: 4, minHeight: 300 }}>
            <TextField
              label={t("searchFragments", "Поиск фрагментов")}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              fullWidth
              sx={{ mb: 3 }}
            />
            <Grid container spacing={3}>
              {filteredFragments.map((frag, index) => (
                <Grid item xs={12} sm={6} md={4} key={frag.fragment_id}>
                  <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.4, delay: index * 0.1 }}
                    whileHover={{ scale: 1.03 }}
                  >
                    <Paper
                      sx={{
                        p: 1,
                        borderRadius: 2,
                        boxShadow: 1,
                        textAlign: "center",
                        cursor: "pointer",
                        transition: "transform 0.3s"
                      }}
                    >
                      <VideoPlayer
                        videoUrl={frag.s3_url}
                        fragments={[]} // Статичный режим для фрагмента
                        staticSubtitle={frag.text}
                        searchWords={searchQuery.split(" ").filter((w) => w.trim() !== "")}
                        exactSearch={true}
                        preview={true} // Режим превью: компактное видео
                      />
                      <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                        {`${t("time")}: ${frag.timecode_start} - ${frag.timecode_end}`}
                      </Typography>
                    </Paper>
                  </motion.div>
                </Grid>
              ))}
            </Grid>
          </Paper>
        </>
      )}
      <AlertMessage
        open={!!error}
        onClose={() => setError("")}
        severity="error"
        message={error}
      />

      {/* Модальное окно для полного видео */}
      <Dialog
        open={openFullVideo}
        onClose={() => setOpenFullVideo(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle
          sx={{
            m: 0,
            p: 2,
            background: "linear-gradient(135deg, #1976d2, #0d47a1)",
            color: "#fff"
          }}
        >
          {t("fullVideo", "Полное видео")}
          <IconButton
            aria-label="close"
            onClick={() => setOpenFullVideo(false)}
            sx={{
              position: "absolute",
              right: 8,
              top: 8,
              color: "#fff"
            }}
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent
          dividers
          sx={{
            p: 2,
            backgroundColor: "#f9f9f9",
            textAlign: "center"
          }}
        >
          <VideoPlayer
            videoUrl={videoUrl}
            fragments={allFragments}
            searchWords={[]}
            exactSearch={false}
          />
        </DialogContent>
      </Dialog>
    </Box>
  );
};

export default VideoDetailPage;
