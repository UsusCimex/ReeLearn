// App.js
import React from 'react';
import './App.css';
import './styles/LoadingOverlay.css';
import './styles/SearchBar.css';
import './styles/VideoPlayer.css';
import './styles/VideoSelectors.css';
import './styles/ErrorToast.css';
import ErrorToast from './components/ErrorToast';
import SearchBar from './components/SearchBar';
import VideoPlayer from './components/VideoPlayer';
import VideoSelectors from './components/VideoSelectors';
import { useVideoApp } from './hooks/useVideoApp';

const App = () => {
  const {
    searchQuery,
    setSearchQuery,
    isSearchSubmitted,
    isVideoDisplayed,
    videoUrls,
    currentVideoIndex,
    errorMessage,
    isLoading,
    inputRef,
    spanRef,
    videoRef,
    handleSearch,
    handleNextVideo,
    handlePrevVideo,
    setCurrentVideoIndex,
    setErrorMessage,
  } = useVideoApp();

  return (
    <div className={`app ${isSearchSubmitted ? 'app-searching' : ''}`}>
      {errorMessage && (
        <ErrorToast 
          message={errorMessage} 
          onClose={() => setErrorMessage('')}
        />
      )}

      <SearchBar
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        handleSearch={handleSearch}
        inputRef={inputRef}
        spanRef={spanRef}
      />

      {isLoading && (
        <div className="loading-overlay">
          <div className="loading-spinner"></div>
        </div>
      )}

      {!errorMessage && isVideoDisplayed && videoUrls.length > 0 && (
        <div className="video-container">
          <VideoPlayer
            videoUrl={videoUrls[currentVideoIndex]}
            handleNextVideo={handleNextVideo}
            currentVideoIndex={currentVideoIndex}
            totalVideos={videoUrls.length}
            videoRef={videoRef}
          />
          <VideoSelectors
            videoUrls={videoUrls}
            currentVideoIndex={currentVideoIndex}
            handleVideoSelect={(index) => setCurrentVideoIndex(index)}
            handleNextVideo={handleNextVideo}
            handlePrevVideo={handlePrevVideo}
          />
        </div>
      )}
    </div>
  );
};

export default App;
