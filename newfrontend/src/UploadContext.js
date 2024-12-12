import React, { createContext, useState } from 'react';

export const UploadContext = createContext();

export function UploadProvider({ children }) {
  const [uploads, setUploads] = useState([]); 
  // Формат upload: { taskId, status, progress }

  // Добавляем загрузку
  const addUpload = (task) => {
    // task = { taskId, status, progress }
    setUploads(prev => [...prev, task]);
  };

  const updateUpload = (taskId, newStatus, newProgress=0) => {
    setUploads(prev => prev.map(u => u.taskId === taskId ? {...u, status:newStatus, progress:newProgress} : u));
  };

  return (
    <UploadContext.Provider value={{ uploads, addUpload, updateUpload }}>
      {children}
    </UploadContext.Provider>
  );
}
