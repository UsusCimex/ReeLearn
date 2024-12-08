import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getVideoList } from '../api/api';
import '../styles/NotificationsView.css';

interface Video {
  id: number;
  title: string;
  upload_date: string;
  status: string;
  fragments_count: number;
}

const NotificationsView: React.FC = () => {
  const [videos, setVideos] = useState<Video[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchVideos = async () => {
      try {
        const data = await getVideoList();
        setVideos(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch videos');
      } finally {
        setLoading(false);
      }
    };

    fetchVideos();
  }, []);

  if (loading) {
    return <div className="notifications-loading">Loading videos...</div>;
  }

  if (error) {
    return <div className="notifications-error">Error: {error}</div>;
  }

  if (videos.length === 0) {
    return <div className="notifications-empty">No videos found.</div>;
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="notifications-container">
      <h2>Uploaded Videos</h2>
      <div className="videos-list">
        {videos.map((video) => (
          <div key={video.id} className="video-item">
            <div className="video-header">
              <h3 className="video-title">{video.title}</h3>
              <span className="video-date">{formatDate(video.upload_date)}</span>
            </div>
            <div className="video-info">
              <span className={`video-status status-${video.status.toLowerCase()}`}>
                {video.status}
              </span>
              <span className="fragments-count">
                {video.fragments_count} fragments
              </span>
            </div>
            <div className="video-actions">
              <Link to={`/videos/${video.id}/fragments`} className="view-fragments-btn">
                View Fragments
              </Link>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default NotificationsView;
