import axios from 'axios';
import { API_URL } from './config';
import { TaskResult, TaskStatus, UploadResponse } from '../types';

const api = axios.create({
  baseURL: API_URL
});

// Функция для загрузки видео
export const uploadVideo = async (
  formData: FormData, 
  onProgress?: (progress: number) => void
): Promise<UploadResponse> => {
  try {
    const response = await api.post<UploadResponse>('/videos/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && onProgress) {
          const progress = (progressEvent.loaded / progressEvent.total) * 100;
          onProgress(progress);
        }
      },
    });
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(error.response?.data?.detail || 'Failed to upload video');
    }
    throw error;
  }
};

export const checkTaskStatus = async (taskId: string): Promise<TaskStatus> => {
  try {
    const response = await axios.get<TaskStatus>(`${API_URL}/tasks/${taskId}`);
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(error.response?.data?.detail || 'Failed to check task status');
    }
    throw error;
  }
};

// Алиас для обратной совместимости
export const getTaskStatus = checkTaskStatus;

export const searchVideos = async (
  query: string,
  exact: boolean = false,
  tags?: string[]
): Promise<any> => {
  const params = new URLSearchParams({
    query: query,
    exact: exact.toString()
  });
  
  if (tags && tags.length > 0) {
    tags.forEach(tag => params.append('tags', tag));
  }

  try {
    const response = await api.get('/search', { params });
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(error.response?.data?.message || 'Error searching videos');
    }
    throw error;
  }
};

export const getVideoList = async () => {
  try {
    const response = await api.get('/videos');
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(error.response?.data?.message || 'Error fetching video list');
    }
    throw error;
  }
};

export const getVideoById = async (videoId: string) => {
  try {
    const response = await api.get(`/videos/${videoId}`);
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(error.response?.data?.message || 'Error fetching video');
    }
    throw error;
  }
};

export const getVideoFragments = async (videoId: string) => {
  try {
    const response = await api.get(`/videos/${videoId}/fragments`);
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(error.response?.data?.detail || 'Failed to fetch video fragments');
    }
    throw error;
  }
};
