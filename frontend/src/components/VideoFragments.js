import React, { useState } from "react";
import axios from "axios";

const VideoFragments = () => {
  const [videoId, setVideoId] = useState("");
  const [fragments, setFragments] = useState([]);
  const [error, setError] = useState("");

  const fetchFragments = async () => {
    if (!videoId.trim()) return;

    try {
      const res = await axios.get(
        `http://localhost:8000/api/v1/videos/${videoId}/fragments`
      );
      setFragments(res.data.fragments);
      setError("");
    } catch (error) {
      console.error("Ошибка получения фрагментов:", error.response?.data || error.message);
      setError("Не удалось получить фрагменты видео");
      setFragments([]);
    }
  };

  return (
    <div className="component-container">
      <h2>Фрагменты Видео</h2>
      <div className="form-container">
        <div className="form-group">
          <label>ID видео:</label>
          <input
            type="text"
            placeholder="Введите ID видео"
            value={videoId}
            onChange={(e) => setVideoId(e.target.value)}
            className="text-input"
          />
        </div>
        <button onClick={fetchFragments} className="submit-button">
          Получить фрагменты
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}
      
      <div className="fragments-container">
        {fragments.length > 0 ? (
          fragments.map((fragment) => (
            <div key={fragment.id} className="fragment-item">
              <h3>Фрагмент {fragment.id}</h3>
              <div className="fragment-content">
                <p><strong>Текст:</strong> {fragment.text}</p>
                <p><strong>Теги:</strong> {fragment.tags.join(", ")}</p>
              </div>
            </div>
          ))
        ) : (
          !error && <p>Нет доступных фрагментов</p>
        )}
      </div>
    </div>
  );
};

export default VideoFragments;
