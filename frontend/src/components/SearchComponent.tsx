import React, { useState, useEffect, useCallback } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { searchVideos, checkTaskStatus } from '../api/api';
import { searchResult, taskStatus, searchResponse } from '../types';
import '../styles/SearchComponent.css';

interface search_component_props {
  on_results_found?: (results: searchResult[]) => void;
}

const SearchComponent: React.FC<search_component_props> = ({ on_results_found }) => {
  const [query, setQuery] = useState('');
  const [search_results, setSearchResults] = useState<searchResult[]>([]);
  const [is_loading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const location = useLocation();
  const navigate = useNavigate();

  const check_search_status = useCallback(async (task_id: string) => {
    try {
      const status = await checkTaskStatus(task_id);
      
      if (status.status === taskStatus.COMPLETED && status.result) {
        const search_response = status.result as searchResponse;
        if (search_response.results) {
          setSearchResults(search_response.results);
          if (on_results_found) {
            on_results_found(search_response.results);
          }
          setIsLoading(false);
        } else {
          setError('Invalid search results format');
          setIsLoading(false);
        }
      } else if (status.status === taskStatus.FAILED) {
        setError('Search failed: ' + (status.error || 'Unknown error'));
        setIsLoading(false);
      } else if (status.status === taskStatus.PENDING || status.status === taskStatus.PROGRESS) {
        // Still processing, check again in 2 seconds
        setTimeout(() => check_search_status(task_id), 2000);
      }
    } catch (error) {
      if (error instanceof Error) {
        setError(error.message);
      } else {
        setError('Failed to check search status');
      }
      setIsLoading(false);
    }
  }, [on_results_found]);

  const handle_search = useCallback(async (e?: React.FormEvent) => {
    if (e) {
      e.preventDefault();
    }

    if (!query.trim()) {
      setError('Please enter a search query');
      return;
    }

    setIsLoading(true);
    setError(null);
    setSearchResults([]);

    try {
      const response = await searchVideos(query);
      check_search_status(response.task_id);
      // Update URL with search query
      navigate(`/search?query=${encodeURIComponent(query.trim())}`, { replace: true });
    } catch (error) {
      setError('Failed to start search');
      setIsLoading(false);
    }
  }, [query, check_search_status, navigate]);

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const query_param = params.get('query');
    if (query_param && query_param !== query) {
      setQuery(query_param);
      handle_search();
    }
  }, [location.search, query, handle_search]);

  return (
    <div className="search-container">
      <form onSubmit={handle_search} className="search-form">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search videos..."
          className="search-input"
        />
        <button type="submit" disabled={is_loading} className="search-button">
          {is_loading ? 'Searching...' : 'Search'}
        </button>
      </form>

      {error && <div className="error-message">{error}</div>}

      {is_loading && <div className="loading-message">Searching...</div>}

      {search_results.length > 0 && (
        <div className="search-results">
          {search_results.map((result) => (
            <div key={result.video_id} className="search-result-item">
              <h3>{result.name}</h3>
              <p>Status: {result.status}</p>
              <p>Fragments: {result.fragments_count}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default SearchComponent;
