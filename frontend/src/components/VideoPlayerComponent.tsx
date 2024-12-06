import React, { useRef, useEffect, useState } from 'react';

interface VideoPlayerProps {
    url: string;
    startTime: number;
    endTime: number;
}

const VideoPlayerComponent: React.FC<VideoPlayerProps> = ({ 
    url, 
    startTime, 
    endTime 
}) => {
    const videoRef = useRef<HTMLVideoElement>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const video = videoRef.current;
        if (!video) return;

        // Устанавливаем начальное время воспроизведения
        video.currentTime = startTime;

        // Обработчик для остановки видео при достижении конечного времени
        const handleTimeUpdate = () => {
            if (video.currentTime >= endTime) {
                video.pause();
            }
        };

        // Обработчик ошибок загрузки видео
        const handleError = () => {
            setError('Ошибка при загрузке видео');
        };

        video.addEventListener('timeupdate', handleTimeUpdate);
        video.addEventListener('error', handleError);

        return () => {
            video.removeEventListener('timeupdate', handleTimeUpdate);
            video.removeEventListener('error', handleError);
        };
    }, [startTime, endTime]);

    return (
        <div className="video-player">
            {error ? (
                <div className="video-error">{error}</div>
            ) : (
                <video
                    ref={videoRef}
                    src={url}
                    controls
                    className="video-element"
                    style={{ width: '100%', maxHeight: '400px' }}
                >
                    Ваш браузер не поддерживает воспроизведение видео.
                </video>
            )}
        </div>
    );
};

export default VideoPlayerComponent;
