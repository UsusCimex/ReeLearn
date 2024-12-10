import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import UploadComponent from './UploadComponent';
import { uploadState } from '../types';
import '../styles/Navigation.css';

interface NavigationProps {
  onUploadStateChange: (state: Partial<uploadState>, notification_id: string) => void;
  onUploadComplete: (videoId: string) => void;
}

export const Navigation: React.FC<NavigationProps> = ({
  onUploadStateChange,
  onUploadComplete
}) => {
  const [showUploadModal, setShowUploadModal] = useState(false);

  const handleUploadComplete = (videoId: string) => {
    setShowUploadModal(false);
    onUploadComplete(videoId);
    // You might want to refresh the video list here
  };

  const handleUploadStateChange = (state: Partial<uploadState>, notification_id: string) => {
    onUploadStateChange(state, notification_id);
  };

  return (
    <nav className="navigation">
      <div className="nav-content">
        <Link to="/" className="nav-logo">
          ReeLearn
        </Link>
        <div className="nav-links">
          <Link to="/videos" className="nav-link">
            My Videos
          </Link>
          <button 
            className="nav-link upload-button"
            onClick={() => setShowUploadModal(true)}
          >
            Upload Video
          </button>
        </div>
      </div>

      {showUploadModal && (
        <div className="modal-overlay" onClick={() => setShowUploadModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <button className="modal-close" onClick={() => setShowUploadModal(false)}>×</button>
            <UploadComponent
              on_upload_state_change={handleUploadStateChange}
              on_upload_complete={handleUploadComplete}
            />
          </div>
        </div>
      )}
    </nav>
  );
};

export default Navigation;
