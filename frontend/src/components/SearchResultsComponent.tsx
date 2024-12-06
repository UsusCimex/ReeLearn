import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { getTaskStatus } from '../api/config';
import { TaskStatusResponse, SearchResult } from '../types';
import VideoPlayerComponent from './VideoPlayerComponent';

const SearchResultsComponent: React.FC = () => {
    const { taskId } = useParams<{ taskId: string }>();
    const [status, setStatus] = useState<TaskStatusResponse | null>(null);

    useEffect(() => {
        if (!taskId) return;

        let intervalId: NodeJS.Timeout;

        const pollStatus = async () => {
            try {
                const response = await getTaskStatus(taskId);
                setStatus(response);

                if (['completed', 'failed'].includes(response.status)) {
                    clearInterval(intervalId);
                    return;
                }
            } catch (error) {
                console.error('Error fetching search results:', error);
                setStatus(prev => prev ? {
                    ...prev,
                    status: 'failed',
                    error: 'Failed to fetch search results'
                } : null);
                clearInterval(intervalId);
            }
        };

        intervalId = setInterval(pollStatus, 2000);
        pollStatus();

        return () => clearInterval(intervalId);
    }, [taskId]);

    if (!status) {
        return <div className="results-container">Loading search results...</div>;
    }

    if (status.status === 'failed') {
        return (
            <div className="results-container error">
                <h2>Search Failed</h2>
                <p>{status.error || 'An unknown error occurred'}</p>
            </div>
        );
    }

    if (status.status !== 'completed') {
        return (
            <div className="results-container">
                <h2>Searching Videos</h2>
                <div className="status-info">
                    <p>Status: {status.status}</p>
                    <p>Progress: {status.progress}%</p>
                    {status.current_operation && (
                        <p>Current Operation: {status.current_operation}</p>
                    )}
                </div>
            </div>
        );
    }

    if (!status.result?.results || !Array.isArray(status.result.results)) {
        return (
            <div className="results-container error">
                <h2>Invalid Results</h2>
                <p>Received invalid search results from the server</p>
            </div>
        );
    }

    const results = status.result.results as SearchResult[];

    return (
        <div className="results-container">
            <h2>Search Results</h2>
            {results.length === 0 ? (
                <p>No results found</p>
            ) : (
                <div className="results-list">
                    {results.map((result, index) => (
                        <div key={index} className="result-item">
                            <h3>{result.video_name}</h3>
                            <p className="description">{result.video_description}</p>
                            <p className="matched-text">Matched Text: {result.text}</p>
                            {result.tags && result.tags.length > 0 && (
                                <p className="tags">
                                    Tags: {result.tags.join(', ')}
                                </p>
                            )}
                            <VideoPlayerComponent
                                url={result.presigned_url}
                                startTime={result.timecode_start}
                                endTime={result.timecode_end}
                            />
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default SearchResultsComponent;
