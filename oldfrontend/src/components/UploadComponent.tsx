import React, { useState } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { uploadVideo } from '../api/api';
import { uploadState, uploadStatus, taskStatus } from '../types';
import '../styles/UploadComponent.css';

interface UploadComponentProps {
  onUploadStateChange: (state: Partial<uploadState>, notificationId: string) => void;
  onUploadComplete?: (video_id: string) => void;
}

const UploadComponent: React.FC<UploadComponentProps> = ({ 
  onUploadStateChange, 
  onUploadComplete 
}) => {
  const [isDragging, setIsDragging] = useState(false);

  const handleFileUpload = async (file: File) => {
    const notificationId = uuidv4();

    // Initial state - starting upload
    onUploadStateChange({
      status: uploadStatus.UPLOADING,
      upload_progress: 0,
      current_operation: 'Starting upload...'
    }, notificationId);

    try {
      const result = await uploadVideo(
        file,
        // Upload progress callback
        (upload_progress) => {
          onUploadStateChange({
            status: uploadStatus.UPLOADING,
            upload_progress,
            current_operation: 'Uploading...'
          }, notificationId);
        }
      );

      // Handle task status updates
      if (result.status === uploadStatus.COMPLETED && result.video_id) {
        onUploadStateChange({
          status: uploadStatus.COMPLETED,
          upload_progress: 100,
          current_operation: 'Upload completed'
        }, notificationId);

        if (onUploadComplete) {
          onUploadComplete(result.video_id);
        }
      } else if (result.status === uploadStatus.FAILED) {
        onUploadStateChange({
          status: uploadStatus.FAILED,
          error: 'Upload failed',
          current_operation: 'Upload failed'
        }, notificationId);
      }
    } catch (error) {
      onUploadStateChange({
        status: uploadStatus.FAILED,
        error: error instanceof Error ? error.message : 'Upload failed',
        current_operation: 'Upload failed'
      }, notificationId);
    }
  };

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      const videoFile = files[0];
      if (videoFile.type.startsWith('video/')) {
        await handleFileUpload(videoFile);
      } else {
        alert('Please upload a video file');
      }
    }
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      const videoFile = files[0];
      if (videoFile.type.startsWith('video/')) {
        await handleFileUpload(videoFile);
      } else {
        alert('Please upload a video file');
      }
    }
  };

  return (
    <div className="upload-component">
      <div
        className={`upload-area ${isDragging ? 'dragging' : ''}`}
        onDragEnter={handleDragEnter}
        onDragOver={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <input
          type="file"
          accept="video/*"
          onChange={handleFileSelect}
          className="file-input"
          id="file-input"
        />
        <label htmlFor="file-input" className="upload-label">
          <div className="upload-icon">📁</div>
          <div className="upload-text">
            {isDragging
              ? 'Drop video here'
              : 'Drag & drop video or click to upload'}
          </div>
        </label>
      </div>
    </div>
  );
};

export default UploadComponent;
