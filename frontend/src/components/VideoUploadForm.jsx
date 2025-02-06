// src/components/VideoUploadForm.jsx
import React, { useState, useEffect } from "react";
import { Box, TextField, Button, LinearProgress, Typography } from "@mui/material";
import AlertMessage from "./AlertMessage";
import { uploadVideo, getTaskStatus } from "../services/api";
import { useTranslation } from "../hooks/useTranslation";

const VideoUploadForm = () => {
  const [file, setFile] = useState(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [taskId, setTaskId] = useState("");
  const [progress, setProgress] = useState(0);
  const [statusText, setStatusText] = useState("");
  const [error, setError] = useState("");
  const { t } = useTranslation();

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
          if (statusRes.status === "completed" || statusRes.status === "failed") {
            clearInterval(interval);
          }
        } catch (err) {
          setError(err.response?.data?.detail || err.message);
          clearInterval(interval);
        }
      }, 1000); // опрашивать каждые 1 секунду
    }
    return () => clearInterval(interval);
  }, [taskId]);

  return (
    <Box>
      <Box component="form" onSubmit={handleUpload} sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
        <Button variant="contained" component="label">
          {t("selectFile") || "Select Video File"}
          <input type="file" hidden accept="video/*" onChange={(e) => setFile(e.target.files[0])} />
        </Button>
        {file && <Typography variant="body2">{file.name}</Typography>}
        <TextField label={t("videoName") || "Video Name"} value={name} onChange={(e) => setName(e.target.value)} required />
        <TextField label={t("description") || "Description"} value={description} onChange={(e) => setDescription(e.target.value)} multiline rows={3} />
        <Button variant="contained" type="submit">
          {t("uploadVideo") || "Upload Video"}
        </Button>
      </Box>
      {taskId && (
        <Box sx={{ mt: 2 }}>
          <LinearProgress variant="determinate" value={progress} />
          <Typography variant="body2" sx={{ mt: 1 }}>
            {t("status") || "Status"}: {statusText} ({progress}%)
          </Typography>
        </Box>
      )}
      <AlertMessage open={!!error} onClose={() => setError("")} severity="error" message={error} />
    </Box>
  );
};

export default VideoUploadForm;
