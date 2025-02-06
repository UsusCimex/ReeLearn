import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { createTheme, ThemeProvider, CssBaseline } from "@mui/material";
import Navigation from "./components/Navigation";
import HomePage from "./pages/HomePage";
import UploadPage from "./pages/UploadPage";
import VideosPage from "./pages/VideosPage";
import VideoDetailPage from "./pages/VideoDetailPage";
import { LanguageProvider } from "./LanguageContext";

const theme = createTheme({
  palette: {
    primary: { main: "#0D47A1" },
    secondary: { main: "#FF6F00" },
    background: { default: "#E3F2FD" },
  },
  typography: {
    fontFamily: '"Roboto", sans-serif',
    h4: { fontWeight: 600, color: "#0D47A1" },
    h6: { fontWeight: 500 },
  },
  components: {
    MuiAppBar: {
      styleOverrides: {
        root: { background: "linear-gradient(45deg, #0D47A1, #1976D2)" },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: { textTransform: "none", borderRadius: 8 },
      },
    },
  },
});

const App = () => (
  <LanguageProvider>
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <BrowserRouter>
        <Navigation />
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/videos" element={<VideosPage />} />
          <Route path="/videos/:id" element={<VideoDetailPage />} />
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  </LanguageProvider>
);

export default App;
