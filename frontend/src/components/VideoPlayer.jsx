import React, { useRef, useEffect, useState } from "react";
import { Box, Typography, IconButton } from "@mui/material";
import FullscreenIcon from "@mui/icons-material/Fullscreen";
import Highlighter from "react-highlight-words";
import { motion } from "framer-motion";

const VideoPlayer = ({
  videoUrl,
  fragments = [],
  searchWords = [],
  exactSearch = false,
  staticSubtitle
}) => {
  const containerRef = useRef(null);
  const videoRef = useRef(null);
  const [currentSubtitle, setCurrentSubtitle] = useState(staticSubtitle || "");

  // Если используется динамический режим – обновляем субтитры в зависимости от текущего времени видео
  useEffect(() => {
    if (staticSubtitle !== undefined) {
      setCurrentSubtitle(staticSubtitle);
      return;
    }
    const video = videoRef.current;
    if (!video) return;
    const handleTimeUpdate = () => {
      if (fragments.length > 0) {
        const frag = fragments.find(
          (f) => video.currentTime >= f.timecode_start && video.currentTime <= f.timecode_end
        );
        setCurrentSubtitle(frag ? frag.text : "");
      } else {
        setCurrentSubtitle("");
      }
    };
    video.addEventListener("timeupdate", handleTimeUpdate);
    return () => video.removeEventListener("timeupdate", handleTimeUpdate);
  }, [fragments, staticSubtitle]);

  const handleFullscreen = () => {
    if (containerRef.current.requestFullscreen) {
      containerRef.current.requestFullscreen();
    } else if (containerRef.current.webkitRequestFullscreen) {
      containerRef.current.webkitRequestFullscreen();
    } else if (containerRef.current.mozRequestFullScreen) {
      containerRef.current.mozRequestFullScreen();
    } else if (containerRef.current.msRequestFullscreen) {
      containerRef.current.msRequestFullscreen();
    }
  };

  return (
    <Box
      ref={containerRef}
      sx={{
        position: "relative",
        width: "100%",
        backgroundColor: "black"
      }}
    >
      {videoUrl ? (
        <video
          ref={videoRef}
          src={videoUrl}
          controls
          style={{ width: "100%", display: "block" }}
          controlsList="nofullscreen"
        />
      ) : (
        <Typography variant="body2" color="text.secondary">
          Video URL not available.
        </Typography>
      )}
      <Box
        sx={{
          position: "absolute",
          top: 10,
          right: 10,
          zIndex: 20
        }}
      >
        <IconButton onClick={handleFullscreen} sx={{ color: "#fff" }}>
          <FullscreenIcon />
        </IconButton>
      </Box>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}
      >
        <Box
          sx={{
            position: "absolute",
            bottom: "10px",
            left: 0,
            right: 0,
            textAlign: "center",
            backgroundColor: "rgba(0, 0, 0, 0.6)",
            color: "#fff",
            py: 1,
            px: 2,
            borderRadius: "4px",
            pointerEvents: "none"
          }}
        >
          {exactSearch && searchWords.length > 0 ? (
            <Highlighter
              searchWords={searchWords}
              autoEscape={true}
              textToHighlight={currentSubtitle}
              highlightStyle={{ backgroundColor: "#ffeb3b", color: "black" }}
            />
          ) : (
            <Typography variant="body1">{currentSubtitle}</Typography>
          )}
        </Box>
      </motion.div>
    </Box>
  );
};

export default VideoPlayer;
