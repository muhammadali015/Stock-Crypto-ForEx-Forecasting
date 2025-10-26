import React from 'react';
import { CheckCircle } from 'lucide-react';

const SuccessMessage = ({ message }) => (
  <div className="success-message">
    <div className="flex items-center">
      <CheckCircle className="w-5 h-5 mr-2" />
      {message}
    </div>
  </div>
);

export default SuccessMessage;
