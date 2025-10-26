import React from 'react';
import { AlertTriangle } from 'lucide-react';

const ErrorMessage = ({ message }) => (
  <div className="error-message">
    <div className="flex items-center">
      <AlertTriangle className="w-5 h-5 mr-2" />
      {message}
    </div>
  </div>
);

export default ErrorMessage;
