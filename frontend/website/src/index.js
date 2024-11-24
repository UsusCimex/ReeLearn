import React from 'react';
import ReactDOM from 'react-dom';
import App from './App';
import './App.css'; // Подключаем стили (если есть)

ReactDOM.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
  document.getElementById('root') // Важно, чтобы в вашем HTML был <div id="root"></div>
);
