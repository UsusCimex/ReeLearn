// SearchPage.jsx
import React, { useState, useEffect, useRef } from 'react';
import { searchVideos } from '../api';
import { Box, TextField, Button, FormControlLabel, Checkbox, Typography, Paper, List, ListItemButton, ListItemIcon, ListItemText, Card, CardContent, Grid, Divider, Dialog, DialogTitle, DialogContent, IconButton } from '@mui/material';
import HistoryIcon from '@mui/icons-material/History';
import SearchIcon from '@mui/icons-material/Search';
import FullscreenIcon from '@mui/icons-material/Fullscreen';
import CloseIcon from '@mui/icons-material/Close';

function SearchPage() {
  const [query, setQuery] = useState('');
  const [exact, setExact] = useState(false);
  const [tags, setTags] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [history, setHistory] = useState([]);
  
  // Для модального окна большого видео
  const [openVideoModal, setOpenVideoModal] = useState(false);
  const [videoModalUrl, setVideoModalUrl] = useState('');
  const videoContainerRef = useRef(null);
  const videoRef = useRef(null);

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

  const highlightTextHtml = (text, term, exact) => {
    if (!term.trim()) return text;
    const regex = exact ? new RegExp(`\\b(${term})\\b`, 'gi') : new RegExp(`(${term})`, 'gi');
    return text.replace(regex, '<span style="background:yellow;">$1</span>');
  };  
  
  const highlightTextVtt = (text, term, exact) => {
    if (!term.trim()) return text;
    const regex = exact ? new RegExp(`\\b${term}\\b`, 'gi') : new RegExp(`(${term})`, 'gi');
    return text.replace(regex, (match) => `<c.highlight>${match}</c>`);
  };

  // Создание WebVTT для субтитров фрагмента
  const createVttBlobUrl = (fragmentText) => {
    const highlighted = highlightTextVtt(fragmentText, query, exact);
    const vtt = `WEBVTT
  
  00:00.000 --> 00:59.000
  ${highlighted}
  `;
    const blob = new Blob([vtt], { type: 'text/vtt' });
    return URL.createObjectURL(blob);
  };

  const handleVideoNameClick = (url) => {
    setVideoModalUrl(url);
    setOpenVideoModal(true);
  };

  const handleFullscreen = () => {
    if (videoContainerRef.current) {
      if (videoContainerRef.current.requestFullscreen) {
        videoContainerRef.current.requestFullscreen();
      } else if (videoContainerRef.current.webkitRequestFullscreen) {
        videoContainerRef.current.webkitRequestFullscreen();
      }
    }
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
                        <Typography variant="h6" sx={{cursor:'pointer', textDecoration:'underline'}}
                          onClick={() => handleVideoNameClick(r.video.s3_url)}>
                          {r.video.name}
                        </Typography>
                        {r.fragments.map(f => {
                          const highlighted = highlightTextHtml(f.text, query, exact);
                          const trackUrl = createVttBlobUrl(f.text);
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
                                >
                                  <track src={trackUrl} kind="subtitles" srcLang="ru" default />
                                </video>
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

      {/* Модальное окно для большого видео */}
      <Dialog open={openVideoModal} onClose={() => setOpenVideoModal(false)} fullWidth maxWidth="md">
        <DialogTitle>
          <Box sx={{display:'flex', alignItems:'center', justifyContent:'space-between'}}>
            <Typography variant="h6">Просмотр видео</Typography>
            <Box>
              <IconButton onClick={handleFullscreen} title="Полноэкранный режим">
                <FullscreenIcon />
              </IconButton>
              <IconButton onClick={() => setOpenVideoModal(false)}>
                <CloseIcon />
              </IconButton>
            </Box>
          </Box>
        </DialogTitle>
        <DialogContent>
          <Box ref={videoContainerRef} sx={{ position:'relative', textAlign:'center' }}>
            <video
              ref={videoRef}
              src={videoModalUrl}
              controls
              style={{ width:'100%', borderRadius:'4px', background:'#000' }}
            />
          </Box>
        </DialogContent>
      </Dialog>
    </Box>
  );
}

export default SearchPage;
