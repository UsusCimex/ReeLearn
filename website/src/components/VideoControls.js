import React from 'react';
import { logInfo } from '../utils/logger';

const VideoControls = ({ handleNextVideo, handlePrevVideo, currentVideoIndex, totalVideos }) => {
  logInfo(`Current video index: ${currentVideoIndex}`);

  return (
    <div className="video-controls">
      <button onClick={handlePrevVideo} disabled={currentVideoIndex === 0}>
        Предыдущее видео
      </button>
      <button onClick={handleNextVideo} disabled={currentVideoIndex === totalVideos - 1}>
        Следующее видео
      </button>
    </div>
  );
};

export default VideoControls;
