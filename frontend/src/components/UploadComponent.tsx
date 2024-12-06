import React, { useState, useRef, useEffect } from 'react';
import { uploadVideo, getTaskStatus } from '../api/config';
import { TaskStatusResponse } from '../types';

const UploadComponent: React.FC = () => {
    const [file, setFile] = useState<File | null>(null);
    const [uploading, setUploading] = useState(false);
    const [uploadProgress, setUploadProgress] = useState(0);
    const [error, setError] = useState<string | null>(null);
    const [name, setName] = useState('');
    const [description, setDescription] = useState('');
    const [taskId, setTaskId] = useState<string | null>(null);
    const [taskStatus, setTaskStatus] = useState<TaskStatusResponse | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const statusCheckInterval = useRef<NodeJS.Timeout>();

    // Очистка формы
    const resetForm = () => {
        setFile(null);
        setName('');
        setDescription('');
        setUploadProgress(0);
        setTaskId(null);
        setTaskStatus(null);
        setUploading(false);
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };

    // Эффект для отслеживания состояния задачи
    useEffect(() => {
        if (taskId) {
            const checkStatus = async () => {
                try {
                    const status = await getTaskStatus(taskId);
                    setTaskStatus(status);
                    
                    if (status.status === 'completed' || status.status === 'failed') {
                        if (statusCheckInterval.current) {
                            clearInterval(statusCheckInterval.current);
                        }
                        
                        if (status.status === 'failed') {
                            setError('Ошибка при обработке видео: ' + status.error);
                            setTaskId(null);
                            setUploading(false);
                        } else {
                            // При успешном завершении
                            setTimeout(() => {
                                resetForm();
                            }, 2000); // Показываем сообщение об успехе 2 секунды
                        }
                    }
                } catch (error) {
                    console.error('Error checking task status:', error);
                    setError('Ошибка при проверке статуса задачи');
                    if (statusCheckInterval.current) {
                        clearInterval(statusCheckInterval.current);
                    }
                    setTaskId(null);
                    setUploading(false);
                }
            };

            // Проверяем статус каждые 2 секунды
            statusCheckInterval.current = setInterval(checkStatus, 2000);
            checkStatus(); // Первая проверка сразу

            return () => {
                if (statusCheckInterval.current) {
                    clearInterval(statusCheckInterval.current);
                }
            };
        }
    }, [taskId]);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            const selectedFile = e.target.files[0];
            setFile(selectedFile);
            // Автоматически устанавливаем имя файла как название
            setName(selectedFile.name.split('.')[0]);
            setError(null);
        }
    };

    const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
        e.preventDefault();
        e.stopPropagation();

        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            const droppedFile = e.dataTransfer.files[0];
            setFile(droppedFile);
            // Автоматически устанавливаем имя файла как название
            setName(droppedFile.name.split('.')[0]);
            setError(null);
        }
    };

    const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
        e.preventDefault();
        e.stopPropagation();
    };

    const handleUpload = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!file) {
            setError('Пожалуйста, выберите файл для загрузки');
            return;
        }
        if (!name.trim()) {
            setError('Пожалуйста, укажите название видео');
            return;
        }

        setUploading(true);
        setError(null);
        try {
            const formData = new FormData();
            formData.append('video_file', file);
            formData.append('name', name);
            if (description.trim()) {
                formData.append('description', description);
            }

            const response = await uploadVideo(formData, (progress) => {
                setUploadProgress(progress);
            });

            // Получаем task_id из ответа и начинаем отслеживание
            if (response.task_id) {
                setTaskId(response.task_id);
            } else {
                throw new Error('Не получен ID задачи от сервера');
            }

        } catch (error) {
            console.error('Upload error:', error);
            setError('Ошибка при загрузке видео');
            setUploading(false);
            setTaskId(null);
        }
    };

    const getStatusMessage = () => {
        if (!taskStatus) return '';
        
        if (taskStatus.status === 'pending') {
            return 'Ожидание обработки...';
        } else if (taskStatus.status === 'processing') {
            return `${taskStatus.current_operation || 'Обработка видео'} (${taskStatus.progress}%)`;
        } else if (taskStatus.status === 'completed') {
            return 'Видео успешно обработано!';
        } else if (taskStatus.status === 'failed') {
            return `Ошибка: ${taskStatus.error || 'Неизвестная ошибка'}`;
        }
        
        return '';
    };

    // Определяем, заблокирована ли кнопка
    const isButtonDisabled = !file || uploading;

    // Определяем текст кнопки
    const getButtonText = () => {
        if (uploading) {
            if (!taskId) {
                return 'Загрузка файла...';
            }
            if (taskStatus?.status === 'pending') {
                return 'Ожидание обработки...';
            }
            if (taskStatus?.status === 'processing') {
                return 'Обработка видео...';
            }
            if (taskStatus?.status === 'completed') {
                return 'Загрузка завершена!';
            }
            if (taskStatus?.status === 'failed') {
                return 'Ошибка загрузки';
            }
            return 'Загрузка...';
        }
        return 'Загрузить видео';
    };

    return (
        <div className="upload-component">
            <form onSubmit={handleUpload}>
                <div
                    className="upload-area"
                    onDrop={handleDrop}
                    onDragOver={handleDragOver}
                >
                    <label>
                        <input
                            type="file"
                            onChange={handleFileChange}
                            accept="video/*"
                            ref={fileInputRef}
                            className="file-input"
                            disabled={uploading}
                        />
                        <div className="upload-icon">
                            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                                <polyline points="17 8 12 3 7 8" />
                                <line x1="12" y1="3" x2="12" y2="15" />
                            </svg>
                        </div>
                        <span>Перетащите видео сюда или нажмите для выбора</span>
                    </label>

                    {file && (
                        <div className="file-info">
                            <span>{file.name}</span>
                            <span className="file-size">
                                {(file.size / (1024 * 1024)).toFixed(2)} MB
                            </span>
                        </div>
                    )}
                </div>

                <div className="form-fields">
                    <div className="form-group">
                        <label htmlFor="name">Название видео</label>
                        <input
                            type="text"
                            id="name"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            placeholder="Введите название видео"
                            required
                            disabled={uploading}
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="description">Описание</label>
                        <textarea
                            id="description"
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            placeholder="Добавьте описание (необязательно)"
                            disabled={uploading}
                        />
                    </div>
                </div>

                {error && <div className="error-message">{error}</div>}

                {(uploading || taskStatus) && (
                    <div className="upload-progress">
                        {taskId ? (
                            <div className="task-status">
                                <div className="status-message">{getStatusMessage()}</div>
                                {taskStatus && taskStatus.status === 'processing' && (
                                    <div className="progress-bar-wrapper">
                                        <div 
                                            className="progress-bar"
                                            style={{ width: `${taskStatus.progress}%` }}
                                        />
                                    </div>
                                )}
                            </div>
                        ) : (
                            <>
                                <div 
                                    className="progress-bar"
                                    style={{ width: `${uploadProgress}%` }}
                                />
                                <span className="progress-text">{uploadProgress}% загружено</span>
                            </>
                        )}
                    </div>
                )}

                <button 
                    type="submit" 
                    disabled={isButtonDisabled}
                    className={`upload-button ${uploading ? 'uploading' : ''}`}
                >
                    {getButtonText()}
                    {uploading && <span className="loading-spinner"></span>}
                </button>
            </form>
        </div>
    );
};

export default UploadComponent;
