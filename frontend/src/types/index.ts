// Frontend types (camelCase)
export interface TaskResponse {
  taskId: string;
}

export interface VideoMetadata {
  videoName: string;
  videoDescription: string;
  tags: string[];
}

export interface SearchResult extends VideoMetadata {
  timecodeStart: number;
  timecodeEnd?: number;
  text?: string;
  confidence?: number;
  presignedUrl?: string;
}

export interface TaskStatusResponse {
  status: 'pending' | 'processing' | 'completed' | 'failed';
  result?: SearchResult[];
  error?: string;
  progress?: number;
}

export interface UploadResponse {
  taskId: string;
  status: string;
  message?: string;
}

export interface AxiosUploadProgress {
  loaded: number;
  total?: number;
  progress?: number;
  bytes: number;
  rate?: number;
  estimated?: number;
  upload: true;
}
