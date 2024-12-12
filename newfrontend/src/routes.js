import React from 'react';
import { Routes, Route } from 'react-router-dom';
import SearchPage from './pages/SearchPage';
import VideoListPage from './pages/VideoListPage';
import VideoFragmentsPage from './pages/VideoFragmentsPage';

function AppRoutes() {
  return (
    <div>
      <nav style={{ marginBottom: '20px' }}>
      </nav>
      <Routes>
        <Route path="/" element={<SearchPage />} />
        <Route path="/videos" element={<VideoListPage />} />
        <Route path="/videos/:id" element={<VideoFragmentsPage />} />
      </Routes>
    </div>
  );
}

export default AppRoutes;
