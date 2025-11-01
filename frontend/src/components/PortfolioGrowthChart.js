import React, { useEffect, useRef, useState } from 'react';
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { TrendingUp, DollarSign } from 'lucide-react';

const PortfolioGrowthChart = ({ portfolioMetricsHistory, initialCapital }) => {
  const [chartData, setChartData] = useState([]);

  useEffect(() => {
    if (!portfolioMetricsHistory || portfolioMetricsHistory.length === 0) {
      setChartData([]);
      return;
    }

    // Transform data for Recharts
    const data = portfolioMetricsHistory
      .slice()
      .reverse() // Reverse to get chronological order
      .map((metric, index) => ({
        date: new Date(metric.metric_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        timestamp: new Date(metric.metric_date).getTime(),
        value: metric.total_value || 0,
        return: metric.total_return || 0,
        index: index
      }));

    // If we have initial capital but no history, add a starting point
    if (initialCapital && data.length > 0 && data[0].value === 0) {
      data.unshift({
        date: new Date(Date.now() - 86400000 * data.length).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        timestamp: Date.now() - 86400000 * data.length,
        value: initialCapital,
        return: 0,
        index: -1
      });
    }

    setChartData(data);
  }, [portfolioMetricsHistory, initialCapital]);

  if (!chartData || chartData.length === 0) {
    return (
      <div className="glass-card p-6">
        <h3 className="section-title mb-4">
          <DollarSign />
          Portfolio Growth
        </h3>
        <div className="flex items-center justify-center h-64 text-white/60">
          <div className="text-center">
            <DollarSign className="w-16 h-16 mx-auto mb-4 opacity-50 text-[#00fff2]" />
            <p>No portfolio data available</p>
            <p className="text-sm mt-2">Start trading to see portfolio growth</p>
          </div>
        </div>
      </div>
    );
  }

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-[#0b0d10] border border-[#00fff2]/30 rounded-lg p-3 backdrop-filter blur-sm" style={{backgroundColor: 'rgba(11, 13, 16, 0.95)'}}>
          <p className="text-white font-semibold mb-1">{data.date}</p>
          <p className="text-[#00fff2]">
            <span className="text-white/70">Value: </span>${data.value.toFixed(2)}
          </p>
          <p className={data.return >= 0 ? 'text-[#00ff9f]' : 'text-[#ff4444]'}>
            <span className="text-white/70">Return: </span>{data.return.toFixed(2)}%
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="glass-card p-6">
      <h3 className="section-title mb-4">
        <TrendingUp />
        Portfolio Growth
      </h3>
      
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="portfolioGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#00fff2" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#00fff2" stopOpacity={0.05} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(0, 255, 242, 0.15)" />
          <XAxis 
            dataKey="date" 
            stroke="#00fff2"
            style={{ fontSize: '12px' }}
          />
          <YAxis 
            stroke="#00fff2"
            style={{ fontSize: '12px' }}
            tickFormatter={(value) => `$${value.toFixed(0)}`}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend 
            wrapperStyle={{ color: '#ffffff' }}
            iconType="line"
          />
          <Area
            type="monotone"
            dataKey="value"
            stroke="#00fff2"
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#portfolioGradient)"
            name="Portfolio Value"
            dot={{ fill: '#00fff2', r: 3 }}
            activeDot={{ r: 6, fill: '#00ff9f' }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

export default PortfolioGrowthChart;

