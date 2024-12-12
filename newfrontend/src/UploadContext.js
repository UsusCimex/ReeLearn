import React, { createContext, useState, useEffect } from 'react';
import { getTaskStatus } from './api';

export const UploadContext = createContext();

export function UploadProvider({ children }) {
  const [uploads, setUploads] = useState([]); 
  // Формат: [{ taskId: string, status: string, progress: number }, ...]

  // Периодически опрашиваем состояние загрузок
  useEffect(() => {
    const interval = setInterval(async () => {
      if (uploads.length === 0) return;
      const updated = [];
      for (let u of uploads) {
        if (u.status === 'completed' || u.status === 'failed') {
          updated.push(u); // Не обновляем завершенные, просто храним их
        } else {
          try {
            const res = await getTaskStatus(u.taskId);
            updated.push({
              ...u,
              status: res.status,
              progress: res.progress || 0
            });
          } catch (e) {
            updated.push(u);
          }
        }
      }
      setUploads(updated);
    }, 3000);
    return () => clearInterval(interval);
  }, [uploads]);

  const addUpload = (taskId) => {
    setUploads(prev => [...prev, { taskId, status: 'uploading', progress: 0 }]);
  };

  return (
    <UploadContext.Provider value={{ uploads, addUpload }}>
      {children}
    </UploadContext.Provider>
  );
}
