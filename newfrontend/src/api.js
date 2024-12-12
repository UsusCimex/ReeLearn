import axios from 'axios';

// Базовый клиент
const api = axios.create({
  baseURL: 'http://localhost:8000', // здесь указать реальный backend host
});

export const searchVideos = async ({query, exact = false, tags = []}) => {
  const params = { query, exact };
  if (tags.length > 0) params.tags = tags;
  const response = await api.get('/api/v1/search', { params });
  return response.data;
};

export const getVideos = async () => {
  const response = await api.get('/api/v1/videos');
  return response.data;
};

export const getVideoFragments = async (videoId) => {
  const response = await api.get(`/api/v1/videos/${videoId}/fragments`);
  return response.data;
};

export const uploadVideo = async (formData) => {
  const response = await api.post('/api/v1/videos/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return response.data;
};

export const getTaskStatus = async (taskId) => {
  const response = await api.get(`/api/v1/tasks/${taskId}`);
  return response.data;
};
