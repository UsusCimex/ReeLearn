import React, { useEffect } from 'react';
import { logError } from '../utils/logger';

const ErrorToast = ({ message, duration = 3000, onClose }) => {
  useEffect(() => {
    logError(`Error Toast displayed: ${message}`);
    const timer = setTimeout(() => {
      onClose();
    }, duration);

    return () => clearTimeout(timer);
  }, [duration, onClose, message]);

  return (
    <div className="error-toast">
      {message}
    </div>
  );
};

export default ErrorToast;
