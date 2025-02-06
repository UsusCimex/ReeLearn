import axios from "axios";

const API_BASE = process.env.REACT_APP_API_BASE || "http://localhost:8000/api/v1";

export const searchVideos = async (query, exact) => {
  const res = await axios.get(`${API_BASE}/search`, { params: { query, exact } });
  return res.data;
};

export const uploadVideo = async (file, name, description) => {
  const formData = new FormData();
  formData.append("video_file", file);
  formData.append("name", name);
  formData.append("description", description);
  const res = await axios.post(`${API_BASE}/videos/upload`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
};

export const getVideoFragments = async (videoId) => {
  const res = await axios.get(`${API_BASE}/videos/${videoId}/fragments`);
  return res.data;
};

export const getVideos = async () => {
  const res = await axios.get(`${API_BASE}/videos`);
  return res.data;
};

export const getTaskStatus = async (taskId) => {
  const res = await axios.get(`${API_BASE}/tasks/${taskId}`);
  return res.data;
};
