import React, { useRef, useEffect } from 'react';
import { Box } from '@chakra-ui/react';

function VideoPlayer({ url, subtitles }) {
  const videoRef = useRef(null);
  const trackRef = useRef(null);

  useEffect(() => {
    if (videoRef.current && subtitles) {
      // Remove existing tracks
      while (videoRef.current.firstChild) {
        videoRef.current.removeChild(videoRef.current.firstChild);
      }

      // Create new track element
      const track = document.createElement('track');
      track.kind = 'subtitles';
      track.label = 'English';
      track.srcLang = 'en';
      track.default = true;

      // Create blob URL for subtitles
      const blob = new Blob([subtitles], { type: 'text/vtt' });
      track.src = URL.createObjectURL(blob);

      trackRef.current = track;
      videoRef.current.appendChild(track);
    }

    return () => {
      // Cleanup blob URL
      if (trackRef.current?.src) {
        URL.revokeObjectURL(trackRef.current.src);
      }
    };
  }, [subtitles]);

  return (
    <Box width="100%" maxW="1000px" mx="auto">
      <video
        ref={videoRef}
        controls
        style={{ width: '100%', height: 'auto' }}
        crossOrigin="anonymous"
      >
        <source src={url} type="video/mp4" />
        Your browser does not support the video tag.
      </video>
    </Box>
  );
}

export default VideoPlayer;
