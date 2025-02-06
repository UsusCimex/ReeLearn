import React from "react";
import { Grid, Typography } from "@mui/material";
import VideoCard from "./VideoCard";
import { useTranslation } from "../hooks/useTranslation";

const VideoList = ({ videos }) => {
  const { t } = useTranslation();

  if (!videos || videos.length === 0) {
    return <Typography>{t("noVideoAvail")}</Typography>;
  }
  return (
    <Grid container spacing={2}>
      {videos.map((video) => (
        <Grid item xs={12} sm={6} md={4} key={video.id}>
          <VideoCard video={video} />
        </Grid>
      ))}
    </Grid>
  );
};

export default VideoList;
