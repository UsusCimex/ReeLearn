import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import '../styles/HomePage.css';

interface RecentSearch {
  query: string;
  timestamp: number;
}

export const HomePage: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [recentSearches, setRecentSearches] = useState<RecentSearch[]>([]);
  const navigate = useNavigate();

  useEffect(() => {
    const savedSearches = localStorage.getItem('recentSearches');
    if (savedSearches) {
      setRecentSearches(JSON.parse(savedSearches));
    }
  }, []);

  const saveRecentSearch = (query: string) => {
    const newSearch: RecentSearch = {
      query,
      timestamp: Date.now(),
    };

    const updatedSearches = [newSearch, ...recentSearches.filter(s => s.query !== query)]
      .slice(0, 5);

    setRecentSearches(updatedSearches);
    localStorage.setItem('recentSearches', JSON.stringify(updatedSearches));
  };

  const handleSearch = async (query: string) => {
    if (!query.trim()) return;

    setIsLoading(true);
    try {
      saveRecentSearch(query);
      navigate(`/search?q=${encodeURIComponent(query)}`);
    } catch (error) {
      console.error('Error during search:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSearch(searchQuery);
  };

  const clearHistory = () => {
    setRecentSearches([]);
    localStorage.removeItem('recentSearches');
  };

  const formatTimestamp = (timestamp: number) => {
    const date = new Date(timestamp);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  };

  return (
    <div className="home-container">
      <div className="search-section">
        <h1 className="search-title">ReeLearn Search</h1>
        <p className="search-description">
          Search through video lectures and find relevant fragments
        </p>

        <form onSubmit={handleSubmit}>
          <div className="search-input-container">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Enter your search query..."
              disabled={isLoading}
            />
            <button
              type="submit"
              className={`search-button ${isLoading ? 'loading' : ''}`}
              disabled={isLoading || !searchQuery.trim()}
            >
              {isLoading ? (
                <div className="loading-spinner" />
              ) : (
                'Search'
              )}
            </button>
          </div>
        </form>

        {recentSearches.length > 0 && (
          <div className="recent-searches">
            <div className="recent-searches-header">
              <h2 className="recent-searches-title">Recent Searches</h2>
              <button className="clear-history" onClick={clearHistory}>
                Clear History
              </button>
            </div>
            <div className="recent-searches-list">
              {recentSearches.map((search, index) => (
                <div
                  key={index}
                  className="recent-search-item"
                  onClick={() => handleSearch(search.query)}
                >
                  <span className="recent-search-text">{search.query}</span>
                  <span className="recent-search-time">
                    {formatTimestamp(search.timestamp)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default HomePage;
