import React, { useEffect, useState } from "react";
import { Typography, Box } from "@mui/material";
import VideoList from "../components/VideoList";
import LoadingSpinner from "../components/LoadingSpinner";
import AlertMessage from "../components/AlertMessage";
import { getVideos } from "../services/api";

const VideosPage = () => {
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  
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
    <Box>
      <Typography variant="h4" sx={{ mb: 2 }}>Uploaded Videos</Typography>
      {loading ? <LoadingSpinner /> : <VideoList videos={videos} />}
      <AlertMessage open={!!error} onClose={() => setError("")} severity="error" message={error} />
    </Box>
  );
};

export default VideosPage;
