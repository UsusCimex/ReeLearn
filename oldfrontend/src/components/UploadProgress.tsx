import React from 'react';
import { FiUploadCloud, FiCpu, FiCheck } from 'react-icons/fi';
import '../styles/upload_progress.css';

interface upload_progressProps {
  upload_progress: number;
  processingProgress: number;
  current_operation: string;
  status: 'uploading' | 'processing' | 'completed' | 'error';
  error?: string;
}

const upload_progress: React.FC<upload_progressProps> = ({
  upload_progress,
  processingProgress,
  current_operation,
  status,
  error
}) => {
  const getStatusIcon = () => {
    switch (status) {
      case 'uploading':
        return <FiUploadCloud className="status-icon uploading" />;
      case 'processing':
        return <FiCpu className="status-icon processing" />;
      case 'completed':
        return <FiCheck className="status-icon completed" />;
      default:
        return null;
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'uploading':
        return 'Uploading video...';
      case 'processing':
        return current_operation || 'Processing video...';
      case 'completed':
        return 'Upload completed!';
      case 'error':
        return error || 'Upload Failed';
      default:
        return 'Preparing...';
    }
  };

  const progress = status === 'uploading' ? upload_progress : status === 'completed' ? 100 : status === 'error' ? 0 : processingProgress;

  return (
    <div className={`upload-progress-container ${status}`}>
      <div className="progress-header">
        {getStatusIcon()}
        <h3>{getStatusText()}</h3>
      </div>
      
      <div className="progress-bar-container">
        <div 
          className="progress-bar"
          style={{ width: `${progress}%` }}
        />
      </div>
      
      <div className="progress-status">
        <span>{Math.round(progress)}%</span>
        <span>{status === 'uploading' ? 'Uploading' : status === 'processing' ? 'Processing' : ''}</span>
      </div>
    </div>
  );
};

export default upload_progress;
