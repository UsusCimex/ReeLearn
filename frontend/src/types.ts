export interface SearchResult {
    video_name: string;
    video_description: string;
    text: string;
    tags?: string[];
    presigned_url: string;
    timecode_start: number;
    timecode_end: number;
}

export interface SearchResultResponse {
    status: 'success' | 'error';
    results: SearchResult[];
    reason: string | null;
}

export interface VideoMetadata {
    name: string;
    description: string;
    tags: string[];
}

export interface TaskResponse {
    task_id: string;
}

export interface FragmentInfo {
    id: number;
    timecode_start: number;
    timecode_end: number;
    text: string;
    s3_url: string;
    tags: string[];
}

export interface VideoFragmentsResponse {
    video_id: number;
    fragments: FragmentInfo[];
}

export interface TaskStatusResponse {
    status: 'pending' | 'processing' | 'completed' | 'failed';
    progress: number;
    current_operation: string | null;
    result?: SearchResultResponse | null;
    error?: string | null;
}

export interface UploadResponse {
    task_id: string;
}
