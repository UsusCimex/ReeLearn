// components/VideoPlayer.js
import React from 'react';

const VideoPlayer = ({ videoUrl, handleNextVideo, currentVideoIndex, totalVideos, videoRef }) => {
  const onVideoEnd = () => {
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
