import axios, { AxiosError } from 'axios';
import { 
    taskResponse, 
    taskStatus, 
    videoFragmentsResponse, 
    uploadResponse,
    taskStatusResponse
} from '../types';

// API URL для разработки
export const api_url = 'http://localhost:8000/api/v1';

// Максимальный размер загружаемого файла (в байтах)
export const max_file_size = 500 * 1024 * 1024; // 500MB

// Поддерживаемые форматы видео
export const supported_video_formats = [
  'video/mp4',
  'video/webm',
  'video/ogg',
  'video/quicktime' // Added support for .mov files
];

// Таймаут для запросов (в миллисекундах)
export const request_timeout = 60000; // Increased to 60 seconds for large uploads

// Retry configuration
export const retry_config = {
  retries: 3,
  initial_delay_ms: 1000,
  max_delay_ms: 5000
};

const api = axios.create({
    baseURL: api_url,
    timeout: request_timeout,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Interceptor for handling request timeouts
api.interceptors.response.use(
    response => response,
    error => {
        if (error.code === 'ECONNABORTED') {
            throw new Error('Request timed out. Please try again.');
        }
        return Promise.reject(error);
    }
);

// Общая функция обработки ошибок
const handle_api_error = (error: unknown, default_message: string): never => {
    if (axios.isAxiosError(error)) {
        const axios_error = error as AxiosError<{ detail: string }>;
        throw new Error(axios_error.response?.data?.detail || default_message);
    }
    throw new Error(default_message);
};

export const upload_video = async (form_data: FormData, on_progress?: (progress: number) => void): Promise<uploadResponse> => {
    try {
        const response = await api.post<uploadResponse>('/upload', form_data, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
            onUploadProgress: (progress_event) => {
                if (progress_event.total && on_progress) {
                    const progress = Math.round((progress_event.loaded * 100) / progress_event.total);
                    on_progress(progress);
                }
            },
        });
        return response.data;
    } catch (error) {
        throw handle_api_error(error, 'Failed to upload video');
    }
};

export const search_videos = async (
    query: string, 
    exact: boolean = false, 
    tags?: string[]
): Promise<taskResponse> => {
    try {
        const response = await api.get<taskResponse>('/search', {
            params: { query, exact, tags },
        });
        return response.data;
    } catch (error) {
        throw handle_api_error(error, 'Failed to search videos');
    }
};

export const get_task_status = async (task_id: string): Promise<taskStatusResponse> => {
    try {
        const response = await axios.get(`${api_url}/tasks/${task_id}/status`);
        return response.data;
    } catch (error) {
        if (axios.isAxiosError(error) && error.response?.status === 404) {
            return {
                status: taskStatus.PENDING,
                progress: 0,
                current_operation: 'Task queued',
                error: undefined
            };
        }
        throw handle_api_error(error, 'Failed to get task status');
    }
};

// eslint-disable-next-line @typescript-eslint/no-unused-vars
const get_initial_task_status = (task_id: string): taskStatusResponse => {
    return {
        status: taskStatus.PENDING,
        progress: 0,
        current_operation: 'Task queued',
        error: undefined
    };
};

export const get_video_fragments = async (video_id: number): Promise<videoFragmentsResponse> => {
    try {
        const response = await api.get<videoFragmentsResponse>(`/videos/${video_id}/fragments`);
        return response.data;
    } catch (error) {
        throw handle_api_error(error, 'Failed to get video fragments');
    }
};

export default api;
