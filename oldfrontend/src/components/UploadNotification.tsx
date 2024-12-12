import React from 'react';
import { uploadState, uploadStatus } from '../types';
import '../styles/UploadNotification.css';

interface UploadNotificationProps {
  notification_state: uploadState;
  on_close: () => void;
  on_video_click?: (video_id: number) => void;
}

const UploadNotification: React.FC<UploadNotificationProps> = ({
  notification_state,
  on_close,
  on_video_click
}) => {
  const get_progress_text = () => {
    if (notification_state.status === uploadStatus.UPLOADING) {
      return `Uploading: ${Math.round(notification_state.upload_progress || 0)}%`;
    } else if (notification_state.status === uploadStatus.PROCESSING) {
      return `Processing: ${Math.round(notification_state.processing_progress || 0)}%`;
    }
    return notification_state.current_operation || '';
  };

  const get_status_icon = () => {
    switch (notification_state.status) {
      case uploadStatus.UPLOADING:
      case uploadStatus.PROCESSING:
        return 'hourglass_empty';
      case uploadStatus.COMPLETED:
        return 'check_circle';
      case uploadStatus.FAILED:
        return 'error';
      default:
        return 'info';
    }
  };

  const handle_click = () => {
    if (notification_state.status === uploadStatus.COMPLETED && notification_state.video_id && on_video_click) {
      on_video_click(Number(notification_state.video_id));
    }
  };

  return (
    <div 
      className={`upload-notification ${notification_state.status.toLowerCase()}`}
      onClick={handle_click}
      style={{ cursor: notification_state.status === uploadStatus.COMPLETED ? 'pointer' : 'default' }}
    >
      <div className="notification-content">
        <span className="material-icons status-icon">{get_status_icon()}</span>
        <div className="notification-details">
          <div className="notification-header">
            <span className="notification-title">
              {notification_state.status === uploadStatus.COMPLETED 
                ? `Upload Complete${notification_state.fragments_count ? ` (${notification_state.fragments_count} fragments)` : ''}`
                : notification_state.status === uploadStatus.FAILED 
                ? 'Upload Failed'
                : 'Video Upload'}
            </span>
            <button className="close-button" onClick={(e) => { e.stopPropagation(); on_close(); }}>
              <span className="material-icons">close</span>
            </button>
          </div>
          <div className="notification-message">
            {notification_state.status === uploadStatus.FAILED ? notification_state.error : get_progress_text()}
          </div>
          {(notification_state.status === uploadStatus.UPLOADING || notification_state.status === uploadStatus.PROCESSING) && (
            <div className="progress-bar">
              <div 
                className="progress-fill"
                style={{ 
                  width: `${notification_state.status === uploadStatus.UPLOADING 
                    ? notification_state.upload_progress 
                    : notification_state.processing_progress}%`
                }}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default UploadNotification;
