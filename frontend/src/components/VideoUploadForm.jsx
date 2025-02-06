import React, { useState, useEffect } from "react";
import { Box, TextField, Button, LinearProgress, Typography } from "@mui/material";
import AlertMessage from "./AlertMessage";
import { uploadVideo, getTaskStatus, getVideos } from "../services/api";

const VideoUploadForm = () => {
  const [file, setFile] = useState(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [taskId, setTaskId] = useState("");
  const [progress, setProgress] = useState(0);
  const [videos, setVideos] = useState([]);
  const [error, setError] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) {
      setError("Please select a video file.");
      return;
    }
    try {
      const res = await uploadVideo(file, name, description);
      setTaskId(res.task_id);
      setSuccessMsg("Video upload started.");
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    }
  };

  useEffect(() => {
    let interval;
    if (taskId) {
      interval = setInterval(async () => {
        try {
          const status = await getTaskStatus(taskId);
          setProgress(status.progress);
          if (status.status === "completed" || status.status === "failed") {
            clearInterval(interval);
            const vids = await getVideos();
            setVideos(vids);
          }
        } catch (err) {
          setError(err.response?.data?.detail || err.message);
          clearInterval(interval);
        }
      }, 1000); // опрашиваем каждые 1 секунду
    }
    return () => clearInterval(interval);
  }, [taskId]);  

  return (
    <Box>
      <Box component="form" onSubmit={handleUpload} sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
        <Button variant="contained" component="label">
          Select Video File
          <input type="file" hidden accept="video/*" onChange={(e) => setFile(e.target.files[0])} />
        </Button>
        {file && <Typography variant="body2">{file.name}</Typography>}
        <TextField label="Video Name" value={name} onChange={(e) => setName(e.target.value)} required />
        <TextField label="Description" value={description} onChange={(e) => setDescription(e.target.value)} multiline rows={3} />
        <Button variant="contained" type="submit">
          Upload Video
        </Button>
      </Box>
      {taskId && (
        <Box sx={{ mt: 2 }}>
          <LinearProgress variant="determinate" value={progress} />
          <Typography variant="body2">Progress: {progress}%</Typography>
        </Box>
      )}
      <AlertMessage open={!!error} onClose={() => setError("")} severity="error" message={error} />
      <AlertMessage open={!!successMsg} onClose={() => setSuccessMsg("")} severity="success" message={successMsg} />
    </Box>
  );
};

export default VideoUploadForm;
