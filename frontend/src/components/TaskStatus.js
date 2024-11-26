import React, { useState } from "react";
import axios from "axios";

const TaskStatus = () => {
  const [taskId, setTaskId] = useState("");
  const [status, setStatus] = useState(null);

  const checkStatus = async () => {
    if (!taskId.trim()) return;
    
    try {
      const res = await axios.get(`http://localhost:8000/api/v1/tasks/${taskId}`);
      setStatus(res.data);
    } catch (error) {
      console.error("Ошибка получения статуса:", error.response?.data || error.message);
    }
  };

  return (
    <div className="component-container">
      <h2>Статус задачи</h2>
      <div className="form-container">
        <div className="form-group">
          <label>ID задачи:</label>
          <input
            type="text"
            placeholder="Введите ID задачи"
            value={taskId}
            onChange={(e) => setTaskId(e.target.value)}
            className="text-input"
          />
        </div>
        <button onClick={checkStatus} className="submit-button">
          Проверить статус
        </button>
      </div>
      {status && (
        <div className="status-container">
          <div className="status-item">
            <strong>Статус:</strong> {status.status}
          </div>
          <div className="status-item">
            <strong>Текущая операция:</strong> {status.current_operation}
          </div>
          {status.result && (
            <div className="status-result">
              <strong>Результат:</strong>
              <pre>{JSON.stringify(status.result, null, 2)}</pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default TaskStatus;
