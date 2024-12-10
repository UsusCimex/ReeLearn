import axios from 'axios';
import { api_url } from './config';
import { 
  videoInfo, 
  videoFragment,
  videoFragmentsResponse,
  videoListResponse,
  searchResponse,
  taskStatusResponse,
  uploadResponse,
  progressCallback,
  taskStatus,
  uploadStatus,
  searchStatus,
} from '../types';

const api = axios.create({
  baseURL: api_url,
  transformResponse: [(data) => {
    const parsedData = typeof data === 'string' ? JSON.parse(data) : data;
    return transformResponse(parsedData);
  }]
});

// Helper function to transform snake_case to camelCase
const toCamelCase = (str: string): string => {
  return str.replace(/_([a-z])/g, (g) => g[1].toUpperCase());
};

// Helper function to transform response data
const transformResponse = (data: any): any => {
  if (!data || typeof data !== 'object') return data;
  
  if (Array.isArray(data)) {
    return data.map(transformResponse);
  }

  const transformed = Object.entries(data).reduce((acc: Record<string, any>, [key, value]) => {
    const camelKey = toCamelCase(key);
    
    // Transform status fields to match our enums
    if (camelKey === 'status' && typeof value === 'string') {
      if (Object.values(taskStatus).includes(value as taskStatus)) {
        acc[camelKey] = value as taskStatus;
      } else if (Object.values(uploadStatus).includes(value as uploadStatus)) {
        acc[camelKey] = value as uploadStatus;
      } else if (Object.values(searchStatus).includes(value as searchStatus)) {
        acc[camelKey] = value as searchStatus;
      } else {
        acc[camelKey] = value;
      }
    } else if (typeof value === 'object') {
      acc[camelKey] = transformResponse(value);
    } else {
      acc[camelKey] = value;
    }
    
    return acc;
  }, {});

  return transformed;
};

// Функция для проверки статуса задачи
export const checkTaskStatus = async (taskId: string): Promise<taskStatusResponse> => {
  try {
    const response = await api.get<taskStatusResponse>(`/tasks/${taskId}`);
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

// Функция для загрузки видео
export const uploadVideo = async (
  file: File,
  onProgress?: progressCallback
): Promise<uploadResponse> => {
  try {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post<uploadResponse>('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
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

// Функция для поиска видео
export const searchVideos = async (query: string): Promise<searchResponse> => {
  try {
    const response = await api.post<searchResponse>('/search', { query });
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(error.response?.data?.detail || 'Failed to search videos');
    }
    throw error;
  }
};

// Функция для получения списка видео
export const getVideoList = async (): Promise<videoListResponse> => {
  try {
    const response = await api.get('/videos');
    return response.data;
  } catch (error) {
    throw new Error('Failed to fetch video list');
  }
};

// Функция для получения информации о видео
export const getVideoById = async (videoId: number): Promise<videoInfo> => {
  try {
    const response = await api.get(`/videos/${videoId}`);
    return response.data;
  } catch (error) {
    throw new Error('Failed to fetch video info');
  }
};

// Функция для получения фрагментов видео
export const getVideoFragments = async (videoId: number): Promise<videoFragmentsResponse> => {
  try {
    const response = await api.get(`/videos/${videoId}/fragments`);
    return response.data;
  } catch (error) {
    throw new Error('Failed to fetch video fragments');
  }
};
