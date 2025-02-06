// src/components/VideoList.jsx
import React from "react";
import { Grid, Typography } from "@mui/material";
import VideoCard from "./VideoCard";
import { useTranslation } from "../hooks/useTranslation";
import { motion } from "framer-motion";

const VideoList = ({ videos }) => {
  const { t } = useTranslation();

  if (!videos || videos.length === 0) {
    return (
      <Typography variant="h6" align="center">
        {t("noVideoAvail", "No videos available.")}
      </Typography>
    );
  }

  return (
    <Grid container spacing={3}>
      {videos.map((video, index) => (
        <Grid item xs={12} sm={6} md={4} key={video.id}>
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.4, delay: index * 0.1 }}
          >
            <VideoCard video={video} />
          </motion.div>
        </Grid>
      ))}
    </Grid>
  );
};

export default VideoList;
