// components/VideoSelectors.js
import React from 'react';

const VideoSelectors = ({ videoUrls, currentVideoIndex, handleVideoSelect, handleNextVideo, handlePrevVideo }) => {
  const visibleButtons = 5; // Количество видимых кнопок
  const startIndex = Math.max(0, currentVideoIndex - Math.floor(visibleButtons / 2)); // Вычисляем начальный индекс
  const endIndex = Math.min(videoUrls.length, startIndex + visibleButtons); // Конечный индекс

  return (
    <div className="video-selectors">
      {/* Кнопка "предыдущее видео" */}
      <button onClick={handlePrevVideo} disabled={currentVideoIndex === 0}>
        &lt; {/* Это символ '<' */}
      </button>

      {/* Нумерация видео */}
      {videoUrls.slice(startIndex, endIndex).map((url, index) => (
        <button
          key={index + startIndex}
          onClick={() => handleVideoSelect(index + startIndex)}
          className={currentVideoIndex === index + startIndex ? 'active' : ''}
        >
          {index + startIndex + 1}
        </button>
      ))}

      {/* Кнопка "следующее видео" */}
      <button onClick={handleNextVideo} disabled={currentVideoIndex === videoUrls.length - 1}>
        &gt; {/* Это символ '>' */}
      </button>
    </div>
  );
};

export default VideoSelectors;
