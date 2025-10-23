import React from 'react';
import { motion } from 'framer-motion';
import { AlertTriangle } from 'lucide-react';

const ErrorMessage = ({ message }) => (
  <motion.div
    initial={{ opacity: 0, y: -20 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: -20 }}
    className="error-message"
  >
    <div className="flex items-center">
      <AlertTriangle className="w-5 h-5 mr-2" />
      {message}
    </div>
  </motion.div>
);

export default ErrorMessage;
