import React, { useRef, useEffect, useState } from "react";
import { Box, Typography, IconButton } from "@mui/material";
import FullscreenIcon from "@mui/icons-material/Fullscreen";
import Highlighter from "react-highlight-words";

const VideoPlayer = ({
  videoUrl,
  fragments = [],
  searchWords = [],
  exactSearch = false,
  staticSubtitle,
}) => {
  const containerRef = useRef(null);
  const videoRef = useRef(null);
  const overlayRef = useRef(null);
  const [currentSubtitle, setCurrentSubtitle] = useState(staticSubtitle || "");

  // Если staticSubtitle не передан, используем динамический режим (по времени)
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

  // Обработка перехода в/из полноэкранного режима для корректного позиционирования оверлея
  useEffect(() => {
    const handleFullscreenChange = () => {
      const isFullscreen =
        document.fullscreenElement === containerRef.current ||
        document.webkitFullscreenElement === containerRef.current ||
        document.mozFullScreenElement === containerRef.current ||
        document.msFullscreenElement === containerRef.current;
      if (overlayRef.current) {
        overlayRef.current.style.position = isFullscreen ? "fixed" : "absolute";
        overlayRef.current.style.bottom = "10px";
        overlayRef.current.style.left = "0";
        overlayRef.current.style.right = "0";
        overlayRef.current.style.zIndex = isFullscreen ? "9999" : "10";
      }
    };

    document.addEventListener("fullscreenchange", handleFullscreenChange);
    document.addEventListener("webkitfullscreenchange", handleFullscreenChange);
    document.addEventListener("mozfullscreenchange", handleFullscreenChange);
    document.addEventListener("MSFullscreenChange", handleFullscreenChange);
    return () => {
      document.removeEventListener("fullscreenchange", handleFullscreenChange);
      document.removeEventListener("webkitfullscreenchange", handleFullscreenChange);
      document.removeEventListener("mozfullscreenchange", handleFullscreenChange);
      document.removeEventListener("MSFullscreenChange", handleFullscreenChange);
    };
  }, []);

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
        backgroundColor: "black",
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
          zIndex: 20,
        }}
      >
        <IconButton onClick={handleFullscreen} sx={{ color: "#fff" }}>
          <FullscreenIcon />
        </IconButton>
      </Box>
      <Box
        ref={overlayRef}
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
          pointerEvents: "none",
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
    </Box>
  );
};

export default VideoPlayer;
