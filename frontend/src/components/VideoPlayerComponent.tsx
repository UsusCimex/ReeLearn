import React, { useRef, useEffect, useState } from 'react';

interface VideoPlayerProps {
    url: string;
    startTime: number;
    endTime: number;
    onUploadProgress?: (progress: number) => void;
}

interface UploadStatus {
    progress: number;
    stage: 'preparing' | 'uploading' | 'processing' | 'complete' | 'error';
    message: string;
}

const getStageMessage = (stage: UploadStatus['stage']): string => {
    switch (stage) {
        case 'preparing':
            return 'Подготовка к загрузке...';
        case 'uploading':
            return 'Загрузка видео...';
        case 'processing':
            return 'Обработка видео...';
        case 'complete':
            return 'Загрузка завершена!';
        case 'error':
            return 'Ошибка загрузки';
        default:
            return 'Загрузка...';
    }
};

const VideoPlayerComponent: React.FC<VideoPlayerProps> = ({ 
    url, 
    startTime, 
    endTime,
    onUploadProgress 
}) => {
    const videoRef = useRef<HTMLVideoElement>(null);
    const [isLoaded, setIsLoaded] = useState(false);
    const [duration, setDuration] = useState<number | null>(null);
    const [uploadStatus, setUploadStatus] = useState<UploadStatus>({
        progress: 0,
        stage: 'preparing',
        message: getStageMessage('preparing')
    });
    const [showUploadStatus, setShowUploadStatus] = useState(false);

    useEffect(() => {
        const video = videoRef.current;
        if (!video) return;

        const handleLoadedMetadata = () => {
            setIsLoaded(true);
            setDuration(video.duration);
        };

        const handleProgress = () => {
            if (video.buffered.length > 0) {
                const progress = (video.buffered.end(0) / video.duration) * 100;
                const stage = progress >= 100 ? 'complete' : 'uploading';
                setUploadStatus(prev => ({
                    ...prev,
                    progress: Math.min(progress, 100),
                    stage,
                    message: getStageMessage(stage)
                }));
                onUploadProgress?.(progress);
            }
        };

        video.addEventListener('loadedmetadata', handleLoadedMetadata);
        video.addEventListener('progress', handleProgress);
        setShowUploadStatus(true);

        return () => {
            video.removeEventListener('loadedmetadata', handleLoadedMetadata);
            video.removeEventListener('progress', handleProgress);
        };
    }, [url, onUploadProgress]);

    return (
        <div className="video-player">
            {showUploadStatus && (
                <div className="upload-progress">
                    <div className="upload-status">
                        <span>{uploadStatus.message}</span>
                        {uploadStatus.stage === 'complete' && (
                            <svg className="upload-status-icon" viewBox="0 0 20 20" fill="currentColor">
                                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                            </svg>
                        )}
                    </div>
                    <div className="progress-bar">
                        <div 
                            className="progress-bar-fill" 
                            style={{ width: `${uploadStatus.progress}%` }}
                        />
                    </div>
                </div>
            )}
            
            <video
                ref={videoRef}
                controls
                preload="auto"
                style={{ 
                    maxWidth: '100%', 
                    width: '100%',
                    borderRadius: 'var(--border-radius)',
                    boxShadow: 'var(--shadow)'
                }}
            >
                <source src={url} type="video/mp4" />
                Ваш браузер не поддерживает HTML5 видео.
            </video>
            
            <div className="video-info">
                <span>Фрагмент видео: {startTime.toFixed(2)}с - {endTime.toFixed(2)}с</span>
                {duration && <span> (Длительность: {duration.toFixed(2)}с)</span>}
            </div>
        </div>
    );
};

export default VideoPlayerComponent;
