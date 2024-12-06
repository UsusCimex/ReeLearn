import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getTaskStatus } from '../api/config';
import { TaskStatusResponse } from '../types';

const UploadStatusComponent: React.FC = () => {
    const { taskId } = useParams<{ taskId: string }>();
    const [status, setStatus] = useState<TaskStatusResponse | null>(null);
    const navigate = useNavigate();

    useEffect(() => {
        if (!taskId) return;

        const pollStatus = async () => {
            try {
                const response = await getTaskStatus(taskId);
                setStatus(response);

                if (['completed', 'failed'].includes(response.status)) {
                    return;
                }
            } catch (error) {
                console.error('Error fetching task status:', error);
                setStatus(prev => prev ? {
                    ...prev,
                    status: 'failed',
                    error: 'Failed to fetch task status'
                } : null);
            }
        };

        const interval = setInterval(pollStatus, 2000);
        pollStatus();

        return () => clearInterval(interval);
    }, [taskId]);

    if (!status) {
        return <div className="status-container">Loading task status...</div>;
    }

    return (
        <div className="status-container">
            <h2>Upload Status</h2>
            <div className="status-info">
                <p>Status: {status.status}</p>
                <p>Progress: {status.progress}%</p>
                {status.current_operation && (
                    <p>Current Operation: {status.current_operation}</p>
                )}
                {status.error && (
                    <p className="error">Error: {status.error}</p>
                )}
            </div>
            {status.status === 'completed' && (
                <button onClick={() => navigate('/')}>Upload Another Video</button>
            )}
            {status.status === 'failed' && (
                <button onClick={() => navigate('/')}>Try Again</button>
            )}
        </div>
    );
};

export default UploadStatusComponent;
