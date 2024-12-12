import React from 'react';
import { videoInfo } from '../types';
import { List, ListItem, ListItemText } from '@mui/material';
import '../styles/VideoList.css';

interface video_list_props {
  videos: videoInfo[];
  on_video_select: (video_id: string) => void;
}

const VideoList: React.FC<video_list_props> = ({ videos, on_video_select }) => {
  if (!videos || videos.length === 0) {
    return (
      <div className="video-list-empty">
        <span className="material-icons">videocam_off</span>
        <p>No videos found</p>
      </div>
    );
  }

  return (
    <List className="video-list">
      {videos.map((video) => (
        <ListItem
          key={video.id}
          button
          className="video-item"
          onClick={() => on_video_select(video.id.toString())}
        >
          <ListItemText
            primary={video.name || `Video ${video.id}`}
            secondary={`${video.fragments_count} fragments • Status: ${video.status}`}
          />
        </ListItem>
      ))}
    </List>
  );
};

export default VideoList;
