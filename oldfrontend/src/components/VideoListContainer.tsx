import React, { useEffect, useState } from 'react';
import VideoList from './VideoList';
import { videoInfo, videoListResponse } from '../types';
import { getVideoList } from '../api/api';

interface VideoListContainerProps {
  on_video_select: (video_id: string) => void;
}

const VideoListContainer: React.FC<VideoListContainerProps> = ({ on_video_select }) => {
  const [videos, set_videos] = useState<videoInfo[]>([]);
  const [loading, set_loading] = useState(true);
  const [error, set_error] = useState<string | null>(null);

  useEffect(() => {
    const fetch_videos = async () => {
      try {
        set_loading(true);
        const response: videoListResponse = await getVideoList();
        set_videos(response.videos);
        set_error(null);
      } catch (err) {
        set_error('Failed to load videos');
        console.error('Error fetching videos:', err);
      } finally {
        set_loading(false);
      }
    };

    fetch_videos();
  }, []);

  if (loading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return <VideoList videos={videos} on_video_select={on_video_select} />;
};

export default VideoListContainer;
