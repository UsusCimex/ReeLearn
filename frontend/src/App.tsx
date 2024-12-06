import React from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import SearchComponent from './components/SearchComponent';
import UploadComponent from './components/UploadComponent';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <header className="App-header">
          <h1>Поиск по видео</h1>
        </header>
        <main className="App-main">
          <div className="main-container">
            <div className="upload-section">
              <UploadComponent />
            </div>
            <div className="search-section">
              <SearchComponent />
            </div>
          </div>
        </main>
      </div>
    </Router>
  );
}

export default App;
