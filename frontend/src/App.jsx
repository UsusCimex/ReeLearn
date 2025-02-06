import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { CssBaseline, Container } from "@mui/material";
import Navigation from "./components/Navigation";
import HomePage from "./pages/HomePage";
import UploadPage from "./pages/UploadPage";
import VideosPage from "./pages/VideosPage";
import VideoDetailPage from "./pages/VideoDetailPage";

const App = () => {
  return (
    <BrowserRouter>
      <CssBaseline />
      <Navigation />
      <Container sx={{ mt: 4, mb: 4 }}>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/videos" element={<VideosPage />} />
          <Route path="/videos/:id" element={<VideoDetailPage />} />
        </Routes>
      </Container>
    </BrowserRouter>
  );
};

export default App;
