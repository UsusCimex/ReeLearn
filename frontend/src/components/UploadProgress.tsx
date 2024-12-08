import React from 'react';
import { FiUploadCloud, FiCpu, FiCheck } from 'react-icons/fi';
import '../styles/UploadProgress.css';

interface UploadProgressProps {
  uploadProgress: number;
  processingProgress: number;
  currentOperation: string;
  status: 'uploading' | 'processing' | 'completed' | 'error';
  error?: string;
}

const UploadProgress: React.FC<UploadProgressProps> = ({
  uploadProgress,
  processingProgress,
  currentOperation,
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
        return currentOperation || 'Processing video...';
      case 'completed':
        return 'Upload completed!';
      case 'error':
        return error || 'Upload Failed';
      default:
        return 'Preparing...';
    }
  };

  const progress = status === 'uploading' ? uploadProgress : status === 'completed' ? 100 : status === 'error' ? 0 : processingProgress;

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

export default UploadProgress;
