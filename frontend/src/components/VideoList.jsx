import React from "react";
import { Grid, Typography } from "@mui/material";
import VideoCard from "./VideoCard";

const VideoList = ({ videos }) => {
  if (!videos || videos.length === 0) {
    return <Typography>No videos available.</Typography>;
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
