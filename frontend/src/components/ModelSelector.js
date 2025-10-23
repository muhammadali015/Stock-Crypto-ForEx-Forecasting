import React from 'react';
import { Brain, Play, BarChart3, CheckCircle } from 'lucide-react';

const ModelSelector = ({ models, selectedModel, onModelChange, onTrainModel, onEvaluateModel, isTraining, trainedModelId }) => {
  return (
    <div className="glass-card p-6">
      <h3 className="section-title">
        <Brain />
        Forecasting Models
      </h3>
      <div className="space-y-4">
        <div>
          <select 
            className="modern-input w-full" 
            value={selectedModel || ''} 
            onChange={(e) => onModelChange(e.target.value)}
          >
            <option value="">Select a model...</option>
            {models.map(model => (
              <option key={model} value={model}>
                {model.toUpperCase()}
              </option>
            ))}
          </select>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <button 
            className="modern-btn"
            onClick={onTrainModel}
            disabled={!selectedModel || isTraining}
          >
            {isTraining ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                Training...
              </>
            ) : (
              <>
                <Play className="w-4 h-4 mr-2" />
                Train
              </>
            )}
          </button>
          <button 
            className="modern-btn"
            onClick={onEvaluateModel}
            disabled={!selectedModel || !trainedModelId}
          >
            <BarChart3 className="w-4 h-4 mr-2" />
            Evaluate
          </button>
        </div>
        {trainedModelId && (
          <div className="flex items-center text-green-400 text-sm">
            <CheckCircle className="w-4 h-4 mr-2" />
            Model trained successfully
          </div>
        )}
      </div>
    </div>
  );
};

export default ModelSelector;
