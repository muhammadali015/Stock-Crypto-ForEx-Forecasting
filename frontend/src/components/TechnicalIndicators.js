import React, { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, Activity, Zap } from 'lucide-react';
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const TechnicalIndicators = ({ priceData, forecasts }) => {
  const [indicators, setIndicators] = useState(null);
  const [selectedIndicator, setSelectedIndicator] = useState('rsi');

  // Calculate technical indicators
  useEffect(() => {
    if (!priceData || priceData.length < 20) return;

    const calculateRSI = (prices, period = 14) => {
      const gains = [];
      const losses = [];
      
      for (let i = 1; i < prices.length; i++) {
        const change = prices[i] - prices[i - 1];
        gains.push(change > 0 ? change : 0);
        losses.push(change < 0 ? Math.abs(change) : 0);
      }

      const rsiValues = [];
      for (let i = period - 1; i < gains.length; i++) {
        const avgGain = gains.slice(i - period + 1, i + 1).reduce((a, b) => a + b) / period;
        const avgLoss = losses.slice(i - period + 1, i + 1).reduce((a, b) => a + b) / period;
        
        if (avgLoss === 0) {
          rsiValues.push(100);
        } else {
          const rs = avgGain / avgLoss;
          const rsi = 100 - (100 / (1 + rs));
          rsiValues.push(rsi);
        }
      }

      return rsiValues;
    };

    const calculateMACD = (prices, fastPeriod = 12, slowPeriod = 26, signalPeriod = 9) => {
      const emaFast = calculateEMA(prices, fastPeriod);
      const emaSlow = calculateEMA(prices, slowPeriod);
      
      const macdLine = emaFast.map((fast, i) => fast - emaSlow[i]);
      const signalLine = calculateEMA(macdLine, signalPeriod);
      const histogram = macdLine.map((macd, i) => macd - signalLine[i]);

      return { macdLine, signalLine, histogram };
    };

    const calculateEMA = (prices, period) => {
      const multiplier = 2 / (period + 1);
      const ema = [prices[0]];
      
      for (let i = 1; i < prices.length; i++) {
        ema.push((prices[i] * multiplier) + (ema[i - 1] * (1 - multiplier)));
      }
      
      return ema;
    };

    const calculateBollingerBands = (prices, period = 20, stdDev = 2) => {
      const sma = [];
      const upperBand = [];
      const lowerBand = [];

      for (let i = period - 1; i < prices.length; i++) {
        const slice = prices.slice(i - period + 1, i + 1);
        const mean = slice.reduce((a, b) => a + b) / period;
        const variance = slice.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / period;
        const standardDeviation = Math.sqrt(variance);

        sma.push(mean);
        upperBand.push(mean + (standardDeviation * stdDev));
        lowerBand.push(mean - (standardDeviation * stdDev));
      }

      return { sma, upperBand, lowerBand };
    };

    const calculateStochastic = (highs, lows, closes, period = 14) => {
      const kValues = [];
      
      for (let i = period - 1; i < closes.length; i++) {
        const highSlice = highs.slice(i - period + 1, i + 1);
        const lowSlice = lows.slice(i - period + 1, i + 1);
        const close = closes[i];
        
        const highestHigh = Math.max(...highSlice);
        const lowestLow = Math.min(...lowSlice);
        
        const k = ((close - lowestLow) / (highestHigh - lowestLow)) * 100;
        kValues.push(k);
      }

      return kValues;
    };

    const closes = priceData.map(d => d.close_price);
    const highs = priceData.map(d => d.high_price);
    const lows = priceData.map(d => d.low_price);

    const rsi = calculateRSI(closes);
    const macd = calculateMACD(closes);
    const bollinger = calculateBollingerBands(closes);
    const stochastic = calculateStochastic(highs, lows, closes);

    // Prepare data for charts
    const chartData = priceData.slice(19).map((d, i) => ({
      date: new Date(d.date).toLocaleDateString(),
      timestamp: new Date(d.date).getTime(),
      price: d.close_price,
      volume: d.volume || 0,
      rsi: rsi[i] || null,
      macd: macd.macdLine[i] || null,
      signal: macd.signalLine[i] || null,
      histogram: macd.histogram[i] || null,
      bbUpper: bollinger.upperBand[i] || null,
      bbMiddle: bollinger.sma[i] || null,
      bbLower: bollinger.lowerBand[i] || null,
      stochastic: stochastic[i] || null,
    }));

    setIndicators({
      rsi,
      macd,
      bollinger,
      stochastic,
      chartData
    });
  }, [priceData]);

  const indicatorOptions = [
    { value: 'rsi', label: 'RSI', description: 'Relative Strength Index' },
    { value: 'macd', label: 'MACD', description: 'Moving Average Convergence Divergence' },
    { value: 'bollinger', label: 'Bollinger Bands', description: 'Price Volatility Indicator' },
    { value: 'stochastic', label: 'Stochastic', description: 'Momentum Oscillator' },
    { value: 'volume', label: 'Volume', description: 'Trading Volume Analysis' }
  ];

  const renderIndicatorChart = () => {
    if (!indicators || !indicators.chartData) return null;

    const data = indicators.chartData;

    switch (selectedIndicator) {
      case 'rsi':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis 
                dataKey="date" 
                stroke="rgba(255,255,255,0.6)"
                fontSize={12}
              />
              <YAxis 
                stroke="rgba(255,255,255,0.6)"
                fontSize={12}
                domain={[0, 100]}
              />
              <Tooltip 
                contentStyle={{
                  backgroundColor: 'rgba(0,0,0,0.8)',
                  border: '1px solid rgba(255,255,255,0.2)',
                  borderRadius: '8px',
                  color: 'white'
                }}
              />
              <Line 
                type="monotone" 
                dataKey="rsi" 
                stroke="#ffd700" 
                strokeWidth={2}
                dot={false}
              />
              <Line 
                type="monotone" 
                dataKey="70" 
                stroke="#ef5350" 
                strokeDasharray="5 5"
                strokeWidth={1}
              />
              <Line 
                type="monotone" 
                dataKey="30" 
                stroke="#26a69a" 
                strokeDasharray="5 5"
                strokeWidth={1}
              />
            </LineChart>
          </ResponsiveContainer>
        );

      case 'macd':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis 
                dataKey="date" 
                stroke="rgba(255,255,255,0.6)"
                fontSize={12}
              />
              <YAxis 
                stroke="rgba(255,255,255,0.6)"
                fontSize={12}
              />
              <Tooltip 
                contentStyle={{
                  backgroundColor: 'rgba(0,0,0,0.8)',
                  border: '1px solid rgba(255,255,255,0.2)',
                  borderRadius: '8px',
                  color: 'white'
                }}
              />
              <Line 
                type="monotone" 
                dataKey="macd" 
                stroke="#667eea" 
                strokeWidth={2}
                dot={false}
              />
              <Line 
                type="monotone" 
                dataKey="signal" 
                stroke="#764ba2" 
                strokeWidth={2}
                dot={false}
              />
              <Area 
                type="monotone" 
                dataKey="histogram" 
                fill="rgba(102, 126, 234, 0.3)"
                stroke="rgba(102, 126, 234, 0.8)"
                strokeWidth={1}
              />
            </LineChart>
          </ResponsiveContainer>
        );

      case 'bollinger':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis 
                dataKey="date" 
                stroke="rgba(255,255,255,0.6)"
                fontSize={12}
              />
              <YAxis 
                stroke="rgba(255,255,255,0.6)"
                fontSize={12}
              />
              <Tooltip 
                contentStyle={{
                  backgroundColor: 'rgba(0,0,0,0.8)',
                  border: '1px solid rgba(255,255,255,0.2)',
                  borderRadius: '8px',
                  color: 'white'
                }}
              />
              <Line 
                type="monotone" 
                dataKey="price" 
                stroke="#ffffff" 
                strokeWidth={2}
                dot={false}
              />
              <Line 
                type="monotone" 
                dataKey="bbUpper" 
                stroke="#ef5350" 
                strokeWidth={1}
                dot={false}
              />
              <Line 
                type="monotone" 
                dataKey="bbMiddle" 
                stroke="#ffd700" 
                strokeWidth={1}
                strokeDasharray="5 5"
                dot={false}
              />
              <Line 
                type="monotone" 
                dataKey="bbLower" 
                stroke="#26a69a" 
                strokeWidth={1}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        );

      case 'stochastic':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis 
                dataKey="date" 
                stroke="rgba(255,255,255,0.6)"
                fontSize={12}
              />
              <YAxis 
                stroke="rgba(255,255,255,0.6)"
                fontSize={12}
                domain={[0, 100]}
              />
              <Tooltip 
                contentStyle={{
                  backgroundColor: 'rgba(0,0,0,0.8)',
                  border: '1px solid rgba(255,255,255,0.2)',
                  borderRadius: '8px',
                  color: 'white'
                }}
              />
              <Line 
                type="monotone" 
                dataKey="stochastic" 
                stroke="#f093fb" 
                strokeWidth={2}
                dot={false}
              />
              <Line 
                type="monotone" 
                dataKey="80" 
                stroke="#ef5350" 
                strokeDasharray="5 5"
                strokeWidth={1}
              />
              <Line 
                type="monotone" 
                dataKey="20" 
                stroke="#26a69a" 
                strokeDasharray="5 5"
                strokeWidth={1}
              />
            </LineChart>
          </ResponsiveContainer>
        );

      case 'volume':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis 
                dataKey="date" 
                stroke="rgba(255,255,255,0.6)"
                fontSize={12}
              />
              <YAxis 
                stroke="rgba(255,255,255,0.6)"
                fontSize={12}
              />
              <Tooltip 
                contentStyle={{
                  backgroundColor: 'rgba(0,0,0,0.8)',
                  border: '1px solid rgba(255,255,255,0.2)',
                  borderRadius: '8px',
                  color: 'white'
                }}
              />
              <Area 
                type="monotone" 
                dataKey="volume" 
                fill="rgba(102, 126, 234, 0.3)"
                stroke="rgba(102, 126, 234, 0.8)"
                strokeWidth={2}
              />
            </AreaChart>
          </ResponsiveContainer>
        );

      default:
        return null;
    }
  };

  const getIndicatorDescription = () => {
    const option = indicatorOptions.find(opt => opt.value === selectedIndicator);
    return option ? option.description : '';
  };

  const getIndicatorIcon = (indicator) => {
    switch (indicator) {
      case 'rsi':
        return <Activity className="w-4 h-4" />;
      case 'macd':
        return <BarChart3 className="w-4 h-4" />;
      case 'bollinger':
        return <TrendingUp className="w-4 h-4" />;
      case 'stochastic':
        return <Zap className="w-4 h-4" />;
      case 'volume':
        return <BarChart3 className="w-4 h-4" />;
      default:
        return <BarChart3 className="w-4 h-4" />;
    }
  };

  if (!priceData || priceData.length < 20) {
    return (
      <div className="glass-card p-6">
        <h3 className="section-title">
          <BarChart3 />
          Technical Indicators
        </h3>
        <div className="text-center text-white/60 py-8">
          <BarChart3 className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>Insufficient data for technical analysis</p>
          <p className="text-sm">Need at least 20 data points</p>
        </div>
      </div>
    );
  }

  return (
    <div className="glass-card p-6">
      <h3 className="section-title">
        <BarChart3 />
        Technical Indicators
      </h3>
      
      {/* Indicator Selector */}
      <div className="mb-4">
        <div className="flex flex-wrap gap-2">
          {indicatorOptions.map(option => (
            <button
              key={option.value}
              className={`indicator-btn ${selectedIndicator === option.value ? 'active' : ''}`}
              onClick={() => setSelectedIndicator(option.value)}
            >
              {getIndicatorIcon(option.value)}
              <span>{option.label}</span>
            </button>
          ))}
        </div>
        <p className="text-sm text-white/60 mt-2">{getIndicatorDescription()}</p>
      </div>

      {/* Chart */}
      <div className="chart-container bg-white/5 rounded-lg p-4">
        {renderIndicatorChart()}
      </div>

      {/* Indicator Values */}
      {indicators && (
        <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
          {selectedIndicator === 'rsi' && indicators.rsi.length > 0 && (
            <div className="text-center">
              <div className="text-lg font-semibold text-white">
                {indicators.rsi[indicators.rsi.length - 1]?.toFixed(2)}
              </div>
              <div className="text-xs text-white/60">Current RSI</div>
              <div className={`text-xs ${
                indicators.rsi[indicators.rsi.length - 1] > 70 ? 'text-red-400' :
                indicators.rsi[indicators.rsi.length - 1] < 30 ? 'text-green-400' : 'text-yellow-400'
              }`}>
                {indicators.rsi[indicators.rsi.length - 1] > 70 ? 'Overbought' :
                 indicators.rsi[indicators.rsi.length - 1] < 30 ? 'Oversold' : 'Neutral'}
              </div>
            </div>
          )}
          
          {selectedIndicator === 'macd' && indicators.macd.macdLine.length > 0 && (
            <>
              <div className="text-center">
                <div className="text-lg font-semibold text-white">
                  {indicators.macd.macdLine[indicators.macd.macdLine.length - 1]?.toFixed(4)}
                </div>
                <div className="text-xs text-white/60">MACD Line</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-semibold text-white">
                  {indicators.macd.signalLine[indicators.macd.signalLine.length - 1]?.toFixed(4)}
                </div>
                <div className="text-xs text-white/60">Signal Line</div>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default TechnicalIndicators;
