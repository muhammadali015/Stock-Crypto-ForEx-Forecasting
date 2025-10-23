import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Zap, Info } from 'lucide-react';

const ForecastControls = ({ onGenerateForecast, isGenerating, trainedModelId }) => {
  const [horizon, setHorizon] = useState(24);
  const [confidenceLevel, setConfidenceLevel] = useState(0.95);

  const horizonOptions = [
    { value: 1, label: '1 hour' },
    { value: 3, label: '3 hours' },
    { value: 24, label: '24 hours' },
    { value: 72, label: '72 hours' },
    { value: 168, label: '1 week' }
  ];

  const confidenceOptions = [
    { value: 0.90, label: '90%' },
    { value: 0.95, label: '95%' },
    { value: 0.99, label: '99%' }
  ];

  return (
    <div className="glass-card p-6">
      <h3 className="section-title">
        <Zap />
        Generate Forecast
      </h3>
      <div className="space-y-4">
        <div>
          <label className="block text-white text-sm font-medium mb-2">
            Forecast Horizon
          </label>
          <select 
            className="modern-input w-full" 
            value={horizon} 
            onChange={(e) => setHorizon(parseInt(e.target.value))}
          >
            {horizonOptions.map(option => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-white text-sm font-medium mb-2">
            Confidence Level
          </label>
          <select 
            className="modern-input w-full" 
            value={confidenceLevel} 
            onChange={(e) => setConfidenceLevel(parseFloat(e.target.value))}
          >
            {confidenceOptions.map(option => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
        <button 
          className="modern-btn w-full"
          onClick={() => onGenerateForecast(horizon, confidenceLevel)}
          disabled={isGenerating || !trainedModelId}
        >
          {isGenerating ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
              Generating...
            </>
          ) : (
            <>
              <Zap className="w-4 h-4 mr-2" />
              Generate Forecast
            </>
          )}
        </button>
        {!trainedModelId && (
          <div className="flex items-center text-yellow-400 text-sm">
            <Info className="w-4 h-4 mr-2" />
            Please train a model first
          </div>
        )}
      </div>
    </div>
  );
};

export default ForecastControls;
