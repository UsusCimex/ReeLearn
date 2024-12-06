export interface TaskResponse {
    task_id: string;
}

export interface TaskStatusResponse {
    status: 'pending' | 'processing' | 'completed' | 'failed';
    progress: number;
    current_operation?: string;
    error?: string;
    result?: any;
}

export interface SearchResult {
    video_name: string;
    video_description: string;
    text: string;
    tags: string[];
    timecode_start: number;
    timecode_end: number;
    presigned_url: string;
}

export interface VideoMetadata {
    name: string;
    description: string;
    tags?: string[];
}
