import React from 'react';
import { taskStatusResponse, uploadState, uploadTaskResult, uploadStatus, taskStatus } from '../types';
import '../styles/NotificationManager.css';
import { get_task_status } from '../api/config';

interface notification_manager_props {
  task_id: string;
  notification_id: string;
  on_state_change: (state: Partial<uploadState>, notification_id: string) => void;
  on_complete?: (video_id: string) => void;
  interval?: number;
}

export const NotificationManager: React.FC<notification_manager_props> = ({
  task_id,
  notification_id,
  on_state_change,
  on_complete,
  interval = 2000
}) => {
  const check_status = async (): Promise<boolean> => {
    try {
      const status: taskStatusResponse = await get_task_status(task_id);

      if (status.status === taskStatus.COMPLETED) {
        if (status.result && 'type' in status.result && status.result.type === 'upload') {
          const upload_result = status.result as uploadTaskResult;
          on_state_change({
            status: uploadStatus.COMPLETED,
            upload_progress: 100,
            processing_progress: 100,
            current_operation: 'Processing complete',
            fragments_count: upload_result.fragments_count,
            video_id: upload_result.video_id.toString()
          }, notification_id);

          if (upload_result.video_id && on_complete) {
            on_complete(upload_result.video_id.toString());
          }
          return true; // Status check complete
        }
      } else if (status.status === taskStatus.PROGRESS) {
        on_state_change({
          status: uploadStatus.PROCESSING,
          processing_progress: status.progress ? status.progress * 100 : 0,
          current_operation: status.current_operation
        }, notification_id);
        return false; // Continue checking
      } else if (status.status === taskStatus.FAILED) {
        on_state_change({
          status: uploadStatus.FAILED,
          error: status.error || 'Processing failed'
        }, notification_id);
        return true; // Status check complete with error
      }

      // Continue checking for other statuses
      return false;
    } catch (error) {
      console.error('Error checking task status:', error);
      on_state_change({
        status: uploadStatus.FAILED,
        error: error instanceof Error ? error.message : 'Failed to check status'
      }, notification_id);
      return true; // Status check complete with error
    }
  };

  const start_checking = async () => {
    const is_complete = await check_status();
    if (!is_complete) {
      setTimeout(start_checking, interval);
    }
  };

  // Start checking status when component mounts
  React.useEffect(() => {
    start_checking();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [task_id]);

  return null;
};

export default NotificationManager;
