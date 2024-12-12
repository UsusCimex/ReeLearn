// App.js
import React, { useState } from 'react';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, AppBar, Toolbar, Typography, Box, IconButton, Drawer, List, ListItemButton, ListItemIcon, ListItemText, Divider, useMediaQuery } from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import VideoLibraryIcon from '@mui/icons-material/VideoLibrary';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import MenuIcon from '@mui/icons-material/Menu';
import AppRoutes from './routes';
import { UploadProvider } from './UploadContext';
import UploadModal from './components/UploadModal';

const theme = createTheme({
  palette: {
    primary: { main: '#1976d2' },
    background: { default: '#f5f5f5' }
  },
});

const drawerWidth = 240;

function App() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);

  // Определим, когда мы на широком экране (например md breakpoint)
  const isDesktop = useMediaQuery(theme.breakpoints.up('sm'));

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const navItems = [
    { text: 'Поиск', icon: <SearchIcon />, link: '/' },
    { text: 'Видео', icon: <VideoLibraryIcon />, link: '/videos' },
    { text: 'Загрузить', icon: <CloudUploadIcon />, action: () => setShowUploadModal(true) },
  ];

  const drawer = (
    <div>
      <Typography variant="h5" sx={{ m:2 }}>ReeLearn</Typography>
      <Divider />
      <List>
        {navItems.map((item) => (
          <ListItemButton 
            key={item.text} 
            onClick={item.link ? () => { window.location.href=item.link; } : item.action}>
            <ListItemIcon>{item.icon}</ListItemIcon>
            <ListItemText primary={item.text}/>
          </ListItemButton>
        ))}
      </List>
    </div>
  );

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <UploadProvider>
        <BrowserRouter>
          <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
            <Toolbar>
              {!isDesktop && (
                <IconButton 
                  color="inherit" 
                  edge="start" 
                  onClick={handleDrawerToggle} 
                  sx={{ mr: 2 }}
                >
                  <MenuIcon />
                </IconButton>
              )}
              <Typography variant="h6" noWrap component="div">
                ReeLearn
              </Typography>
            </Toolbar>
          </AppBar>

          {/* Drawer для мобильного режима */}
          <Box component="nav">
            <Drawer
              variant="temporary"
              open={mobileOpen}
              onClose={handleDrawerToggle}
              ModalProps={{ keepMounted: true }}
              sx={{
                display:{ xs:'block', sm:'none' },
                '& .MuiDrawer-paper': { boxSizing:'border-box', width:drawerWidth }
              }}
            >
              {drawer}
            </Drawer>
            
            {/* Drawer для большого экрана (постоянный) */}
            <Drawer
              variant="permanent"
              sx={{
                display: { xs:'none', sm:'block' },
                '& .MuiDrawer-paper': { boxSizing:'border-box', width:drawerWidth }
              }}
              open
            >
              {drawer}
            </Drawer>
          </Box>

          <Box 
            component="main" 
            sx={{ 
              flexGrow:1, 
              p:3, 
              mt:8, 
              // Отступ слева для широких экранов, чтобы контент не был перекрыт Drawer:
              ml: { sm: `${drawerWidth}px` } 
            }}
          >
            <AppRoutes />
          </Box>

          {showUploadModal && <UploadModal onClose={() => setShowUploadModal(false)} />}
        </BrowserRouter>
      </UploadProvider>
    </ThemeProvider>
  );
}

export default App;
