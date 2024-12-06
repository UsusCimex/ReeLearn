import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { searchVideos } from '../api/config';

const SearchComponent: React.FC = () => {
    const [query, setQuery] = useState('');
    const [exact, setExact] = useState(false);
    const [tags, setTags] = useState('');
    const [isSearching, setIsSearching] = useState(false);
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!query.trim()) {
            alert('Пожалуйста, введите поисковый запрос');
            return;
        }

        setIsSearching(true);
        try {
            const tagList = tags.trim() ? tags.split(',').map(tag => tag.trim()) : undefined;
            const response = await searchVideos(query, exact, tagList);
            navigate(`/search-results/${response.task_id}`);
        } catch (error) {
            console.error('Search error:', error);
            alert('Ошибка при выполнении поиска');
        } finally {
            setIsSearching(false);
        }
    };

    return (
        <div className="search-container">
            <h2>Поиск видео</h2>
            <form onSubmit={handleSubmit}>
                <div className="form-group">
                    <label htmlFor="query">Поисковый запрос:</label>
                    <input
                        type="text"
                        id="query"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="Введите текст для поиска"
                        required
                    />
                </div>
                <div className="form-group checkbox">
                    <label>
                        <input
                            type="checkbox"
                            checked={exact}
                            onChange={(e) => setExact(e.target.checked)}
                        />
                        Точное совпадение
                    </label>
                </div>
                <div className="form-group">
                    <label htmlFor="tags">Фильтр по тегам:</label>
                    <input
                        type="text"
                        id="tags"
                        value={tags}
                        onChange={(e) => setTags(e.target.value)}
                        placeholder="тег1, тег2, тег3"
                    />
                </div>
                <button type="submit" disabled={isSearching}>
                    {isSearching ? 'Поиск...' : 'Найти'}
                </button>
            </form>
        </div>
    );
};

export default SearchComponent;
