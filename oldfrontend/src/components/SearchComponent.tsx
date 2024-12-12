import React, { useState, useCallback, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { searchVideos } from '../api/api';
import { searchResult, taskStatus, searchResponse, searchStatus } from '../types';
import '../styles/SearchComponent.css';

interface SearchComponentProps {
  onResultsFound?: (results: searchResult[]) => void;
}

const SearchComponent: React.FC<SearchComponentProps> = ({ onResultsFound }) => {
  const [query, setQuery] = useState('');
  const [searchResults, setSearchResults] = useState<searchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState<number>(0);
  const location = useLocation();
  const navigate = useNavigate();

  const handleSearch = useCallback(async (e?: React.FormEvent) => {
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
    setProgress(0);

    try {
      const results = await searchVideos(query);

      if (results.results) {
        setSearchResults(results.results);
        if (onResultsFound) {
          onResultsFound(results.results);
        }
      } else {
        setError('No results found');
      }
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Search failed');
    } finally {
      setIsLoading(false);
      setProgress(0);
    }
  }, [query, onResultsFound]);

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const queryParam = params.get('query');
    if (queryParam && queryParam !== query) {
      setQuery(queryParam);
      handleSearch();
    }
  }, [location.search, query, handleSearch]);

  return (
    <div className="search-container">
      <form onSubmit={handleSearch} className="search-form">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search videos..."
          className="search-input"
          disabled={isLoading}
        />
        <button type="submit" disabled={isLoading} className="search-button">
          {isLoading ? 'Searching...' : 'Search'}
        </button>
      </form>

      {error && <div className="error-message">{error}</div>}

      {isLoading && (
        <div className="search-progress">
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${progress}%` }}
            />
          </div>
          <div className="progress-text">
            Searching... {progress > 0 ? `${Math.round(progress)}%` : ''}
          </div>
        </div>
      )}

      {searchResults.length > 0 && (
        <div className="search-results">
          {searchResults.map((result) => (
            <div key={result.video_id} className="search-result-item">
              <h3>{result.name}</h3>
              <p>Status: {result.status}</p>
              <p>Fragments: {result.fragments_count}</p>
            </div>
          ))}
        </div>
      )}

      {!isLoading && searchResults.length === 0 && query && !error && (
        <div className="no-results">No videos found matching your search.</div>
      )}
    </div>
  );
};

export default SearchComponent;
