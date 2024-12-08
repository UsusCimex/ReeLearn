export interface SearchResult {
  video_id: string;
  title: string;
  description: string;
  text: string;
  presigned_url: string;
  confidence?: number;
  timecode_start: number;
  timecode_end: number;
  tags?: string[];
}

export interface SearchResultResponse {
  status: 'success' | 'error';
  results: SearchResult[];
  reason: string | null;
}

export interface VideoMetadata {
  title: string;
  description: string;
  tags: string[];
}

export interface TaskResponse {
  task_id: string;
}

export interface BaseTaskResult {
  type: string;
}

export interface UploadTaskResult extends BaseTaskResult {
  type: 'upload';
  video_id: number;
  fragments_count: number;
}

export interface SearchTaskResult extends BaseTaskResult {
  type: 'search';
  timestamp: number;
  text: string;
  similarity: number;
}

export type TaskResult = UploadTaskResult | SearchTaskResult;

export interface TaskStatus {
  status: 'pending' | 'progress' | 'completed' | 'failed';
  progress: number;
  current_operation: string;
  error?: string;
  result?: {
    status: 'success' | 'error';
    video_id: number;
    fragments_count: number;
  };
}

export type TaskStatusResponse = TaskStatus;

export interface UploadResponse {
  task_id: string;
}

export interface UploadStateBase {
  uploadProgress: number;
  processingProgress: number;
  currentOperation: string;
  status: 'uploading' | 'processing' | 'completed' | 'failed' | 'error';
  error?: string;
  videoName: string;
}

export interface UploadState extends UploadStateBase {
  videoId?: string;
  fragmentCount: number;
}

export interface UploadNotificationItem extends UploadState {
  id: string;
  timestamp: number;
}

export interface UploadNotificationProps {
  uploadProgress: number;
  processingProgress: number;
  currentOperation: string;
  status: 'uploading' | 'processing' | 'completed' | 'failed' | 'error';
  error?: string;
  fragmentCount: number;
  videoName: string;
  videoId?: string;
  onClose: () => void;
  onClick?: () => void;
}

export interface VideoFragment {
  id: number;
  timecode_start: number;
  timecode_end: number;
  text: string;
  s3_url: string;
  tags: string[];
}

export interface VideoFragmentsResponse {
  video_id: number;
  fragments: VideoFragment[];
}
