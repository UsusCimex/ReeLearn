import React, { useState } from 'react';
import { Routes, Route, useNavigate } from 'react-router-dom';
import Navigation from './components/Navigation';
import SearchResultsComponent from './components/SearchResultsComponent';
import VideoFragmentsView from './components/VideoFragmentsView';
import { searchStatus, uploadState } from './types';
import './styles/AppContent.css';

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
                        <Route path="/video/:id" element={<VideoFragmentsView />} />
                        <Route path="/results" element={
                            <SearchResultsComponent
                                on_video_select={handle_video_select}
                                search_status={searchStatus.COMPLETED}
                            />
                        } />
                        <Route path="/" element={<div>Welcome to Video Processing App</div>} />
                    </Routes>
                </div>
            </div>
        </div>
    );
};

export default AppContent;
