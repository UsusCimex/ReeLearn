import React from 'react';
import { logInfo } from '../utils/logger';

const SearchBar = ({ searchQuery, setSearchQuery, handleSearch, inputRef, spanRef }) => {
  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      logInfo(`Search triggered: ${searchQuery}`);
      handleSearch();
    }
  };

  return (
    <div className="search-container">
      <input
        ref={inputRef}
        type="text"
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Введите поисковый запрос"
        className="search-input"
      />
      <span ref={spanRef} className="hidden-span">
        {searchQuery || 'Введите поисковый запрос'}
      </span>
    </div>
  );
};

export default SearchBar;
