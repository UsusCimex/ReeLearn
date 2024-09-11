// hooks/useVideoApp.js
import { useState, useEffect, useRef, useCallback } from 'react';
import { logInfo, logError } from '../utils/logger';

export const useVideoApp = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearchSubmitted, setIsSearchSubmitted] = useState(false);
  const [isVideoDisplayed, setIsVideoDisplayed] = useState(false);
  const [videoUrls, setVideoUrls] = useState([]);
  const [currentVideoIndex, setCurrentVideoIndex] = useState(0);
  const [errorMessage, setErrorMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const spanRef = useRef(null);
  const inputRef = useRef(null); 
  const videoRef = useRef(null);

  useEffect(() => {
    if (spanRef.current) {
      inputRef.current.style.width = `${spanRef.current.offsetWidth + 10}px`;
    }
  }, [searchQuery]);

  const handleSearch = useCallback(async () => {
    setErrorMessage('');
    setIsVideoDisplayed(false);

    if (!searchQuery) return;

    setIsLoading(true);
    logInfo(`Search query: ${searchQuery}`);

    try {
      const response = await fetch(
        `http://localhost:5000/search?query=${searchQuery}`
      );
      const data = await response.json();
      
      if (data.results && data.results.length > 0) {
        setVideoUrls(data.results.map(result => ({
          url: `http://localhost:5000/download?url=${result.url}`,
          name: result.name,
          timecode: result.timecode,
        })));
        setCurrentVideoIndex(0);
        setIsSearchSubmitted(true);

        // Снимаем фокус с поисковой строки после успешного поиска
        inputRef.current.blur();

        setTimeout(() => {
          setIsVideoDisplayed(true);
        }, 500);

        logInfo(`Videos found: ${data.results.length}`);
      } else {
        throw new Error('Видео не найдено');
      }
    } catch (error) {
      logError(`Error fetching videos: ${error.message}`);
      setErrorMessage('Ошибка при получении видео: Видео не найдено');
      setIsSearchSubmitted(false);
      setIsVideoDisplayed(false);
    } finally {
      setIsLoading(false);
    }
  }, [searchQuery]);

  const handleNextVideo = useCallback(() => {
    if (currentVideoIndex < videoUrls.length - 1) {
      setCurrentVideoIndex(currentVideoIndex + 1);
      logInfo(`Next video: ${currentVideoIndex + 1}`);
    }
  }, [currentVideoIndex, videoUrls.length]);

  const handlePrevVideo = useCallback(() => {
    if (currentVideoIndex > 0) {
      setCurrentVideoIndex(currentVideoIndex - 1);
      logInfo(`Previous video: ${currentVideoIndex - 1}`);
    }
  }, [currentVideoIndex]);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && document.activeElement === inputRef.current) {
        inputRef.current.blur();
      }
      if (document.activeElement !== inputRef.current) {
        switch (e.key) {
          case 'Control':
            e.preventDefault();
            inputRef.current.focus();
            break;
          case ' ':
            e.preventDefault();
            if (videoRef.current) {
              if (videoRef.current.paused) {
                videoRef.current.play();
              } else {
                videoRef.current.pause();
              }
            }
            break;
          case 'ArrowRight':
            handleNextVideo();
            break;
          case 'ArrowLeft':
            handlePrevVideo();
            break;
          default:
            break;
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [handleNextVideo, handlePrevVideo]);

  return {
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
  };
};
