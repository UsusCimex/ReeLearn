import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ChakraProvider, Box } from '@chakra-ui/react';
import Header from './components/Header';
import SearchPage from './pages/SearchPage';
import ResultsPage from './pages/ResultsPage';
import AdminButton from './components/AdminButton';
import OldInterface from './pages/OldInterface';

function App() {
  return (
    <ChakraProvider>
      <Router>
        <Box minH="100vh" bg="gray.50">
          <Routes>
            <Route
              path="/admin"
              element={<OldInterface />}
            />
            <Route
              path="/*"
              element={
                <>
                  <Header />
                  <Box maxW="container.xl" mx="auto" p={4}>
                    <Routes>
                      <Route path="/" element={<SearchPage />} />
                      <Route path="/results" element={<ResultsPage />} />
                    </Routes>
                  </Box>
                  <AdminButton />
                </>
              }
            />
          </Routes>
        </Box>
      </Router>
    </ChakraProvider>
  );
}

export default App;
