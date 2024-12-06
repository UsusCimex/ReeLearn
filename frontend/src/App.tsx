import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import UploadComponent from './components/UploadComponent';
import UploadStatusComponent from './components/UploadStatusComponent';
import SearchComponent from './components/SearchComponent';
import SearchResultsComponent from './components/SearchResultsComponent';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <header className="App-header">
          <h1>Поиск по видео</h1>
          <nav>
            <ul>
              <li><Link to="/">Загрузить видео</Link></li>
              <li><Link to="/search">Поиск видео</Link></li>
            </ul>
          </nav>
        </header>
        <main>
          <Routes>
            <Route path="/" element={<UploadComponent />} />
            <Route path="/upload-status/:taskId" element={<UploadStatusComponent />} />
            <Route path="/search" element={<SearchComponent />} />
            <Route path="/search-results/:taskId" element={<SearchResultsComponent />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
