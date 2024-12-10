import { taskStatus, taskStatusResponse, videoFragment } from './index';

export function isTaskStatusResponse(obj: any): obj is taskStatusResponse {
  return (
    obj !== null &&
    typeof obj === 'object' &&
    Object.values(taskStatus).includes(obj.status) &&
    typeof obj.progress === 'number' &&
    typeof obj.current_operation === 'string' &&
    (obj.error === undefined || typeof obj.error === 'string')
  );
}

export function isVideoFragment(obj: any): obj is videoFragment {
  return (
    obj !== null &&
    typeof obj === 'object' &&
    typeof obj.fragment_id === 'number' &&
    typeof obj.video_id === 'number' &&
    typeof obj.timecode_start === 'number' &&
    typeof obj.timecode_end === 'number' &&
    (obj.text === undefined || typeof obj.text === 'string') &&
    typeof obj.s3_url === 'string' &&
    (obj.tags === undefined || Array.isArray(obj.tags))
  );
}
