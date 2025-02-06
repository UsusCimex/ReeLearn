import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Box, Typography, TextField, Grid, Paper } from "@mui/material";
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
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const { t } = useTranslation();

  const fetchVideoDetails = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await getVideoFragments(id);
      setAllFragments(res.fragments || []);
      setFilteredFragments(res.fragments || []);
      setVideoUrl(res.video_url || "");
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
          <Paper sx={{ p: 3, mb: 4 }}>
            <Typography variant="h4" sx={{ mb: 2 }}>
              {t("videoDetail")}
            </Typography>
            <Typography variant="h6" sx={{ mb: 1 }}>
              {t("fullVideo")}
            </Typography>
            <VideoPlayer
              videoUrl={videoUrl}
              fragments={allFragments}
              searchWords={[]}
              exactSearch={false}
            />
          </Paper>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" sx={{ mb: 1 }}>
              {t("videoFragments")}
            </Typography>
            <TextField
              label={t("searchFragments")}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              fullWidth
              sx={{ mb: 2 }}
            />
            <Grid container spacing={2}>
              {filteredFragments.map((frag) => (
                <Grid item xs={12} sm={6} md={4} key={frag.fragment_id}>
                  <VideoPlayer
                    videoUrl={frag.s3_url}
                    fragments={[]} // Статичный режим для фрагмента
                    staticSubtitle={frag.text}
                    searchWords={searchQuery.split(" ").filter((w) => w.trim() !== "")}
                    exactSearch={true}
                  />
                  <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                    {`${t("time")}: ${frag.timecode_start} - ${frag.timecode_end}`}
                  </Typography>
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
    </Box>
  );
};

export default VideoDetailPage;
