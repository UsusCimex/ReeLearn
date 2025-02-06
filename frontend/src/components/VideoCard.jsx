import React from "react";
import { Card, CardContent, Typography, CardActionArea } from "@mui/material";
import { Link as RouterLink } from "react-router-dom";

const VideoCard = ({ video }) => (
  <Card>
    <CardActionArea component={RouterLink} to={`/videos/${video.id}`}>
      <CardContent>
        <Typography variant="h6">{video.name}</Typography>
        <Typography variant="body2" color="text.secondary">
          Fragments: {video.fragments_count}
        </Typography>
      </CardContent>
    </CardActionArea>
  </Card>
);

export default VideoCard;
