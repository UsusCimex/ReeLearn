import React, { useEffect, useState } from 'react';
import { getVideos } from '../api';
import { Typography, Grid, Card, CardActionArea, CardContent, CircularProgress } from '@mui/material';
import { Link } from 'react-router-dom';

function VideoListPage() {
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchVideos = async () => {
      setLoading(true);
      try {
        const data = await getVideos();
        setVideos(data);
      } catch (e) {
        setError('Ошибка при загрузке списка видео');
      } finally {
        setLoading(false);
      }
    };
    fetchVideos();
  }, []);

  return (
    <div>
      <Typography variant="h4" gutterBottom>Список видео</Typography>
      {loading && <CircularProgress />}
      {error && <Typography color="error">{error}</Typography>}
      {videos.length === 0 && !loading && <Typography>Нет видео</Typography>}
      <Grid container spacing={2}>
        {videos.map(v => (
          <Grid item xs={12} sm={6} md={4} key={v.id}>
            <Card variant="outlined">
              <CardActionArea component={Link} to={`/videos/${v.id}`}>
                <CardContent>
                  <Typography variant="h6">{v.name}</Typography>
                  <Typography variant="body2" color="text.secondary">{v.status}, фрагментов: {v.fragments_count}</Typography>
                </CardContent>
              </CardActionArea>
            </Card>
          </Grid>
        ))}
      </Grid>
    </div>
  );
}

export default VideoListPage;
