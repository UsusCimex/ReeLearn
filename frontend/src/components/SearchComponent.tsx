import React, { useState, useEffect } from 'react';
import { searchVideos, getTaskStatus } from '../api/config';
import { SearchResult } from '../types';
import VideoPlayerComponent from './VideoPlayerComponent';

const SearchComponent: React.FC = () => {
    const [query, setQuery] = useState('');
    const [exact, setExact] = useState(false);
    const [tags, setTags] = useState('');
    const [isSearching, setIsSearching] = useState(false);
    const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
    const [error, setError] = useState<string | null>(null);
    const [taskId, setTaskId] = useState<string | null>(null);

    useEffect(() => {
        let intervalId: NodeJS.Timeout;

        const checkTaskStatus = async () => {
            if (taskId) {
                try {
                    const response = await getTaskStatus(taskId);
                    if (response.status === 'completed' && response.result) {
                        setSearchResults(response.result.results);
                        setTaskId(null); // Останавливаем опрос
                    } else if (response.status === 'failed') {
                        setError('Ошибка при выполнении поиска');
                        setTaskId(null);
                    }
                } catch (error) {
                    console.error('Error checking task status:', error);
                    setError('Ошибка при получении результатов');
                    setTaskId(null);
                }
            }
        };

        if (taskId) {
            // Проверяем статус каждые 2 секунды
            intervalId = setInterval(checkTaskStatus, 2000);
        }

        return () => {
            if (intervalId) {
                clearInterval(intervalId);
            }
        };
    }, [taskId]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!query.trim()) {
            setError('Пожалуйста, введите поисковый запрос');
            return;
        }

        setIsSearching(true);
        setError(null);
        setSearchResults([]);
        try {
            const tagList = tags.trim() ? tags.split(',').map(tag => tag.trim()) : undefined;
            const { task_id } = await searchVideos(query, exact, tagList);
            setTaskId(task_id);
        } catch (error) {
            console.error('Search error:', error);
            setError('Ошибка при выполнении поиска');
        } finally {
            setIsSearching(false);
        }
    };

    // Форматирование времени в формат MM:SS
    const formatTime = (seconds: number) => {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = Math.floor(seconds % 60);
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    };

    return (
        <div className="search-component">
            <form onSubmit={handleSubmit} className="search-form">
                <div className="form-group">
                    <input
                        type="text"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="Введите текст для поиска"
                        className="search-input"
                        required
                    />
                    <button type="submit" disabled={isSearching}>
                        {isSearching ? (
                            <>
                                Поиск
                                <span className="loading-spinner"></span>
                            </>
                        ) : (
                            'Найти'
                        )}
                    </button>
                </div>
                
                <div className="search-options">
                    <label className="checkbox-label">
                        <input
                            type="checkbox"
                            checked={exact}
                            onChange={(e) => setExact(e.target.checked)}
                        />
                        Точное совпадение
                    </label>
                    <div className="tags-input">
                        <input
                            type="text"
                            value={tags}
                            onChange={(e) => setTags(e.target.value)}
                            placeholder="Теги (через запятую)"
                        />
                    </div>
                </div>
            </form>

            {error && <div className="error-message">{error}</div>}

            {taskId && (
                <div className="search-status">
                    Выполняется поиск...
                    <span className="loading-spinner"></span>
                </div>
            )}

            <div className="search-results">
                {searchResults.map((result, index) => (
                    <div key={index} className="result-item">
                        <div className="result-info">
                            <h3>{result.video_name}</h3>
                            <p className="video-description">{result.video_description}</p>
                        </div>
                        
                        {/* Добавляем компонент видеоплеера */}
                        <div className="video-container">
                            <VideoPlayerComponent
                                url={result.presigned_url}
                                startTime={0}
                                endTime={result.timecode_end - result.timecode_start}
                            />
                        </div>

                        <div className="result-timestamp">
                            <div>Фрагмент из полного видео: {formatTime(result.timecode_start)} - {formatTime(result.timecode_end)}</div>
                            <div>Длительность: {formatTime(result.timecode_end - result.timecode_start)}</div>
                        </div>
                        
                        <div className="result-text">
                            <strong>Субтитры:</strong> {result.text}
                        </div>
                        
                        {result.tags && result.tags.length > 0 && (
                            <div className="result-tags">
                                {result.tags.map((tag, tagIndex) => (
                                    <span key={tagIndex} className="tag">
                                        {tag}
                                    </span>
                                ))}
                            </div>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
};

export default SearchComponent;
