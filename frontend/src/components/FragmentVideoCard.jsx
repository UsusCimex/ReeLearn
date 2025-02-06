// src/components/FragmentVideoCard.jsx
import React, { useRef, useEffect, useState } from "react";
import { Card, CardMedia, Box, Typography } from "@mui/material";
import Highlighter from "react-highlight-words";

const FragmentVideoCard = ({ fragment, searchWords = [], exactSearch = false }) => {
  const videoRef = useRef(null);
  const [currentTime, setCurrentTime] = useState(0);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;
    const handleTimeUpdate = () => {
      setCurrentTime(video.currentTime);
    };
    video.addEventListener("timeupdate", handleTimeUpdate);
    return () => video.removeEventListener("timeupdate", handleTimeUpdate);
  }, []);

  return (
    <Card sx={{ mb: 2, position: "relative" }}>
      <CardMedia
        component="video"
        ref={videoRef}
        src={fragment.s3_url}
        controls
        sx={{ width: "100%", maxHeight: 200 }}
      />
      <Box
        sx={{
          position: "absolute",
          bottom: { xs: 70, sm: 100 },
          left: 0,
          right: 0,
          textAlign: "center",
          backgroundColor: "rgba(0, 0, 0, 0.6)",
          color: "#fff",
          py: 1,
          px: 2,
          borderRadius: "4px",
          pointerEvents: "none",
        }}
      >
        {exactSearch && searchWords.length > 0 ? (
          <Highlighter
            searchWords={searchWords}
            autoEscape={true}
            textToHighlight={fragment.text}
            highlightStyle={{ backgroundColor: "#ffeb3b", color: "black" }}
          />
        ) : (
          <Typography variant="body2">{fragment.text}</Typography>
        )}
      </Box>
    </Card>
  );
};

export default FragmentVideoCard;
