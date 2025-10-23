import React from 'react';
import { motion } from 'framer-motion';
import { CheckCircle } from 'lucide-react';

const SuccessMessage = ({ message }) => (
  <motion.div
    initial={{ opacity: 0, y: -20 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: -20 }}
    className="success-message"
  >
    <div className="flex items-center">
      <CheckCircle className="w-5 h-5 mr-2" />
      {message}
    </div>
  </motion.div>
);

export default SuccessMessage;
