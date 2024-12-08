import React, { useState, useRef } from 'react';
import { uploadVideo, checkTaskStatus } from '../api/api';
import { UploadState } from '../types';
import UploadNotification from './UploadNotification';
import '../styles/UploadComponent.css';
import { FiUploadCloud } from 'react-icons/fi';

interface UploadComponentProps {
  onClose: () => void;
  onUploadComplete: (videoId: string) => void;
  onUploadStateChange: (state: Partial<UploadState>, notificationId?: string) => string;
}

const UploadComponent: React.FC<UploadComponentProps> = ({
  onClose,
  onUploadComplete,
  onUploadStateChange
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [metadata, setMetadata] = useState<{ title: string, description: string, tags: string[] }>({
    title: '',
    description: '',
    tags: []
  });
  const [isDragOver, setIsDragOver] = useState(false);
  const [showNotification, setShowNotification] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) {
      setSelectedFile(file);
      setMetadata(prev => ({
        ...prev,
        title: file.name.split('.')[0]
      }));
    }
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setMetadata(prev => ({
        ...prev,
        title: file.name.split('.')[0]
      }));
    }
  };

  const handleMetadataChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setMetadata(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleTagsChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const tags = e.target.value.split(',').map(tag => tag.trim()).filter(tag => tag);
    setMetadata(prev => ({
      ...prev,
      tags
    }));
  };

  const startUploadProcess = async () => {
    if (!selectedFile || isUploading) return;

    setIsUploading(true);
    const videoName = metadata.title || selectedFile.name;
    const notificationId = onUploadStateChange({
      status: 'uploading',
      uploadProgress: 0,
      processingProgress: 0,
      currentOperation: 'Starting upload...',
      videoName,
      error: undefined,
      fragmentCount: 0
    });

    const formData = new FormData();
    formData.append('video_file', selectedFile);
    formData.append('name', metadata.title);
    formData.append('description', metadata.description || '');
    formData.append('tags', JSON.stringify(metadata.tags));

    try {
      const uploadResponse = await uploadVideo(formData, (progress) => {
        onUploadStateChange({
          status: 'uploading',
          uploadProgress: progress,
          fragmentCount: 0,
          currentOperation: 'Uploading video...'
        }, notificationId);
      });

      onUploadStateChange({
        status: 'processing',
        uploadProgress: 100,
        processingProgress: 0,
        currentOperation: 'Starting video processing...',
        fragmentCount: 0
      }, notificationId);

      // Start polling for task status
      const pollInterval = setInterval(async () => {
        try {
          const taskStatus = await checkTaskStatus(uploadResponse.task_id);
          
          if (taskStatus.status === 'completed' && taskStatus.result) {
            clearInterval(pollInterval);
            onUploadStateChange({
              status: 'completed',
              processingProgress: 100,
              currentOperation: taskStatus.current_operation,
              fragmentCount: taskStatus.result.fragments_count,
              videoId: taskStatus.result.video_id.toString(),
              error: undefined
            }, notificationId);
            
            onUploadComplete(taskStatus.result.video_id.toString());
            onClose();
          } else if (taskStatus.status === 'progress') {
            onUploadStateChange({
              status: 'processing',
              processingProgress: taskStatus.progress,
              currentOperation: taskStatus.current_operation,
              fragmentCount: 0
            }, notificationId);
          } else if (taskStatus.status === 'failed') {
            clearInterval(pollInterval);
            onUploadStateChange({
              status: 'failed',
              error: taskStatus.error || 'Unknown error occurred',
              currentOperation: taskStatus.current_operation
            }, notificationId);
          }
        } catch (error) {
          console.error('Error checking task status:', error);
          // Don't clear interval or update state on temporary network errors
          // Just skip this update and try again
        }
      }, 1000);

      return () => {
        clearInterval(pollInterval);
      };
    } catch (error) {
      onUploadStateChange({
        status: 'error',
        error: error instanceof Error ? error.message : 'Upload failed'
      }, notificationId);
      setIsUploading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    startUploadProcess();
  };

  const handleNotificationClose = () => {
    setShowNotification(false);
  };

  const handleNotificationClick = () => {
    // onUploadStateChange({ status: 'completed' });
  };

  return (
    <div className="upload-component">
      <div className="modal-header">
        <h2>Upload Video</h2>
        <button className="close-button" onClick={onClose}>×</button>
      </div>

      <form onSubmit={handleSubmit} className="upload-form">
        <div className="upload-section">
          <div 
            className={`upload-area ${isDragOver ? 'drag-over' : ''} ${selectedFile ? 'has-file' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <input
              type="file"
              accept="video/*"
              onChange={handleFileChange}
              className="file-input"
              ref={fileInputRef}
            />
            
            {selectedFile ? (
              <div className="selected-file">
                <span className="file-name">{selectedFile.name}</span>
                <button
                  type="button"
                  className="change-file"
                  onClick={() => fileInputRef.current?.click()}
                >
                  Change File
                </button>
              </div>
            ) : (
              <div className="upload-placeholder">
                <FiUploadCloud className="upload-icon" />
                <p>Drag and drop your video here</p>
                <p>or click to browse</p>
              </div>
            )}
          </div>
        </div>

        <div className="metadata-section">
          <div className="form-group">
            <label htmlFor="title">Title</label>
            <input
              type="text"
              id="title"
              name="title"
              value={metadata.title}
              onChange={handleMetadataChange}
              className="form-input"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="description">Description</label>
            <textarea
              id="description"
              name="description"
              value={metadata.description}
              onChange={handleMetadataChange}
              className="form-input"
              rows={4}
            />
          </div>

          <div className="form-group">
            <label htmlFor="tags">Tags (comma-separated)</label>
            <input
              type="text"
              id="tags"
              name="tags"
              value={metadata.tags.join(', ')}
              onChange={handleTagsChange}
              className="form-input"
              placeholder="Enter tags separated by commas"
            />
          </div>
        </div>

        <div className="form-actions">
          <button
            type="button"
            className="cancel-button"
            onClick={onClose}
          >
            Cancel
          </button>
          <button
            type="submit"
            className="submit-button"
            disabled={!selectedFile || isUploading}
          >
            {isUploading ? 'Uploading...' : 'Upload'}
          </button>
        </div>
      </form>

      {showNotification && (
        <UploadNotification
          uploadProgress={0}
          processingProgress={0}
          currentOperation=""
          status="uploading"
          error=""
          fragmentCount={0}
          videoName={selectedFile?.name || "Unknown file"}
          onClose={handleNotificationClose}
          onClick={handleNotificationClick}
        />
      )}
    </div>
  );
};

export default UploadComponent;
