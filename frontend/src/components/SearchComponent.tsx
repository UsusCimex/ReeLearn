import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { searchVideos } from '../api/api';
import { TaskResponse } from '../types';
import '../styles/SearchComponent.css';

const SearchComponent: React.FC = () => {
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleSearch = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setIsLoading(true);
    try {
      const response: TaskResponse = await searchVideos(query.trim());
      if (response.task_id) {
        navigate(`/search/${response.task_id}`);
      }
    } catch (error) {
      console.error('Error initiating search:', error);
    } finally {
      setIsLoading(false);
    }
  }, [query, navigate]);

  return (
    <form className="search-container" onSubmit={handleSearch}>
      <div className="search-input-container">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Поиск по видео..."
          className="search-input"
          disabled={isLoading}
        />
        <button 
          type="submit" 
          className="search-button"
          disabled={isLoading || !query.trim()}
        >
          {isLoading ? (
            <span className="loading-spinner" />
          ) : (
            'Поиск'
          )}
        </button>
      </div>
    </form>
  );
};

export default SearchComponent;
