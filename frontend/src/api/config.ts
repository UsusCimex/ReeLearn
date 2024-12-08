import axios, { AxiosError } from 'axios';
import { 
    TaskResponse, 
    TaskStatus, 
    VideoFragmentsResponse, 
    UploadResponse 
} from '../types';

// API URL для разработки
export const API_URL = `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/v1`;

// Максимальный размер загружаемого файла (в байтах)
export const MAX_FILE_SIZE = 500 * 1024 * 1024; // 500MB

// Поддерживаемые форматы видео
export const SUPPORTED_VIDEO_FORMATS = [
  'video/mp4',
  'video/webm',
  'video/ogg'
];

// Таймаут для запросов (в миллисекундах)
export const REQUEST_TIMEOUT = 30000; // 30 секунд

const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Общая функция обработки ошибок
const handleApiError = (error: unknown, defaultMessage: string): never => {
    if (axios.isAxiosError(error)) {
        const axiosError = error as AxiosError<{ detail: string }>;
        throw new Error(axiosError.response?.data?.detail || defaultMessage);
    }
    throw new Error(defaultMessage);
};

export const uploadVideo = async (formData: FormData, onProgress?: (progress: number) => void): Promise<UploadResponse> => {
    try {
        const response = await api.post<UploadResponse>('/upload', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
            onUploadProgress: (progressEvent) => {
                if (progressEvent.total && onProgress) {
                    const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                    onProgress(progress);
                }
            },
        });
        return response.data;
    } catch (error) {
        throw handleApiError(error, 'Failed to upload video');
    }
};

export const searchVideos = async (
    query: string, 
    exact: boolean = false, 
    tags?: string[]
): Promise<TaskResponse> => {
    try {
        const response = await api.get<TaskResponse>('/search', {
            params: { query, exact, tags },
        });
        return response.data;
    } catch (error) {
        throw handleApiError(error, 'Failed to search videos');
    }
};

export const getTaskStatus = async (taskId: string): Promise<TaskStatus> => {
    try {
        const response = await axios.get<TaskStatus>(`${API_URL}/task/${taskId}/status`);
        return response.data;
    } catch (error) {
        if (axios.isAxiosError(error) && error.response?.status === 404) {
            return {
                status: 'pending',
                progress: 0,
                current_operation: 'Task queued',
                error: undefined
            };
        }
        throw handleApiError(error, 'Failed to get task status');
    }
};

export const getVideoFragments = async (videoId: number): Promise<VideoFragmentsResponse> => {
    try {
        const response = await api.get<VideoFragmentsResponse>(`/videos/${videoId}/fragments`);
        return response.data;
    } catch (error) {
        throw handleApiError(error, 'Failed to get video fragments');
    }
};

export default api;
