import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { getVideoFragments } from '../api/api';
import { VideoFragmentsResponse } from '../types';
import '../styles/VideoFragmentsView.css';

const VideoFragmentsView: React.FC = () => {
  const { videoId } = useParams<{ videoId: string }>();
  const [fragments, setFragments] = useState<VideoFragmentsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchFragments = async () => {
      try {
        if (!videoId) {
          throw new Error('Video ID is required');
        }
        const data = await getVideoFragments(videoId);
        setFragments(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch video fragments');
      } finally {
        setLoading(false);
      }
    };

    fetchFragments();
  }, [videoId]);

  if (loading) {
    return <div className="video-fragments-loading">Loading fragments...</div>;
  }

  if (error) {
    return <div className="video-fragments-error">Error: {error}</div>;
  }

  if (!fragments || fragments.fragments.length === 0) {
    return <div className="video-fragments-empty">No fragments found for this video.</div>;
  }

  const formatTime = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  return (
    <div className="video-fragments-container">
      <h2>Video Fragments</h2>
      <div className="fragments-list">
        {fragments.fragments.map((fragment) => (
          <div key={fragment.id} className="fragment-item">
            <div className="fragment-header">
              <span className="fragment-time">
                {formatTime(fragment.timecode_start)} - {formatTime(fragment.timecode_end)}
              </span>
              {fragment.tags && fragment.tags.length > 0 && (
                <div className="fragment-tags">
                  {fragment.tags.map((tag, index) => (
                    <span key={index} className="tag">{tag}</span>
                  ))}
                </div>
              )}
            </div>
            <div className="fragment-text">{fragment.text}</div>
            <video 
              className="fragment-video" 
              src={fragment.s3_url} 
              controls
              preload="metadata"
            >
              Your browser does not support the video tag.
            </video>
          </div>
        ))}
      </div>
    </div>
  );
};

export default VideoFragmentsView;
