import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Typography, Box, TextField, Grid } from "@mui/material";
import VideoPlayer from "../components/VideoPlayer";
import LoadingSpinner from "../components/LoadingSpinner";
import AlertMessage from "../components/AlertMessage";
import { getVideoFragments } from "../services/api";

const VideoDetailPage = () => {
  const { id } = useParams();
  const [allFragments, setAllFragments] = useState([]);
  const [filteredFragments, setFilteredFragments] = useState([]);
  const [videoUrl, setVideoUrl] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fetchVideoDetails = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await getVideoFragments(id);
      // Ожидается, что API возвращает объект с полями video_url и fragments
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
    <Box sx={{ p: 2 }}>
      <Typography variant="h4" sx={{ mb: 2 }}>
        Video Detail
      </Typography>
      {loading ? (
        <LoadingSpinner />
      ) : (
        <>
          {/* Полный видеоплеер с динамическими субтитрами */}
          <Typography variant="h6" sx={{ mb: 1 }}>
            Full Video
          </Typography>
          <VideoPlayer
            videoUrl={videoUrl}
            fragments={allFragments}
            searchWords={[]}
            exactSearch={false}
          />
          {/* Секция с фрагментами */}
          <Box sx={{ mt: 4 }}>
            <Typography variant="h6" sx={{ mb: 1 }}>
              Video Fragments
            </Typography>
            <TextField
              label="Search fragments"
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
                    fragments={[]} // Используем статический режим
                    staticSubtitle={frag.text}
                    searchWords={searchQuery.split(" ").filter((w) => w.trim() !== "")}
                    exactSearch={true}
                  />
                  <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                    Time: {frag.timecode_start} - {frag.timecode_end}
                  </Typography>
                </Grid>
              ))}
            </Grid>
          </Box>
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
