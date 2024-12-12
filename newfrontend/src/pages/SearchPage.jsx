import React, { useState, useEffect } from 'react';
import { searchVideos } from '../api';
import { Box, TextField, Button, FormControlLabel, Checkbox, Typography, Paper, List, ListItemButton, ListItemIcon, ListItemText, Card, CardContent, Grid, Divider } from '@mui/material';
import HistoryIcon from '@mui/icons-material/History';
import SearchIcon from '@mui/icons-material/Search';

function SearchPage() {
  const [query, setQuery] = useState('');
  const [exact, setExact] = useState(false);
  const [tags, setTags] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [history, setHistory] = useState([]);

  useEffect(() => {
    const savedHistory = JSON.parse(localStorage.getItem('searchHistory') || '[]');
    setHistory(savedHistory);
  }, []);

  const saveHistory = (newQuery) => {
    const savedHistory = JSON.parse(localStorage.getItem('searchHistory') || '[]');
    const filtered = savedHistory.filter(h => h !== newQuery);
    const updated = [newQuery, ...filtered.slice(0,9)];
    localStorage.setItem('searchHistory', JSON.stringify(updated));
    setHistory(updated);
  };

  const performSearch = async (searchQuery) => {
    setLoading(true);
    setError(null);
    try {
      const tagsArr = tags ? tags.split(',').map(t => t.trim()) : [];
      const data = await searchVideos({ query: searchQuery, exact, tags: tagsArr });
      setResults(data);
      saveHistory(searchQuery);
    } catch (e) {
      setError(e.message || 'Ошибка поиска');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    performSearch(query);
  };

  const handleHistoryClick = (item) => {
    setQuery(item);
    performSearch(item);
  };

  const handleKeyDown = (e) => {
    if(e.key === 'Enter') {
      handleSearch();
    }
  };

  const highlightText = (text, term) => {
    if (!term.trim()) return text;
    const regex = new RegExp(`(${term})`, 'gi');
    return text.replace(regex, '<mark>$1</mark>');
  };

  return (
    <Box>
      <Paper sx={{ p:4, mb:4, background:'linear-gradient(to right, #2196f3, #64b5f6)', color:'#fff' }}>
        <Typography variant="h3" gutterBottom>Поиск по видео</Typography>
        <Typography variant="subtitle1">Найдите нужный фрагмент по текстовому описанию</Typography>
        <Box sx={{ display:'flex', alignItems:'center', mt:3, gap:2, flexWrap:'wrap' }}>
          <TextField
            placeholder="Запрос..."
            variant="outlined"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            size="small"
            onKeyDown={handleKeyDown}
            sx={{ background:'#fff', borderRadius:1, minWidth:'200px' }}
          />
          <TextField
            placeholder="Теги (через запятую)"
            variant="outlined"
            value={tags}
            onChange={(e) => setTags(e.target.value)}
            size="small"
            onKeyDown={handleKeyDown}
            sx={{ background:'#fff', borderRadius:1, minWidth:'200px' }}
          />
          <FormControlLabel
            control={<Checkbox checked={exact} onChange={() => setExact(!exact)} sx={{color:'#fff'}} />}
            label={<Typography sx={{color:'#fff'}}>Точный поиск</Typography>}
          />
          <Button startIcon={<SearchIcon />} variant="contained" onClick={handleSearch}>Поиск</Button>
        </Box>
      </Paper>

      {loading && <Typography>Загрузка...</Typography>}
      {error && <Typography color="error">{error}</Typography>}

      <Grid container spacing={2}>
        <Grid item xs={12} md={3}>
          <Paper variant="outlined" sx={{ p:2 }}>
            <Typography variant="h6" gutterBottom>История запросов</Typography>
            <Divider sx={{ mb:1 }}/>
            {history.length === 0 && <Typography color="text.secondary">Нет истории</Typography>}
            <List>
              {history.map((h, idx) => (
                <ListItemButton key={idx} onClick={() => handleHistoryClick(h)}>
                  <ListItemIcon><HistoryIcon color="primary"/></ListItemIcon>
                  <ListItemText primary={h}/>
                </ListItemButton>
              ))}
            </List>
          </Paper>
        </Grid>
        <Grid item xs={12} md={9}>
          {results && results.status === 'completed' && (
            <Box>
              <Typography variant="h5" gutterBottom>Результаты:</Typography>
              {results.results.length === 0 && <Typography>Ничего не найдено</Typography>}
              <Grid container spacing={2}>
                {results.results.map((r) => (
                  <Grid item xs={12} sm={6} key={r.video.video_id}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="h6">
                          <a href={r.video.s3_url} target="_blank" rel="noopener noreferrer"
                             style={{textDecoration:'none', color:'inherit', cursor:'pointer'}}>
                            {r.video.name}
                          </a>
                        </Typography>
                        {r.fragments.map(f => {
                          const highlighted = highlightText(f.text, query);
                          return (
                            <Box key={f.fragment_id} sx={{ mt:2 }}>
                              <Typography variant="subtitle1" component="div"><b>Фрагмент:</b></Typography>
                              <Typography variant="body1" component="div"
                                dangerouslySetInnerHTML={{__html: highlighted}} />
                              <Typography variant="body2" color="text.secondary"><b>Время:</b> {f.timecode_start} - {f.timecode_end}</Typography>
                              <Box sx={{ mt:1 }}>
                                <video
                                  src={f.s3_url}
                                  controls
                                  style={{ width: '100%', maxWidth:'400px', borderRadius:'4px', border:'1px solid #ccc' }}
                                />
                              </Box>
                              <Typography variant="body2" sx={{mt:1}}><b>Оценка:</b> {f.score.toFixed(2)}</Typography>
                            </Box>
                          );
                        })}
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </Box>
          )}
        </Grid>
      </Grid>
    </Box>
  );
}

export default SearchPage;
