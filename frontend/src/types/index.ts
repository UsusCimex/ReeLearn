// Frontend types
// API Response Types
export interface videoMetadata {
  video_name: string;
  video_description: string;
  tags: string[];
}

export interface videoFragment {
  id: number;
  video_id: string;
  video_name: string;
  timecode_start: number;
  timecode_end: number;
  text: string;
  s3_url: string;
  tags: string[];
  score: number;
}

export interface videoFragmentsResponse {
  video_id: number;
  fragments: videoFragment[];
}

export interface videoInfo {
  id: number;
  name: string;
  status: string;
  fragments_count: number;
}

export interface videoListResponse {
  videos: videoInfo[];
}

// Type guard for VideoFragment
export const isVideoFragment = (obj: any): obj is videoFragment => {
  return (
    obj !== null &&
    typeof obj === 'object' &&
    typeof obj.id === 'number' &&
    typeof obj.video_id === 'string' &&
    typeof obj.video_name === 'string' &&
    typeof obj.timecode_start === 'number' &&
    typeof obj.timecode_end === 'number' &&
    typeof obj.text === 'string' &&
    typeof obj.s3_url === 'string' &&
    Array.isArray(obj.tags) &&
    typeof obj.score === 'number'
  );
};

// Status types
export enum taskStatus {
  PENDING = 'pending',
  PROGRESS = 'progress',
  COMPLETED = 'completed',
  FAILED = 'failed'
}

export enum uploadStatus {
  UPLOADING = 'uploading',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed'
}

export enum searchStatus {
  PENDING = 'pending',
  PROGRESS = 'progress',
  COMPLETED = 'completed',
  FAILED = 'failed'
}

// Task response types
export interface taskResponse {
  task_id: string;
}

export interface taskStatusResponse {
  status: taskStatus;
  progress: number;
  current_operation: string;
  result?: any;
  error?: string;
}

export interface searchResult {
  video_id: string;
  name: string;
  status: string;
  fragments_count: number;
}

export interface searchResponse {
  status: searchStatus;
  results: searchResult[];
  error?: string;
  task_id: string;
}

export interface uploadResponse {
  video_id: string;
  task_id: string;
  status: uploadStatus;
}

// Component Props types
export interface searchResultsProps {
  on_video_select: (video_id: string) => void;
  status: searchStatus;
  results?: searchResult[];
}

// Frontend state types
export interface uploadState {
  status: uploadStatus;
  upload_progress?: number;
  processing_progress?: number;
  current_operation?: string;
  error?: string;
  video_id?: string;
  fragments_count?: number;
}

export interface notificationState {
  id: string;
  message: string;
  type: 'info' | 'success' | 'error';
  progress?: number;
}

export interface videoState {
  id: number;
  name: string;
  status: string;
}

// Progress callback type
export type progressCallback = (progress: number) => void;

// Upload task result type
export interface uploadTaskResult {
  type: 'upload';
  video_id: number;
  fragments_count: number;
}

// Upload notification props
export interface uploadNotificationProps {
  upload_progress: number;
  processing_progress: number;
  status: uploadStatus;
  current_operation: string;
  error?: string;
  fragments_count?: number;
  on_close: () => void;
  on_video_click?: () => void;
}
