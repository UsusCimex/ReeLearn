import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { uploadVideo } from '../api/config';
import { VideoMetadata } from '../types';

const UploadComponent: React.FC = () => {
    const [videoFile, setVideoFile] = useState<File | null>(null);
    const [metadata, setMetadata] = useState<VideoMetadata>({
        name: '',
        description: '',
        tags: [],
    });
    const [isUploading, setIsUploading] = useState(false);
    const navigate = useNavigate();

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setVideoFile(e.target.files[0]);
        }
    };

    const handleMetadataChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
        const { name, value } = e.target;
        setMetadata((prev: VideoMetadata) => ({
            ...prev,
            [name]: value,
        }));
    };

    const handleTagsChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const tags = e.target.value.split(',').map(tag => tag.trim());
        setMetadata((prev: VideoMetadata) => ({
            ...prev,
            tags,
        }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!videoFile || !metadata.name) {
            alert('Пожалуйста, выберите видеофайл и укажите название');
            return;
        }

        setIsUploading(true);
        try {
            const formData = new FormData();
            formData.append('video_file', videoFile);
            formData.append('name', metadata.name);
            formData.append('description', metadata.description);
            if (metadata.tags && metadata.tags.length > 0) {
                formData.append('tags', JSON.stringify(metadata.tags));
            }

            const response = await uploadVideo(formData);
            navigate(`/upload-status/${response.task_id}`);
        } catch (error) {
            console.error('Upload error:', error);
            alert('Ошибка при загрузке видео');
        } finally {
            setIsUploading(false);
        }
    };

    return (
        <div className="upload-container">
            <h2>Загрузка видео</h2>
            <form onSubmit={handleSubmit}>
                <div className="form-group">
                    <label htmlFor="video">Видеофайл:</label>
                    <input
                        type="file"
                        id="video"
                        accept="video/*"
                        onChange={handleFileChange}
                        required
                    />
                </div>
                <div className="form-group">
                    <label htmlFor="name">Название:</label>
                    <input
                        type="text"
                        id="name"
                        name="name"
                        value={metadata.name}
                        onChange={handleMetadataChange}
                        required
                    />
                </div>
                <div className="form-group">
                    <label htmlFor="description">Описание:</label>
                    <textarea
                        id="description"
                        name="description"
                        value={metadata.description}
                        onChange={handleMetadataChange}
                    />
                </div>
                <div className="form-group">
                    <label htmlFor="tags">Теги (через запятую):</label>
                    <input
                        type="text"
                        id="tags"
                        value={metadata.tags.join(', ')}
                        onChange={handleTagsChange}
                        placeholder="тег1, тег2, тег3"
                    />
                </div>
                <button type="submit" disabled={isUploading}>
                    {isUploading ? 'Загрузка...' : 'Загрузить'}
                </button>
            </form>
        </div>
    );
};

export default UploadComponent;
