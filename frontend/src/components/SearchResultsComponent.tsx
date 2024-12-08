import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getTaskStatus } from '../api/api';
import { TaskStatus } from '../types';
import '../styles/SearchResultsComponent.css';

const SearchResultsComponent: React.FC = () => {
  const { taskId } = useParams<{ taskId: string }>();
  const [status, setStatus] = useState<TaskStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedResult, setSelectedResult] = useState<any>(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (!taskId) {
      setError('No task ID provided');
      return;
    }

    const pollStatus = async () => {
      try {
        const response = await getTaskStatus(taskId);
        setStatus(response);

        if (response.status === 'completed' && Array.isArray(response.result) && response.result.length > 0) {
          setSelectedResult(response.result[0]);
        } else if (response.status === 'failed') {
          setError(response.error || 'An error occurred while processing the request');
        }

        if (response.status === 'pending' || response.status === 'progress') {
          setTimeout(pollStatus, 2000);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
      }
    };

    pollStatus();
  }, [taskId]);

  if (error) {
    return (
      <div className="search-results error">
        <h2>Error</h2>
        <p>{error}</p>
        <button onClick={() => navigate('/')}>Back to Search</button>
      </div>
    );
  }

  if (!status || status.status === 'pending' || status.status === 'progress') {
    return (
      <div className="search-results loading">
        <h2>Processing Search</h2>
        <p>{status?.current_operation || 'Please wait...'}</p>
        <div className="progress-bar">
          <div 
            className="progress-bar-fill"
            style={{ width: `${status?.progress || 0}%` }}
          />
        </div>
      </div>
    );
  }

  if (status.status === 'completed' && selectedResult) {
    return (
      <div className="search-results">
        <h2>Search Results</h2>
        <div className="results-container">
          {/* Отображение результатов поиска */}
          <div className="result-item">
            <h3>{selectedResult.title}</h3>
            <p>{selectedResult.description}</p>
            {/* Дополнительная информация о результате */}
          </div>
        </div>
        <button onClick={() => navigate('/')}>Back to Search</button>
      </div>
    );
  }

  return (
    <div className="search-results empty">
      <h2>No Results Found</h2>
      <p>Try modifying your search query</p>
      <button onClick={() => navigate('/')}>Back to Search</button>
    </div>
  );
};

export default SearchResultsComponent;
