import React, { useEffect, useRef, useState } from 'react';
import { SearchResult } from '../types';
import '../styles/VideoPlayerComponent.css';

interface VideoPlayerComponentProps {
  result: SearchResult;
}

const VideoPlayerComponent: React.FC<VideoPlayerComponentProps> = ({ result }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);

  useEffect(() => {
    if (videoRef.current && result.presigned_url) {
      videoRef.current.src = result.presigned_url;
      videoRef.current.currentTime = result.timecode_start;
    }
  }, [result]);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const handleTimeUpdate = () => {
      setCurrentTime(video.currentTime);
    };

    const handleDurationChange = () => {
      setDuration(video.duration);
    };

    video.addEventListener('timeupdate', handleTimeUpdate);
    video.addEventListener('durationchange', handleDurationChange);

    return () => {
      video.removeEventListener('timeupdate', handleTimeUpdate);
      video.removeEventListener('durationchange', handleDurationChange);
    };
  }, []);

  const togglePlay = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const time = parseFloat(e.target.value);
    if (videoRef.current) {
      videoRef.current.currentTime = time;
      setCurrentTime(time);
    }
  };

  const formatTime = (time: number): string => {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  return (
    <div className="video-player">
      <video
        ref={videoRef}
        className="video-element"
        playsInline
        onPlay={() => setIsPlaying(true)}
        onPause={() => setIsPlaying(false)}
      />
      <div className="video-controls">
        <button 
          className="play-pause-button" 
          onClick={togglePlay}
          aria-label={isPlaying ? 'Пауза' : 'Воспроизвести'}
        >
          {isPlaying ? '⏸' : '▶'}
        </button>
        <div className="time-control">
          <span className="time-display">{formatTime(currentTime)}</span>
          <input
            type="range"
            className="seek-bar"
            value={currentTime}
            min={0}
            max={duration}
            step={0.1}
            onChange={handleSeek}
          />
          <span className="time-display">{formatTime(duration)}</span>
        </div>
      </div>
      {result.text && (
        <div className="video-caption">
          <p>{result.text}</p>
          <div className="caption-time">
            {formatTime(result.timecode_start)}
            {result.timecode_end && ` - ${formatTime(result.timecode_end)}`}
          </div>
        </div>
      )}
    </div>
  );
};

export default VideoPlayerComponent;
