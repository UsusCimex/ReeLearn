import React, { useState } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { uploadVideo, checkTaskStatus } from '../api/api';
import { uploadState, uploadStatus, taskStatusResponse, taskStatus } from '../types';
import '../styles/UploadComponent.css';

interface upload_component_props {
  on_upload_state_change: (state: Partial<uploadState>, notification_id: string) => void;
  on_upload_complete?: (video_id: string) => void;
}

const UploadComponent: React.FC<upload_component_props> = ({ 
  on_upload_state_change, 
  on_upload_complete 
}) => {
  const [is_dragging, setIsDragging] = useState(false);

  const check_upload_status = async (task_id: string, notification_id: string) => {
    try {
      const status: taskStatusResponse = await checkTaskStatus(task_id);

      if (status.status === taskStatus.COMPLETED) {
        on_upload_state_change({
          status: uploadStatus.COMPLETED,
          upload_progress: 100,
          current_operation: 'Completed'
        }, notification_id);

        if (on_upload_complete && status.result?.video_id) {
          on_upload_complete(status.result.video_id);
        }
      } else if (status.status === taskStatus.FAILED) {
        on_upload_state_change({
          status: uploadStatus.FAILED,
          error: status.error || 'Processing failed',
          current_operation: 'Failed'
        }, notification_id);
      } else if (status.status === taskStatus.PROGRESS) {
        on_upload_state_change({
          status: uploadStatus.PROCESSING,
          processing_progress: status.progress,
          current_operation: status.current_operation
        }, notification_id);
        // Still processing, check again in 2 seconds
        setTimeout(() => check_upload_status(task_id, notification_id), 2000);
      } else {
        // PENDING status
        setTimeout(() => check_upload_status(task_id, notification_id), 2000);
      }
    } catch (error) {
      on_upload_state_change({
        status: uploadStatus.FAILED,
        error: error instanceof Error ? error.message : 'Failed to check upload status',
        current_operation: 'Error checking status'
      }, notification_id);
    }
  };

  const handle_file_upload = async (file: File) => {
    const notification_id = uuidv4();

    on_upload_state_change({
      status: uploadStatus.UPLOADING,
      upload_progress: 0,
      current_operation: 'Starting upload...'
    }, notification_id);

    try {
      const response = await uploadVideo(file, (progress) => {
        on_upload_state_change({
          status: uploadStatus.UPLOADING,
          upload_progress: progress,
          current_operation: 'Uploading...'
        }, notification_id);
      });

      on_upload_state_change({
        status: uploadStatus.PROCESSING,
        upload_progress: 100,
        processing_progress: 0,
        current_operation: 'Processing video...'
      }, notification_id);

      check_upload_status(response.task_id, notification_id);
    } catch (error) {
      on_upload_state_change({
        status: uploadStatus.FAILED,
        error: error instanceof Error ? error.message : 'Upload failed',
        current_operation: 'Upload failed'
      }, notification_id);
    }
  };

  const handle_drag_enter = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handle_drag_leave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handle_drop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      const video_file = files[0];
      if (video_file.type.startsWith('video/')) {
        await handle_file_upload(video_file);
      } else {
        alert('Please upload a video file');
      }
    }
  };

  const handle_file_select = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      const video_file = files[0];
      if (video_file.type.startsWith('video/')) {
        await handle_file_upload(video_file);
      } else {
        alert('Please upload a video file');
      }
    }
  };

  return (
    <div className="upload-component">
      <div
        className={`upload-area ${is_dragging ? 'dragging' : ''}`}
        onDragEnter={handle_drag_enter}
        onDragOver={handle_drag_enter}
        onDragLeave={handle_drag_leave}
        onDrop={handle_drop}
      >
        <input
          type="file"
          accept="video/*"
          onChange={handle_file_select}
          className="file-input"
          id="file-input"
        />
        <label htmlFor="file-input" className="upload-label">
          <div className="upload-icon">📁</div>
          <div className="upload-text">
            {is_dragging
              ? 'Drop video here'
              : 'Drag & drop video or click to upload'}
          </div>
        </label>
      </div>
    </div>
  );
};

export default UploadComponent;
