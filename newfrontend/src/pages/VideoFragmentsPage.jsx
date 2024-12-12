import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { getVideoFragments } from '../api';
import { Typography, Grid, Card, CardContent, CircularProgress, TextField, Box } from '@mui/material';

function VideoFragmentsPage() {
  const { id } = useParams();
  const [fragments, setFragments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const [inputTerm, setInputTerm] = useState('');

  useEffect(() => {
    const fetchFragments = async () => {
      setLoading(true);
      try {
        const data = await getVideoFragments(id);
        setFragments(data.fragments);
      } catch (e) {
        setError('Ошибка при загрузке фрагментов');
      } finally {
        setLoading(false);
      }
    };
    fetchFragments();
  }, [id]);

  const highlightText = (text, term) => {
    if(!term.trim()) return text;
    const regex = new RegExp(`(${term})`, 'gi');
    return text.replace(regex, '<span style="background:yellow;">$1</span>');
  };

  // Динамическая фильтрация без Enter: searchTerm = inputTerm
  const searchTerm = inputTerm;
  
  const filteredFragments = searchTerm.trim()
    ? fragments.filter(f => f.text.toLowerCase().includes(searchTerm.toLowerCase()))
    : fragments;

  return (
    <div>
      <Typography variant="h4" gutterBottom>Фрагменты видео (ID: {id})</Typography>
      {loading && <CircularProgress />}
      {error && <Typography color="error">{error}</Typography>}
      {!loading && !error && (
        <Box sx={{ mb:2 }}>
          <TextField
            placeholder="Поиск по фрагментам..."
            variant="outlined"
            size="small"
            value={inputTerm}
            onChange={(e) => setInputTerm(e.target.value)} // сразу обновляем, без Enter
            sx={{ background:'#fff', borderRadius:1 }}
          />
        </Box>
      )}
      {filteredFragments.length === 0 && !loading && <Typography>Нет подходящих фрагментов</Typography>}
      <Grid container spacing={2}>
        {filteredFragments.map(f => {
          const highlightedText = highlightText(f.text, searchTerm);
          return (
            <Grid item xs={12} md={6} key={f.id}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="subtitle1"><b>Старт:</b> {f.timecode_start}, <b>Конец:</b> {f.timecode_end}</Typography>
                  <Typography variant="body1" sx={{mt:1}} 
                    dangerouslySetInnerHTML={{__html: highlightedText}} />
                  {f.s3_url && (
                    <video 
                      src={f.s3_url} 
                      controls 
                      style={{ width: '100%', marginTop:'10px', borderRadius:'4px' }} 
                    />
                  )}
                  <Typography variant="body2" sx={{mt:1}}><b>Теги:</b> {f.tags.join(', ')}</Typography>
                </CardContent>
              </Card>
            </Grid>
          );
        })}
      </Grid>
    </div>
  );
}

export default VideoFragmentsPage;
