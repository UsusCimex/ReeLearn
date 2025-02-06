// src/components/VideoUploadForm.jsx
import React, { useState, useEffect, useRef } from "react";
import {
  Box,
  TextField,
  Button,
  LinearProgress,
  Typography,
  Paper
} from "@mui/material";
import AlertMessage from "./AlertMessage";
import { uploadVideo, getTaskStatus } from "../services/api"; // API‑сервисы должны быть реализованы отдельно
import { useTranslation } from "../hooks/useTranslation";

const VideoUploadForm = () => {
  const [file, setFile] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [taskId, setTaskId] = useState("");
  const [progress, setProgress] = useState(0);
  const [statusText, setStatusText] = useState("");
  const [error, setError] = useState("");
  const { t } = useTranslation();
  const fileInputRef = useRef();

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) {
      setError("Please select a video file.");
      return;
    }
    try {
      const res = await uploadVideo(file, name, description);
      setTaskId(res.task_id);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    }
  };

  useEffect(() => {
    let interval;
    if (taskId) {
      interval = setInterval(async () => {
        try {
          const statusRes = await getTaskStatus(taskId);
          setProgress(statusRes.progress || 0);
          setStatusText(statusRes.current_operation || "");
          if (
            statusRes.status === "completed" ||
            statusRes.status === "failed"
          ) {
            clearInterval(interval);
          }
        } catch (err) {
          setError(err.response?.data?.detail || err.message);
          clearInterval(interval);
        }
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [taskId]);

  const handleFileChange = (e) => {
    if (e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  };

  // Обработчики для drag & drop
  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setFile(e.dataTransfer.files[0]);
      e.dataTransfer.clearData();
    }
  };

  return (
    <Box>
      <Box
        component="form"
        onSubmit={handleUpload}
        sx={{
          display: "flex",
          flexDirection: "column",
          gap: 2
        }}
      >
        {/* Область drag & drop / выбора файла */}
        <Paper
          variant="outlined"
          sx={{
            p: 2,
            textAlign: "center",
            borderColor: dragOver ? "primary.main" : "grey.400",
            backgroundColor: dragOver ? "grey.100" : "inherit",
            cursor: "pointer",
            transition: "border-color 0.3s, background-color 0.3s"
          }}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current.click()}
        >
          <Typography variant="body1">
            {file
              ? file.name
              : t("selectFile") ||
                "Select Video File (click or drag & drop)"}
          </Typography>
          <input
            ref={fileInputRef}
            type="file"
            hidden
            accept="video/*"
            onChange={handleFileChange}
          />
        </Paper>
        <TextField
          label={t("videoName")}
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />
        <TextField
          label={t("description")}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          multiline
          rows={3}
        />
        <Button variant="contained" type="submit">
          {t("uploadVideo")}
        </Button>
      </Box>
      {taskId && (
        <Box sx={{ mt: 2 }}>
          <LinearProgress variant="determinate" value={progress} />
          <Typography variant="body2" sx={{ mt: 1 }}>
            {t("status")}: {statusText} ({progress}%)
          </Typography>
        </Box>
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

export default VideoUploadForm;
