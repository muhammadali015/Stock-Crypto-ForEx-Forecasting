import React from 'react';
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
        return value < 2 ? 'text-[#00ff9f]' : value < 5 ? 'text-[#00fff2]' : 'text-[#ff4444]';
      case 'MAE':
        return value < 1.5 ? 'text-[#00ff9f]' : value < 3 ? 'text-[#00fff2]' : 'text-[#ff4444]';
      case 'MAPE':
        return value < 2 ? 'text-[#00ff9f]' : value < 5 ? 'text-[#00fff2]' : 'text-[#ff4444]';
      case 'Directional Accuracy':
        return value > 65 ? 'text-[#00ff9f]' : value > 55 ? 'text-[#00fff2]' : 'text-[#ff4444]';
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

    // RMSE scoring (lower is better)
    if (metrics.rmse < 2) score += 25;
    else if (metrics.rmse < 5) score += 15;
    else score += 5;

    // MAE scoring (lower is better)
    if (metrics.mae < 1.5) score += 25;
    else if (metrics.mae < 3) score += 15;
    else score += 5;

    // MAPE scoring (lower is better)
    if (metrics.mape < 2) score += 25;
    else if (metrics.mape < 5) score += 15;
    else score += 5;

    // Directional Accuracy scoring (higher is better)
    if (metrics.directional_accuracy > 65) score += 25;
    else if (metrics.directional_accuracy > 55) score += 15;
    else score += 5;

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
        <div className="mb-6 p-4 bg-gradient-to-r from-[#00fff2]/15 to-[#b980ff]/15 rounded-lg border border-[#00fff2]/30 relative z-10" style={{backgroundColor: 'rgba(11, 13, 16, 0.85)', backdropFilter: 'none'}}>
          <div className="flex items-center justify-between">
            <div>
              <h4 className="text-lg font-semibold text-white" style={{color: '#ffffff', textShadow: '0 0 10px rgba(255, 255, 255, 0.3)'}}>Overall Performance</h4>
              <p className="text-sm text-white" style={{color: '#ffffff', opacity: 0.9}}>Based on all metrics</p>
            </div>
            <div className="text-right">
              <div className={`text-3xl font-bold ${overallScore >= 80 ? 'text-[#00ff9f]' : overallScore >= 60 ? 'text-[#00fff2]' : 'text-[#ff4444]'}`} style={{textShadow: overallScore >= 80 ? '0 0 15px rgba(0, 255, 159, 0.5)' : overallScore >= 60 ? '0 0 15px rgba(0, 255, 242, 0.5)' : '0 0 15px rgba(255, 68, 68, 0.5)'}}>
                {overallScore}/100
              </div>
              <div className="text-sm text-white" style={{color: '#ffffff', opacity: 0.9}}>
                {overallScore >= 80 ? 'Excellent' : overallScore >= 60 ? 'Good' : 'Needs Improvement'}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Individual Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {metricCards.map((metric, index) => (
          <div
            key={metric.label}
            className="metric-card group"
          >
            <div className="flex items-center justify-between mb-3">
              <div className={`p-2 rounded-lg bg-white/10 ${metric.color}`}>
                {metric.icon}
              </div>
              <div className={`text-xs px-2 py-1 rounded-full ${
                metric.performance === 'Excellent' ? 'bg-[#00ff9f]/20 text-[#00ff9f] border border-[#00ff9f]/30' :
                metric.performance === 'Good' ? 'bg-[#00fff2]/20 text-[#00fff2] border border-[#00fff2]/30' :
                'bg-[#ff4444]/20 text-[#ff4444] border border-[#ff4444]/30'
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
                  <div
                    className={`h-2 rounded-full ${
                      parseFloat(metric.value) > 65 ? 'bg-[#00ff9f] shadow-[0_0_8px_rgba(0,255,159,0.5)]' :
                      parseFloat(metric.value) > 55 ? 'bg-[#00fff2] shadow-[0_0_8px_rgba(0,255,242,0.5)]' : 'bg-[#ff4444] shadow-[0_0_8px_rgba(255,68,68,0.5)]'
                    }`}
                    style={{ width: `${parseFloat(metric.value)}%` }}
                  />
                </div>
                <div className="text-xs text-white/60 mt-1">
                  Target: 65%+
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Performance Insights */}
      {overallScore !== null && (
        <div className="mt-6 p-4 bg-white/5 rounded-lg border border-[#00fff2]/10 relative z-10" style={{backgroundColor: 'rgba(11, 13, 16, 0.85)', backdropFilter: 'none'}}>
          <h4 className="text-sm font-semibold text-white mb-2" style={{color: '#ffffff', textShadow: '0 0 10px rgba(255, 255, 255, 0.3)'}}>Performance Insights</h4>
          <div className="text-xs text-white space-y-1" style={{color: '#ffffff', opacity: 0.95}}>
            {metrics.directional_accuracy > 65 && (
              <div className="flex items-center gap-2">
                <TrendingUp className="w-3 h-3 text-[#00ff9f]" style={{filter: 'drop-shadow(0 0 5px rgba(0, 255, 159, 0.6))'}} />
                <span style={{color: '#ffffff', opacity: 0.95}}>Strong directional accuracy - model predicts price direction well</span>
              </div>
            )}
            {metrics.rmse < 2 && (
              <div className="flex items-center gap-2">
                <Target className="w-3 h-3 text-[#00ff9f]" style={{filter: 'drop-shadow(0 0 5px rgba(0, 255, 159, 0.6))'}} />
                <span style={{color: '#ffffff', opacity: 0.95}}>Low prediction error - forecasts are highly accurate</span>
              </div>
            )}
            {metrics.mape < 2 && (
              <div className="flex items-center gap-2">
                <BarChart3 className="w-3 h-3 text-[#00ff9f]" style={{filter: 'drop-shadow(0 0 5px rgba(0, 255, 159, 0.6))'}} />
                <span style={{color: '#ffffff', opacity: 0.95}}>Excellent percentage accuracy - minimal relative error</span>
              </div>
            )}
            {overallScore < 60 && (
              <div className="flex items-center gap-2">
                <TrendingDown className="w-3 h-3 text-[#00fff2]" style={{filter: 'drop-shadow(0 0 5px rgba(0, 255, 242, 0.6))'}} />
                <span style={{color: '#ffffff', opacity: 0.95}}>Consider retraining with more data or different parameters</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default PerformanceMetrics;
