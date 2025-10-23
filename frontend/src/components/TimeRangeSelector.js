import React from 'react';
import { Calendar, Clock } from 'lucide-react';

const TimeRangeSelector = ({ timeRange, onTimeRangeChange }) => {
  const timeRanges = [
    { value: '1h', label: '1 Hour', icon: Clock },
    { value: '3h', label: '3 Hours', icon: Clock },
    { value: '6h', label: '6 Hours', icon: Clock },
    { value: '12h', label: '12 Hours', icon: Clock },
    { value: '1d', label: '1 Day', icon: Calendar },
    { value: '3d', label: '3 Days', icon: Calendar },
    { value: '1w', label: '1 Week', icon: Calendar },
    { value: '1m', label: '1 Month', icon: Calendar },
  ];

  return (
    <div className="glass-card p-4">
      <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
        <Clock className="w-5 h-5" />
        Time Range
      </h3>
      
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
        {timeRanges.map((range) => {
          const IconComponent = range.icon;
          return (
            <button
              key={range.value}
              onClick={() => onTimeRangeChange(range.value)}
              className={`p-3 rounded-lg border transition-all duration-200 flex items-center justify-center gap-2 ${
                timeRange === range.value
                  ? 'bg-blue-600 border-blue-500 text-white shadow-lg'
                  : 'bg-white/10 border-white/20 text-white hover:bg-white/20 hover:border-white/30'
              }`}
            >
              <IconComponent className="w-4 h-4" />
              <span className="text-sm font-medium">{range.label}</span>
            </button>
          );
        })}
      </div>
      
      <div className="mt-4 p-3 bg-white/5 rounded-lg">
        <p className="text-sm text-gray-300">
          <strong>Selected:</strong> {timeRanges.find(r => r.value === timeRange)?.label || 'Custom'}
        </p>
        <p className="text-xs text-gray-400 mt-1">
          Choose a time range to filter historical data and forecast horizon
        </p>
      </div>
    </div>
  );
};

export default TimeRangeSelector;
