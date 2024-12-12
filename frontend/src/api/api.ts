import axios, { AxiosError } from 'axios';
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

// Create axios instance with base configuration
const api = axios.create({
  baseURL: api_url,
  timeout: 30000, // 30 second timeout
});

// Add response transformation interceptor
api.interceptors.response.use(
  (response) => {
    if (response.data) {
      return {
        ...response,
        data: transformResponse(response.data)
      };
    }
    return response;
  },
  (error: AxiosError) => {
    if (error.response?.status === 503) {
      // Service Unavailable - likely a Celery task not ready
      return Promise.reject({
        status: taskStatus.PENDING,
        message: 'Task is still processing'
      });
    }
    return Promise.reject(error);
  }
);

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

// Task polling configuration
const POLL_INTERVAL = 2000; // 2 seconds
const MAX_POLL_ATTEMPTS = 30; // 1 minute maximum polling time

// Generic task polling function
const pollTaskStatus = async (
  taskId: string,
  onProgress?: (status: taskStatusResponse) => void
): Promise<taskStatusResponse> => {
  let attempts = 0;

  const poll = async (): Promise<taskStatusResponse> => {
    try {
      const response = await api.get<taskStatusResponse>(`/tasks/${taskId}`);
      const status = response.data;

      if (onProgress) {
        onProgress(status);
      }

      if (status.status === taskStatus.COMPLETED || status.status === taskStatus.FAILED) {
        return status;
      }

      if (++attempts >= MAX_POLL_ATTEMPTS) {
        throw new Error('Task polling timeout exceeded');
      }

      await new Promise(resolve => setTimeout(resolve, POLL_INTERVAL));
      return poll();
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(error.response?.data?.detail || 'Task status check failed');
      }
      throw error;
    }
  };

  return poll();
};

// Upload video with progress tracking
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

// Search videos with task polling
export const searchVideos = async (
  query: string
): Promise<searchResponse> => {
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

// Synchronous operations
export const getVideoList = async (): Promise<videoListResponse> => {
  try {
    const response = await api.get<videoListResponse>('/videos');
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(error.response?.data?.detail || 'Failed to fetch video list');
    }
    throw error;
  }
};

export const getVideoById = async (video_id: number): Promise<videoInfo> => {
  try {
    const response = await api.get<videoInfo>(`/videos/${video_id}`);
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(error.response?.data?.detail || 'Failed to fetch video info');
    }
    throw error;
  }
};

export const getVideoFragments = async (video_id: number): Promise<videoFragmentsResponse> => {
  try {
    const response = await api.get<videoFragmentsResponse>(`/videos/${video_id}/fragments`);
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(error.response?.data?.detail || 'Failed to fetch video fragments');
    }
    throw error;
  }
};
