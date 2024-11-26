import React, { useState } from "react";
import axios from "axios";

const UploadVideo = () => {
  const [videoFile, setVideoFile] = useState(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [response, setResponse] = useState(null);

  const handleFileChange = (e) => {
    setVideoFile(e.target.files[0]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const formData = new FormData();
    formData.append("video_file", videoFile);
    formData.append("name", name);
    formData.append("description", description);

    try {
      const res = await axios.post("http://localhost:8000/api/v1/upload", formData);
      setResponse(res.data);
    } catch (error) {
      console.error("Ошибка загрузки:", error.response?.data || error.message);
    }
  };

  return (
    <div className="component-container">
      <h2>Загрузить Видео</h2>
      <form onSubmit={handleSubmit} className="form-container">
        <div className="form-group">
          <label>Выберите файл:</label>
          <input type="file" onChange={handleFileChange} required className="file-input" />
        </div>
        <div className="form-group">
          <label>Название:</label>
          <input
            type="text"
            placeholder="Название видео"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            className="text-input"
          />
        </div>
        <div className="form-group">
          <label>Описание:</label>
          <textarea
            placeholder="Описание видео"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="textarea-input"
          />
        </div>
        <button type="submit" className="submit-button">Загрузить</button>
      </form>
      {response && (
        <div className="response-container">
          <p>Загрузка началась!</p>
          <p>Task ID: {response.task_id}</p>
        </div>
      )}
    </div>
  );
};

export default UploadVideo;
