import React from 'react';
import { motion } from 'framer-motion';
import { BarChart3, TrendingUp, TrendingDown, Target, Zap } from 'lucide-react';

const PerformanceMetrics = ({ metrics }) => {
  if (!metrics || Object.keys(metrics).length === 0) {
    return null;
  }

  const getMetricIcon = (label) => {
    switch (label) {
      case 'RMSE':
        return <Target className="w-5 h-5" />;
      case 'MAE':
        return <BarChart3 className="w-5 h-5" />;
      case 'MAPE':
        return <TrendingUp className="w-5 h-5" />;
      case 'Directional Accuracy':
        return <Zap className="w-5 h-5" />;
      default:
        return <BarChart3 className="w-5 h-5" />;
    }
  };

  const getMetricColor = (label, value) => {
    switch (label) {
      case 'RMSE':
        return value < 2 ? 'text-green-400' : value < 5 ? 'text-yellow-400' : 'text-red-400';
      case 'MAE':
        return value < 1.5 ? 'text-green-400' : value < 3 ? 'text-yellow-400' : 'text-red-400';
      case 'MAPE':
        return value < 2 ? 'text-green-400' : value < 5 ? 'text-yellow-400' : 'text-red-400';
      case 'Directional Accuracy':
        return value > 65 ? 'text-green-400' : value > 55 ? 'text-yellow-400' : 'text-red-400';
      default:
        return 'text-white';
    }
  };

  const getPerformanceLevel = (label, value) => {
    switch (label) {
      case 'RMSE':
        if (value < 2) return 'Excellent';
        if (value < 5) return 'Good';
        return 'Needs Improvement';
      case 'MAE':
        if (value < 1.5) return 'Excellent';
        if (value < 3) return 'Good';
        return 'Needs Improvement';
      case 'MAPE':
        if (value < 2) return 'Excellent';
        if (value < 5) return 'Good';
        return 'Needs Improvement';
      case 'Directional Accuracy':
        if (value > 65) return 'Excellent';
        if (value > 55) return 'Good';
        return 'Needs Improvement';
      default:
        return 'N/A';
    }
  };

  const metricCards = [
    {
      label: 'RMSE',
      value: metrics.rmse?.toFixed(4) || 'N/A',
      description: 'Root Mean Square Error',
      suffix: '',
      icon: getMetricIcon('RMSE'),
      color: getMetricColor('RMSE', metrics.rmse),
      performance: getPerformanceLevel('RMSE', metrics.rmse)
    },
    {
      label: 'MAE',
      value: metrics.mae?.toFixed(4) || 'N/A',
      description: 'Mean Absolute Error',
      suffix: '',
      icon: getMetricIcon('MAE'),
      color: getMetricColor('MAE', metrics.mae),
      performance: getPerformanceLevel('MAE', metrics.mae)
    },
    {
      label: 'MAPE',
      value: metrics.mape?.toFixed(2) || 'N/A',
      description: 'Mean Absolute Percentage Error',
      suffix: '%',
      icon: getMetricIcon('MAPE'),
      color: getMetricColor('MAPE', metrics.mape),
      performance: getPerformanceLevel('MAPE', metrics.mape)
    },
    {
      label: 'Directional Accuracy',
      value: metrics.directional_accuracy?.toFixed(1) || 'N/A',
      description: 'Direction Prediction Accuracy',
      suffix: '%',
      icon: getMetricIcon('Directional Accuracy'),
      color: getMetricColor('Directional Accuracy', metrics.directional_accuracy),
      performance: getPerformanceLevel('Directional Accuracy', metrics.directional_accuracy)
    }
  ];

  // Calculate overall performance score
  const calculateOverallScore = () => {
    if (!metrics.rmse || !metrics.mae || !metrics.mape || !metrics.directional_accuracy) {
      return null;
    }

    let score = 0;
    let count = 0;

    // RMSE scoring (lower is better)
    if (metrics.rmse < 2) score += 25;
    else if (metrics.rmse < 5) score += 15;
    else score += 5;
    count++;

    // MAE scoring (lower is better)
    if (metrics.mae < 1.5) score += 25;
    else if (metrics.mae < 3) score += 15;
    else score += 5;
    count++;

    // MAPE scoring (lower is better)
    if (metrics.mape < 2) score += 25;
    else if (metrics.mape < 5) score += 15;
    else score += 5;
    count++;

    // Directional Accuracy scoring (higher is better)
    if (metrics.directional_accuracy > 65) score += 25;
    else if (metrics.directional_accuracy > 55) score += 15;
    else score += 5;
    count++;

    return Math.round(score);
  };

  const overallScore = calculateOverallScore();

  return (
    <div className="glass-card p-6">
      <h3 className="section-title">
        <BarChart3 />
        Model Performance
      </h3>
      
      {/* Overall Score */}
      {overallScore !== null && (
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="mb-6 p-4 bg-gradient-to-r from-blue-500/20 to-purple-500/20 rounded-lg border border-white/20"
        >
          <div className="flex items-center justify-between">
            <div>
              <h4 className="text-lg font-semibold text-white">Overall Performance</h4>
              <p className="text-sm text-white/70">Based on all metrics</p>
            </div>
            <div className="text-right">
              <div className={`text-3xl font-bold ${overallScore >= 80 ? 'text-green-400' : overallScore >= 60 ? 'text-yellow-400' : 'text-red-400'}`}>
                {overallScore}/100
              </div>
              <div className="text-sm text-white/70">
                {overallScore >= 80 ? 'Excellent' : overallScore >= 60 ? 'Good' : 'Needs Improvement'}
              </div>
            </div>
          </div>
        </motion.div>
      )}

      {/* Individual Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {metricCards.map((metric, index) => (
          <motion.div
            key={metric.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: index * 0.1 }}
            className="metric-card group"
          >
            <div className="flex items-center justify-between mb-3">
              <div className={`p-2 rounded-lg bg-white/10 ${metric.color}`}>
                {metric.icon}
              </div>
              <div className={`text-xs px-2 py-1 rounded-full ${
                metric.performance === 'Excellent' ? 'bg-green-500/20 text-green-400' :
                metric.performance === 'Good' ? 'bg-yellow-500/20 text-yellow-400' :
                'bg-red-500/20 text-red-400'
              }`}>
                {metric.performance}
              </div>
            </div>
            
            <div className={`metric-value ${metric.color}`}>
              {metric.value}{metric.suffix}
            </div>
            
            <div className="metric-label">{metric.label}</div>
            <div className="text-xs opacity-60 mt-1">{metric.description}</div>
            
            {/* Progress bar for directional accuracy */}
            {metric.label === 'Directional Accuracy' && metric.value !== 'N/A' && (
              <div className="mt-3">
                <div className="w-full bg-white/10 rounded-full h-2">
                  <motion.div
                    className={`h-2 rounded-full ${
                      parseFloat(metric.value) > 65 ? 'bg-green-400' :
                      parseFloat(metric.value) > 55 ? 'bg-yellow-400' : 'bg-red-400'
                    }`}
                    initial={{ width: 0 }}
                    animate={{ width: `${parseFloat(metric.value)}%` }}
                    transition={{ duration: 1, delay: index * 0.1 + 0.5 }}
                  />
                </div>
                <div className="text-xs text-white/60 mt-1">
                  Target: 65%+
                </div>
              </div>
            )}
          </motion.div>
        ))}
      </div>

      {/* Performance Insights */}
      {overallScore !== null && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.6 }}
          className="mt-6 p-4 bg-white/5 rounded-lg border border-white/10"
        >
          <h4 className="text-sm font-semibold text-white mb-2">Performance Insights</h4>
          <div className="text-xs text-white/70 space-y-1">
            {metrics.directional_accuracy > 65 && (
              <div className="flex items-center gap-2">
                <TrendingUp className="w-3 h-3 text-green-400" />
                <span>Strong directional accuracy - model predicts price direction well</span>
              </div>
            )}
            {metrics.rmse < 2 && (
              <div className="flex items-center gap-2">
                <Target className="w-3 h-3 text-green-400" />
                <span>Low prediction error - forecasts are highly accurate</span>
              </div>
            )}
            {metrics.mape < 2 && (
              <div className="flex items-center gap-2">
                <BarChart3 className="w-3 h-3 text-green-400" />
                <span>Excellent percentage accuracy - minimal relative error</span>
              </div>
            )}
            {overallScore < 60 && (
              <div className="flex items-center gap-2">
                <TrendingDown className="w-3 h-3 text-yellow-400" />
                <span>Consider retraining with more data or different parameters</span>
              </div>
            )}
          </div>
        </motion.div>
      )}
    </div>
  );
};

export default PerformanceMetrics;
