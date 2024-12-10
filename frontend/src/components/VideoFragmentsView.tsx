import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { getVideoFragments } from '../api/api';
import { videoFragment } from '../types';
import { isVideoFragment } from '../types/guards';
import '../styles/VideoFragmentsView.css';

interface video_fragments_view_props {
  video_id?: string;
}

const VideoFragmentsView: React.FC<video_fragments_view_props> = ({ video_id: prop_video_id }) => {
  const { video_id: url_video_id } = useParams<{ video_id: string }>();
  const video_id = prop_video_id || url_video_id;

  const [fragments, setFragments] = useState<videoFragment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selected_fragment, setSelectedFragment] = useState<videoFragment | null>(null);

  useEffect(() => {
    const load_fragments = async () => {
      if (!video_id) {
        setError('No video ID provided');
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);
        const response = await getVideoFragments(Number(video_id));
        
        // Validate fragments
        const valid_fragments = response.fragments.filter(isVideoFragment);
        if (valid_fragments.length !== response.fragments.length) {
          console.warn('Some fragments were invalid and filtered out');
        }
        
        setFragments(valid_fragments);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load fragments');
      } finally {
        setLoading(false);
      }
    };

    load_fragments();
  }, [video_id]);

  if (loading) {
    return <div className="loading">Loading fragments...</div>;
  }

  if (error) {
    return <div className="error">{error}</div>;
  }

  if (fragments.length === 0) {
    return <div className="no-fragments">No fragments found for this video</div>;
  }

  const format_time = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const remaining_seconds = Math.floor(seconds % 60);
    return `${minutes}:${remaining_seconds.toString().padStart(2, '0')}`;
  };

  return (
    <div className="video-fragments-container">
      <div className="fragments-list">
        {fragments.map((fragment) => (
          <div
            key={fragment.id}
            className={`fragment-item ${selected_fragment?.id === fragment.id ? 'selected' : ''}`}
            onClick={() => setSelectedFragment(fragment)}
          >
            <div className="fragment-header">
              <span className="fragment-time">
                {format_time(fragment.timecode_start)} - {format_time(fragment.timecode_end)}
              </span>
              {fragment.score && (
                <span className="fragment-score">
                  Score: {(fragment.score * 100).toFixed(1)}%
                </span>
              )}
            </div>
            <div className="fragment-text">{fragment.text}</div>
            {fragment.tags && fragment.tags.length > 0 && (
              <div className="fragment-tags">
                {fragment.tags.map((tag, index) => (
                  <span key={index} className="tag">
                    {tag}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {selected_fragment && (
        <div className="fragment-details">
          <h3>Selected Fragment</h3>
          <div className="fragment-info">
            <p>
              <strong>Time:</strong> {format_time(selected_fragment.timecode_start)} -{' '}
              {format_time(selected_fragment.timecode_end)}
            </p>
            <p>
              <strong>Video:</strong> {selected_fragment.video_name}
            </p>
            <p>
              <strong>Text:</strong> {selected_fragment.text}
            </p>
            {selected_fragment.tags && selected_fragment.tags.length > 0 && (
              <p>
                <strong>Tags:</strong>{' '}
                {selected_fragment.tags.map((tag, index) => (
                  <span key={index} className="tag">
                    {tag}
                  </span>
                ))}
              </p>
            )}
            {selected_fragment.score && (
              <p>
                <strong>Match Score:</strong> {(selected_fragment.score * 100).toFixed(1)}%
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default VideoFragmentsView;
