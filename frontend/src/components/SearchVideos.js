import React, { useState } from "react";
import axios from "axios";

const SearchVideos = () => {
  const [query, setQuery] = useState("");
  const [exact, setExact] = useState(false);
  const [tags, setTags] = useState("");
  const [taskId, setTaskId] = useState(null);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    const params = {
      query,
      exact,
      tags: tags ? tags.split(",").map(tag => tag.trim()) : null,
    };

    try {
      const res = await axios.get("http://localhost:8000/api/v1/search", { params });
      setTaskId(res.data.task_id);
      setError("");
    } catch (error) {
      console.error("Ошибка поиска:", error.response?.data || error.message);
      setError("Ошибка при выполнении поиска");
      setTaskId(null);
    }
  };

  return (
    <div className="component-container">
      <h2>Поиск Видео</h2>
      <form onSubmit={handleSubmit} className="form-container">
        <div className="form-group">
          <label>Поисковый запрос:</label>
          <input
            type="text"
            placeholder="Введите запрос"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            required
            className="text-input"
          />
        </div>
        <div className="form-group checkbox-group">
          <label>
            <input
              type="checkbox"
              checked={exact}
              onChange={() => setExact(!exact)}
              className="checkbox-input"
            />
            Точное совпадение
          </label>
        </div>
        <div className="form-group">
          <label>Теги:</label>
          <input
            type="text"
            placeholder="Введите теги через запятую"
            value={tags}
            onChange={(e) => setTags(e.target.value)}
            className="text-input"
          />
        </div>
        <button type="submit" className="submit-button">Искать</button>
      </form>
      
      {error && (
        <div className="error-message">
          {error}
        </div>
      )}
      
      {taskId && (
        <div className="response-container">
          <p>Поиск начат!</p>
          <p>ID задачи: {taskId}</p>
          <p>Используйте этот ID в разделе "Статус задачи" для просмотра результатов</p>
        </div>
      )}
    </div>
  );
};

export default SearchVideos;
