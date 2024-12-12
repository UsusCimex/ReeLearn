import React from 'react';
import { uploadState } from '../types';
import '../styles/NotificationsView.css';

interface NotificationsViewProps {
  notifications: { [key: string]: uploadState };
  onClose: (id: string) => void;
}

const NotificationsView: React.FC<NotificationsViewProps> = ({
  notifications,
  onClose
}) => {
  if (Object.keys(notifications).length === 0) {
    return null;
  }

  return (
    <div className="notifications-container">
      {Object.entries(notifications).map(([id, notification]) => (
        <div key={id} className={`notification ${notification.status}`}>
          <div className="notification-content">
            <div className="notification-header">
              <h4>Загрузка видео</h4>
              <button
                className="close-button"
                onClick={(e) => {
                  e.stopPropagation();
                  onClose(id);
                }}
              >
                ×
              </button>
            </div>
            <div className="notification-body">
              <div className="progress-info">
                <span className="operation">{notification.current_operation}</span>
                {notification.status === 'uploading' && (
                  <div className="progress-bar">
                    <div
                      className="progress-fill"
                      style={{ width: `${notification.upload_progress}%` }}
                    />
                  </div>
                )}
                {notification.status === 'processing' && (
                  <div className="progress-bar">
                    <div
                      className="progress-fill"
                      style={{ width: `${notification.processing_progress}%` }}
                    />
                  </div>
                )}
                {(notification.status === 'uploading' || notification.status === 'processing') && (
                  <span className="progress-text">
                    {notification.status === 'uploading'
                      ? `${notification.upload_progress}%`
                      : `${notification.upload_progress}%`}
                  </span>
                )}
              </div>
              {notification.error && (
                <div className="error-message">{notification.error}</div>
              )}
              {notification.status === 'completed' && notification.fragments_count !== undefined && (
                <div className="success-message">
                  Обработано фрагментов: {notification.fragments_count}
                </div>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default NotificationsView;
