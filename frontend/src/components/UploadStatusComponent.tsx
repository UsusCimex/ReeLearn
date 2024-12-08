import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getTaskStatus } from '../api/config';
import { TaskStatus } from '../types';

const UploadStatusComponent: React.FC = () => {
    const { taskId } = useParams<{ taskId: string }>();
    const navigate = useNavigate();
    const [status, setStatus] = useState<TaskStatus | null>(null);

    useEffect(() => {
        if (!taskId) {
            navigate('/');
            return;
        }

        const pollStatus = async () => {
            try {
                const response = await getTaskStatus(taskId);
                setStatus(response);

                if (response.status === 'failed') {
                    // Оставляем статус ошибки для отображения
                } else if (response.status !== 'completed') {
                    // Продолжаем опрос только для pending и processing
                    setTimeout(pollStatus, 2000);
                }
            } catch (error) {
                console.error('Error fetching task status:', error);
                setStatus((prev: TaskStatus | null) => prev ? {
                    ...prev,
                    status: 'failed',
                    error: 'Failed to fetch task status'
                } : null);
            }
        };

        pollStatus();
    }, [taskId, navigate]);

    if (!status) {
        return <div className="loading">Loading...</div>;
    }

    if (status.status === 'failed') {
        return (
            <div className="error-container">
                <h2>Upload Failed</h2>
                <p>{status.error || 'An unknown error occurred'}</p>
                <button onClick={() => navigate('/')}>Back to Home</button>
            </div>
        );
    }

    return (
        <div className="upload-status">
            <h2>Processing Video</h2>
            <div className="progress-container">
                <div className="progress-bar">
                    <div 
                        className="progress-fill"
                        style={{ width: `${status.progress}%` }}
                    />
                </div>
                <div className="progress-text">
                    {status.current_operation}
                    <span className="progress-percentage">
                        {Math.round(status.progress)}%
                    </span>
                </div>
            </div>
        </div>
    );
};

export default UploadStatusComponent;
