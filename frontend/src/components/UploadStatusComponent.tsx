import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { get_task_status } from '../api/config';
import { taskStatus, taskStatusResponse } from '../types';
import '../styles/UploadStatusComponent.css';

interface upload_status_component_props {
    status: taskStatusResponse;
}

const UploadStatusComponent: React.FC<upload_status_component_props> = ({ status }) => {
    const get_progress_percentage = () => {
        if (status.progress !== undefined) {
            return Math.round(status.progress * 100);
        }
        return 0;
    };

    const get_status_text = () => {
        switch (status.status) {
            case taskStatus.PENDING:
                return 'Waiting to start...';
            case taskStatus.PROGRESS:
                return status.current_operation || 'Processing...';
            case taskStatus.COMPLETED:
                return 'Complete!';
            case taskStatus.FAILED:
                return status.error || 'Failed';
            default:
                return 'Unknown status';
        }
    };

    const is_in_progress = status.status === taskStatus.PROGRESS || status.status === taskStatus.PENDING;
    const progress_percentage = get_progress_percentage();
    const status_text = get_status_text();

    return (
        <div className={`upload-status ${status.status}`}>
            {is_in_progress && (
                <div className="progress-container">
                    <div className="progress-bar">
                        <div
                            className="progress-fill"
                            style={{ width: `${progress_percentage}%` }}
                        />
                    </div>
                    <div className="progress-text">
                        {status_text}
                        <span className="progress-percentage">
                            {progress_percentage}%
                        </span>
                    </div>
                </div>
            )}

            {status.status === 'completed' && (
                <div className="status-message success">
                    {status_text}
                </div>
            )}

            {status.status === 'failed' && (
                <div className="status-message error">
                    {status_text}
                </div>
            )}
        </div>
    );
};

const UploadStatusContainer: React.FC = () => {
    const { task_id } = useParams<{ task_id: string }>();
    const navigate = useNavigate();
    const [status, setStatus] = useState<taskStatusResponse | null>(null);

    useEffect(() => {
        if (!task_id) {
            navigate('/');
            return;
        }

        const poll_status = async () => {
            try {
                const response = await get_task_status(task_id);
                setStatus(response);

                if (response.status === 'failed') {
                    // Оставляем статус ошибки для отображения
                } else if (response.status !== 'completed') {
                    // Продолжаем опрос только для pending и processing
                    setTimeout(poll_status, 2000);
                }
            } catch (error) {
                console.error('Error fetching task status:', error);
                setStatus((prev: taskStatusResponse | null) => prev ? {
                    ...prev,
                    status: taskStatus.FAILED,
                    error: 'Failed to fetch task status'
                } : null);
            }
        };

        poll_status();
    }, [task_id, navigate]);

    if (!status) {
        return <div className="loading">Loading...</div>;
    }

    return <UploadStatusComponent status={status} />;
};

export default UploadStatusContainer;
