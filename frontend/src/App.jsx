import React from "react";
import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import { createTheme, ThemeProvider, CssBaseline } from "@mui/material";
import { AnimatePresence, motion } from "framer-motion";
import Navigation from "./components/Navigation";
import HomePage from "./pages/HomePage";
import UploadPage from "./pages/UploadPage";
import VideosPage from "./pages/VideosPage";
import VideoDetailPage from "./pages/VideoDetailPage";
import { LanguageProvider } from "./LanguageContext";

// Определяем анимационные варианты для переходов
const pageVariants = {
  initial: { opacity: 0, y: 20 },
  in: { opacity: 1, y: 0 },
  out: { opacity: 0, y: -20 }
};

const pageTransition = {
  type: "tween",
  duration: 0.2
};

const AnimatedRoutes = () => {
  const location = useLocation();
  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        <Route
          path="/"
          element={
            <motion.div
              initial="initial"
              animate="in"
              exit="out"
              variants={pageVariants}
              transition={pageTransition}
            >
              <HomePage />
            </motion.div>
          }
        />
        <Route
          path="/upload"
          element={
            <motion.div
              initial="initial"
              animate="in"
              exit="out"
              variants={pageVariants}
              transition={pageTransition}
            >
              <UploadPage />
            </motion.div>
          }
        />
        <Route
          path="/videos"
          element={
            <motion.div
              initial="initial"
              animate="in"
              exit="out"
              variants={pageVariants}
              transition={pageTransition}
            >
              <VideosPage />
            </motion.div>
          }
        />
        <Route
          path="/videos/:id"
          element={
            <motion.div
              initial="initial"
              animate="in"
              exit="out"
              variants={pageVariants}
              transition={pageTransition}
            >
              <VideoDetailPage />
            </motion.div>
          }
        />
      </Routes>
    </AnimatePresence>
  );
};

const theme = createTheme({
  palette: {
    primary: { main: "#0D47A1" },
    secondary: { main: "#FF6F00" },
    background: { default: "#E3F2FD" }
  },
  typography: {
    fontFamily: '"Roboto", sans-serif',
    h4: { fontWeight: 600, color: "#0D47A1" },
    h6: { fontWeight: 500 }
  },
  components: {
    MuiAppBar: {
      styleOverrides: {
        root: {
          background: "linear-gradient(45deg, #0D47A1, #1976D2)"
        }
      }
    },
    MuiButton: {
      styleOverrides: {
        root: { textTransform: "none", borderRadius: 8 }
      }
    }
  }
});

const App = () => (
  <LanguageProvider>
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <BrowserRouter>
        <Navigation />
        <AnimatedRoutes />
      </BrowserRouter>
    </ThemeProvider>
  </LanguageProvider>
);

export default App;
