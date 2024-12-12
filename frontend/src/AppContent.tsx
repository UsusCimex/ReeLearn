import React, { useState } from 'react';
import { Routes, Route, useNavigate } from 'react-router-dom';
import Navigation from './components/Navigation';
import SearchResultsComponent from './components/SearchResultsComponent';
import VideoFragmentsView from './components/VideoFragmentsView';
import { searchStatus, uploadState } from './types';
import './styles/AppContent.css';
import { Home } from '@mui/icons-material';
import HomePage from './components/HomePage';
import SearchComponent from './components/SearchComponent';
import UploadComponent from './components/UploadComponent';

const AppContent: React.FC = () => {
    const navigate = useNavigate();
    const [upload_states, setUploadStates] = useState<Record<string, uploadState>>({});

    const handle_upload_state_change = (state: Partial<uploadState>, notification_id: string) => {
        setUploadStates(prev => ({
            ...prev,
            [notification_id]: {
                ...prev[notification_id],
                ...state
            } as uploadState
        }));
    };

    const handle_upload_complete = (video_id: string) => {
        navigate(`/video/${video_id}`);
    };

    const handle_video_select = (video_id: string) => {
        navigate(`/video/${video_id}`);
    };

    return (
        <div className="app-content">
            <div className="content-wrapper">
                <Navigation
                    onUploadStateChange={handle_upload_state_change}
                    onUploadComplete={handle_upload_complete}
                />
                <div className="main-content">
                <Routes>
                    <Route path="/" element={<HomePage />} />
                    
                    <Route path="/search" element={<SearchComponent onResultsFound={(results) => {
                        // Обработка результатов поиска
                    }} />} />
                    
                    <Route path="/results" element={<SearchResultsComponent 
                        search_status={searchStatus.COMPLETED}
                        search_results={[]} 
                        on_video_select={handle_video_select}
                    />} />
                    
                    <Route path="/upload" element={<UploadComponent 
                        onUploadStateChange={handle_upload_state_change}
                        onUploadComplete={handle_upload_complete}
                    />} />
                    
                    <Route path="/video/:videoId" element={<VideoFragmentsView />} />
                </Routes>
                </div>
            </div>
        </div>
    );
};

export default AppContent;
