// src/components/VideoPlayer.jsx
import React, { useRef, useEffect, useState } from "react";
import { Box, Typography, IconButton, Fade } from "@mui/material";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import PauseIcon from "@mui/icons-material/Pause";
import FullscreenIcon from "@mui/icons-material/Fullscreen";
import CloudDownloadIcon from "@mui/icons-material/CloudDownload";
import Highlighter from "react-highlight-words";
import { motion } from "framer-motion";

const VideoPlayer = ({
  videoUrl,
  fragments = [],
  searchWords = [],
  exactSearch = false,
  staticSubtitle,
  preview = false // Если true, ограничиваем размер видео для превью
}) => {
  const containerRef = useRef(null);
  const videoRef = useRef(null);
  const [currentSubtitle, setCurrentSubtitle] = useState(staticSubtitle || "");
  const [isPlaying, setIsPlaying] = useState(false);

  // Обновление субтитров, если видео воспроизводится в динамическом режиме
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
          (f) =>
            video.currentTime >= f.timecode_start &&
            video.currentTime <= f.timecode_end
        );
        setCurrentSubtitle(frag ? frag.text : "");
      } else {
        setCurrentSubtitle("");
      }
    };
    video.addEventListener("timeupdate", handleTimeUpdate);
    return () => video.removeEventListener("timeupdate", handleTimeUpdate);
  }, [fragments, staticSubtitle]);

  // Переключение воспроизведения по клику
  const togglePlayPause = () => {
    const video = videoRef.current;
    if (!video) return;
    if (video.paused) {
      video.play();
      setIsPlaying(true);
    } else {
      video.pause();
      setIsPlaying(false);
    }
  };

  // Обработчик перехода в полноэкранный режим
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
        maxWidth: preview ? 400 : "100%",
        mx: "auto",
        backgroundColor: "black",
        borderRadius: 2,
        overflow: "hidden"
      }}
    >
      {videoUrl ? (
        <video
          ref={videoRef}
          src={videoUrl}
          style={{ width: "100%", display: "block" }}
          // Скрываем нативные элементы управления для использования кастомных кнопок
          controls={false}
          onClick={togglePlayPause}
        />
      ) : (
        <Typography variant="body2" color="text.secondary">
          Video URL not available.
        </Typography>
      )}

      {/* Центровая кнопка Play, если видео не воспроизводится */}
      <Fade in={!isPlaying}>
        <IconButton
          onClick={togglePlayPause}
          sx={{
            position: "absolute",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            color: "#fff",
            bgcolor: "rgba(0,0,0,0.5)",
            "&:hover": { bgcolor: "rgba(0,0,0,0.7)" },
            zIndex: 10
          }}
        >
          <PlayArrowIcon sx={{ fontSize: 50 }} />
        </IconButton>
      </Fade>

      {/* Панель управления в правом верхнем углу */}
      <Box
        sx={{
          position: "absolute",
          top: "10px",
          right: "10px",
          zIndex: 10,
          display: "flex",
          gap: 1
        }}
      >
        {/* Кнопка полноэкранного режима */}
        <IconButton
          onClick={handleFullscreen}
          sx={{
            color: "#fff",
            bgcolor: "rgba(0,0,0,0.5)",
            "&:hover": { bgcolor: "rgba(0,0,0,0.7)" }
          }}
        >
          <FullscreenIcon />
        </IconButton>
        {/* Кнопка скачивания видео */}
        <IconButton
          component="a"
          href={videoUrl}
          download
          sx={{
            color: "#fff",
            bgcolor: "rgba(0,0,0,0.5)",
            "&:hover": { bgcolor: "rgba(0,0,0,0.7)" }
          }}
        >
          <CloudDownloadIcon />
        </IconButton>
      </Box>

      {/* Субтитры */}
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
