import React from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import AppContent from './AppContent';
import './styles/variables.css';
import './styles/App.css';

function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}

export default App;
