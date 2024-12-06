import axios, { AxiosError } from 'axios';
import { 
    TaskResponse, 
    TaskStatusResponse, 
    VideoFragmentsResponse, 
    UploadResponse 
} from '../types';

const API_BASE_URL = 'http://localhost:8000';
const API_PREFIX = '/api/v1';

const api = axios.create({
    baseURL: `${API_BASE_URL}${API_PREFIX}`,
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

export const uploadVideo = async (formData: FormData): Promise<UploadResponse> => {
    try {
        const response = await api.post<UploadResponse>('/upload', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
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

export const getTaskStatus = async (taskId: string): Promise<TaskStatusResponse> => {
    try {
        const response = await api.get<TaskStatusResponse>(`/tasks/${taskId}`);
        return response.data;
    } catch (error) {
        if (axios.isAxiosError(error) && error.response?.status === 404) {
            return {
                status: 'pending',
                progress: 0,
                current_operation: 'Task queued'
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
