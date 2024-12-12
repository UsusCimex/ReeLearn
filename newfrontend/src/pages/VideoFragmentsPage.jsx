import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { getVideoFragments } from '../api';
import { Typography, Grid, Card, CardContent, CircularProgress } from '@mui/material';

function VideoFragmentsPage() {
  const { id } = useParams();
  const [fragments, setFragments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

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

  return (
    <div>
      <Typography variant="h4" gutterBottom>Фрагменты видео (ID: {id})</Typography>
      {loading && <CircularProgress />}
      {error && <Typography color="error">{error}</Typography>}
      {fragments.length === 0 && !loading && <Typography>Нет фрагментов</Typography>}
      <Grid container spacing={2}>
        {fragments.map(f => (
          <Grid item xs={12} md={6} key={f.id}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="subtitle1"><b>Старт:</b> {f.timecode_start}, <b>Конец:</b> {f.timecode_end}</Typography>
                <Typography variant="body1" sx={{mt:1}}>{f.text}</Typography>
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
        ))}
      </Grid>
    </div>
  );
}

export default VideoFragmentsPage;
