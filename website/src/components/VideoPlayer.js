import React from 'react';
import { logInfo } from '../utils/logger'; 

const VideoPlayer = ({ videoUrl, handleNextVideo, currentVideoIndex, totalVideos, videoRef }) => {
  const onVideoEnd = () => {
    logInfo(`Video ${currentVideoIndex + 1} ended`);
    if (currentVideoIndex < totalVideos - 1) {
      handleNextVideo();
    }
  };

  return (
    <div className="video-player-container">
      <video
        ref={videoRef}
        className="video-player"
        src={videoUrl}
        controls
        autoPlay
        onEnded={onVideoEnd}
      />
    </div>
  );
};

export default VideoPlayer;
