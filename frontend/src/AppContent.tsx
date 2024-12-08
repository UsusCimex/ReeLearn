import React, { useState } from 'react';
import { Routes, Route, useNavigate, Link } from 'react-router-dom';
import { UploadState, UploadNotificationItem } from './types';
import UploadComponent from './components/UploadComponent';
import UploadNotification from './components/UploadNotification';
import SearchComponent from './components/SearchComponent';
import SearchResultsComponent from './components/SearchResultsComponent';
import VideoFragmentsView from './components/VideoFragmentsView';
import NotificationsView from './components/NotificationsView';

const AppContent: React.FC = () => {
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [notifications, setNotifications] = useState<UploadNotificationItem[]>([]);
  const navigate = useNavigate();

  const handleUploadComplete = (videoId: string, notificationId: string) => {
    setNotifications(prev => prev.map(notification => 
      notification.id === notificationId 
        ? { ...notification, videoId }
        : notification
    ));
  };

  const handleNotificationClose = (notificationId: string) => {
    setNotifications(prev => prev.filter(notification => notification.id !== notificationId));
  };

  const handleUploadStateChange = (newState: Partial<UploadState>, notificationId?: string): string => {
    if (!notificationId) {
      // Create new notification
      if (!newState.videoName) {
        throw new Error('Video name is required for new notifications');
      }
      const newNotification: UploadNotificationItem = {
        id: Math.random().toString(36).substring(7),
        timestamp: Date.now(),
        uploadProgress: 0,
        processingProgress: 0,
        currentOperation: '',
        status: 'uploading',
        fragmentCount: 0,
        videoName: newState.videoName,
        ...newState
      };
      setNotifications(prev => [...prev, newNotification]);
      return newNotification.id;
    } else {
      // Update existing notification
      setNotifications(prev => prev.map(notification =>
        notification.id === notificationId
          ? { ...notification, ...newState }
          : notification
      ));
      return notificationId;
    }
  };

  return (
    <>
      <header className="header">
        <div className="header-content">
          <h1 className="logo">
            <Link to="/" className="logo-link">ReeLearn</Link>
          </h1>
          <div className="header-actions">
            <Link to="/notifications" className="notifications-link">
              Uploaded Videos
            </Link>
            <button 
              className="upload-button"
              onClick={() => setShowUploadModal(true)}
            >
              Upload Video
            </button>
          </div>
        </div>
      </header>

      <main className="main">
        <div className="content">
          <div className="main-container">
            <Routes>
              <Route 
                path="/" 
                element={
                  <div className="home-container">
                    <div className="search-section">
                      <h2 className="search-title">Video Search</h2>
                      <p className="search-description">
                        Find the right moment in the video using text search
                      </p>
                      <SearchComponent />
                    </div>
                  </div>
                } 
              />
              <Route 
                path="/search/:taskId" 
                element={<SearchResultsComponent />} 
              />
              <Route 
                path="/videos/:videoId/fragments" 
                element={<VideoFragmentsView />} 
              />
              <Route 
                path="/notifications" 
                element={<NotificationsView />} 
              />
            </Routes>
          </div>
        </div>
      </main>

      {showUploadModal && (
        <div className="modal-overlay" onClick={() => setShowUploadModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <UploadComponent
              onClose={() => setShowUploadModal(false)}
              onUploadComplete={(videoId) => {
                const notificationId = handleUploadStateChange({ status: 'completed', videoId });
                handleUploadComplete(videoId, notificationId);
              }}
              onUploadStateChange={handleUploadStateChange}
            />
          </div>
        </div>
      )}

      <div className="notifications-container">
        {notifications.map((notification) => (
          <UploadNotification
            key={notification.id}
            uploadProgress={notification.uploadProgress}
            processingProgress={notification.processingProgress}
            currentOperation={notification.currentOperation}
            status={notification.status}
            error={notification.error}
            fragmentCount={notification.fragmentCount}
            videoName={notification.videoName}
            videoId={notification.videoId}
            onClose={() => handleNotificationClose(notification.id)}
          />
        ))}
      </div>

      <footer className="footer">
        <div className="footer-content">
          <p>&copy; 2024 ReeLearn. All rights reserved.</p>
        </div>
      </footer>
    </>
  );
};

export default AppContent;
