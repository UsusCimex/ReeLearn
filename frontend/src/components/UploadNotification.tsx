import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import '../styles/UploadNotification.css';
import { UploadNotificationProps } from '../types';

const UploadNotification: React.FC<UploadNotificationProps> = ({
  uploadProgress,
  processingProgress,
  currentOperation,
  status,
  error,
  fragmentCount,
  videoName,
  videoId,
  onClose,
  onClick
}) => {
  const navigate = useNavigate();

  useEffect(() => {
    let timeoutId: NodeJS.Timeout;
    if (status === 'completed') {
      timeoutId = setTimeout(() => {
        onClose();
      }, 10000); // 10 seconds
    }
    return () => {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  }, [status, onClose]);

  const getStatusMessage = () => {
    switch (status) {
      case 'uploading':
        return `Uploading ${videoName}...`;
      case 'processing':
        return `Processing ${videoName}...`;
      case 'completed':
        return `${videoName} uploaded! Found ${fragmentCount} fragments`;
      case 'failed':
        return `Error uploading ${videoName}: ${error || 'Unknown error occurred'}`;
      default:
        return currentOperation || 'Unknown status';
    }
  };

  const handleClick = () => {
    if (status === 'completed' && videoId) {
      navigate(`/videos/${videoId}/fragments`);
    }
  };

  const progress = status === 'uploading' ? uploadProgress : processingProgress;

  return (
    <div
      className={`upload-notification ${status} ${status === 'completed' ? 'clickable' : ''}`}
      onClick={status === 'completed' ? handleClick : undefined}
    >
      <button className="close-button" onClick={(e) => { e.stopPropagation(); onClose(); }}>×</button>
      <div className="title">{getStatusMessage()}</div>
      <div className="progress-container">
        <div className="progress-bar">
          <div className="progress-fill" style={{ width: `${progress}%` }} />
        </div>
      </div>
      {currentOperation && status !== 'completed' && (
        <div className="operation">{currentOperation}</div>
      )}
      {status === 'completed' && (
        <div className="operation">Click to view fragments (notification will close in 10s)</div>
      )}
    </div>
  );
};

export default UploadNotification;
