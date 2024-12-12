import React, { useState, useEffect, useRef } from 'react';
import ReactPlayer from 'react-player';
import { videoFragment } from '../types';
import { Box, IconButton, Typography } from '@mui/material';
import { PlayArrow, Pause } from '@mui/icons-material';
import '../styles/VideoPlayer.css';

interface video_player_props {
  fragment: videoFragment;
  on_end?: () => void;
}

const VideoPlayerComponent: React.FC<video_player_props> = ({
  fragment,
  on_end
}) => {
  const [is_playing, setIsPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const playerRef = useRef<ReactPlayer>(null);

  useEffect(() => {
    if (playerRef.current) {
      playerRef.current.seekTo(fragment.timecode_start);
    }
  }, [fragment]);

  const handle_progress = (state: { played: number }) => {
    const total_duration = fragment.timecode_end - fragment.timecode_start;
    const current_time = state.played * total_duration;
    const progress_percent = (current_time / total_duration) * 100;
    setProgress(progress_percent);

    if (state.played >= (fragment.timecode_end - fragment.timecode_start)) {
      setIsPlaying(false);
      if (on_end) {
        on_end();
      }
    }
  };

  const format_time = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const remaining_seconds = Math.floor(seconds % 60);
    return `${minutes}:${remaining_seconds.toString().padStart(2, '0')}`;
  };

  const handle_play_pause = () => {
    setIsPlaying(!is_playing);
  };

  return (
    <div className="video-player">
      <div className="player-wrapper">
        <ReactPlayer
          ref={playerRef}
          url={fragment.s3_url}
          playing={is_playing}
          controls={false}
          onProgress={handle_progress}
          width="100%"
          height="100%"
          progressInterval={100}
          config={{
            file: {
              attributes: {
                crossOrigin: "anonymous"
              }
            }
          }}
        />
      </div>
      <div className="controls">
        <IconButton onClick={handle_play_pause}>
          {is_playing ? <Pause /> : <PlayArrow />}
        </IconButton>
        <Box sx={{ flex: 1, mx: 2 }}>
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${progress}%` }}
            />
          </div>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
            <Typography variant="caption">
              {format_time(fragment.timecode_start + (progress / 100) * (fragment.timecode_end - fragment.timecode_start))}
              {' / '}
              {format_time(fragment.timecode_end)}
            </Typography>
          </Box>
        </Box>
      </div>
    </div>
  );
};

export default VideoPlayerComponent;
