import React, { useState, useContext } from 'react';
import { uploadVideo } from '../api';
import { UploadContext } from '../UploadContext';
import { Dialog, DialogTitle, DialogContent, DialogActions, TextField, Button, Typography } from '@mui/material';

function UploadModal({ onClose }) {
  const { addUpload } = useContext(UploadContext);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [file, setFile] = useState(null);
  const [error, setError] = useState(null);

  const handleUpload = async () => {
    if (!file || !name.trim()) {
      setError('Укажите имя и выберите файл');
      return;
    }
    setError(null);
    const formData = new FormData();
    formData.append('video_file', file);
    formData.append('name', name);
    if (description) formData.append('description', description);

    try {
      const res = await uploadVideo(formData);
      addUpload(res.task_id);
      onClose(); 
    } catch (e) {
      setError('Ошибка при загрузке');
    }
  };

  return (
    <Dialog open onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle>Загрузить видео</DialogTitle>
      <DialogContent dividers>
        <TextField
          label="Название"
          fullWidth
          value={name}
          onChange={(e) => setName(e.target.value)}
          sx={{ my: 2 }}
        />
        <TextField
          label="Описание"
          fullWidth
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          sx={{ mb: 2 }}
        />
        <Button variant="contained" component="label">
          Выбрать файл
          <input
            type="file"
            hidden
            onChange={(e) => setFile(e.target.files[0])}
          />
        </Button>
        {file && <Typography sx={{mt:1}}>{file.name}</Typography>}
        {error && <Typography color="error" sx={{mt:2}}>{error}</Typography>}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Отмена</Button>
        <Button onClick={handleUpload} variant="contained">Начать загрузку</Button>
      </DialogActions>
    </Dialog>
  );
}

export default UploadModal;
