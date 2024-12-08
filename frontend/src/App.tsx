import React from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import AppContent from './AppContent';
import './styles/variables.css';
import './styles/App.css';

const App: React.FC = () => {
  return (
    <div className="App">
      <Router>
        <AppContent />
      </Router>
    </div>
  );
};

export default App;
