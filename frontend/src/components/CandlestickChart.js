import React, { useEffect, useRef, useState } from 'react';
import { TrendingUp, ZoomIn, ZoomOut, RotateCcw, Maximize2 } from 'lucide-react';
import { createChart } from 'lightweight-charts';

const TimeRangeSelector = ({ selectedRange, onRangeChange }) => {
  const ranges = [
    { label: '1D', value: '1d', hours: 24 },
    { label: '1W', value: '1w', hours: 168 },
    { label: '1M', value: '1m', hours: 720 },
    { label: '3M', value: '3m', hours: 2160 },
    { label: '1Y', value: '1y', hours: 8760 }
  ];

  return (
    <div className="flex gap-2 mb-4">
      {ranges.map(range => (
        <button
          key={range.value}
          className={`time-btn ${selectedRange === range.value ? 'active' : ''}`}
          onClick={() => onRangeChange(range.value)}
        >
          {range.label}
        </button>
      ))}
    </div>
  );
};

const CandlestickChart = ({ priceData, forecasts, timeRange, onTimeRangeChange }) => {
  const chartContainerRef = useRef();
  const chartRef = useRef();
  const candlestickSeriesRef = useRef();
  const volumeSeriesRef = useRef();
  const forecastSeriesRef = useRef();
  const confidenceSeriesRef = useRef();
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [chartReady, setChartReady] = useState(false);

  // Filter data based on time range
  const filterDataByTimeRange = (data, range) => {
    if (!data || data.length === 0) return data;
    
    // For demo purposes with historical data, just return the data
    // In a real application, you'd filter based on the actual time range
    return data;
  };

  // Initialize chart
  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 500,
      layout: {
        background: { color: 'rgba(0, 0, 0, 0.1)' },
        textColor: '#ffffff',
      },
      grid: {
        vertLines: { color: 'rgba(255, 255, 255, 0.1)' },
        horzLines: { color: 'rgba(255, 255, 255, 0.1)' },
      },
      crosshair: {
        mode: 1,
      },
      rightPriceScale: {
        borderColor: 'rgba(255, 255, 255, 0.2)',
      },
      timeScale: {
        borderColor: 'rgba(255, 255, 255, 0.2)',
        timeVisible: true,
        secondsVisible: false,
      },
      handleScroll: {
        mouseWheel: true,
        pressedMouseMove: true,
      },
      handleScale: {
        axisPressedMouseMove: true,
        mouseWheel: true,
        pinch: true,
      },
    });

    // Create candlestick series
    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderDownColor: '#ef5350',
      borderUpColor: '#26a69a',
      wickDownColor: '#ef5350',
      wickUpColor: '#26a69a',
    });

    // Create volume series
    const volumeSeries = chart.addHistogramSeries({
      color: 'rgba(102, 126, 234, 0.3)',
      priceFormat: {
        type: 'volume',
      },
      priceScaleId: '',
      scaleMargins: {
        top: 0.8,
        bottom: 0,
      },
    });

    // Create forecast series
    const forecastSeries = chart.addLineSeries({
      color: '#ffd700',
      lineWidth: 2,
      lineStyle: 2, // dashed
      title: 'Forecast',
    });

    // Create confidence interval series
    const confidenceSeries = chart.addAreaSeries({
      topColor: 'rgba(255, 215, 0, 0.1)',
      bottomColor: 'rgba(255, 215, 0, 0.05)',
      lineColor: 'rgba(255, 215, 0, 0.3)',
      lineWidth: 1,
      title: 'Confidence Interval',
    });

    chartRef.current = chart;
    candlestickSeriesRef.current = candlestickSeries;
    volumeSeriesRef.current = volumeSeries;
    forecastSeriesRef.current = forecastSeries;
    confidenceSeriesRef.current = confidenceSeries;

    setChartReady(true);

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({
          width: chartContainerRef.current.clientWidth,
          height: isFullscreen ? window.innerHeight - 100 : 500,
        });
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [isFullscreen]);

  // Update chart data
  useEffect(() => {
    if (!chartReady || !priceData || priceData.length === 0) {
      return;
    }

  const filteredData = filterDataByTimeRange(priceData, timeRange);
    
    // Sort data by time in ascending order (required by lightweight-charts)
    const sortedData = [...filteredData].sort((a, b) => new Date(a.date) - new Date(b.date));
    
    // Remove duplicates based on timestamp using Map for better performance
    const dataMap = new Map();
    sortedData.forEach(item => {
      const timestamp = new Date(item.date).getTime() / 1000;
      dataMap.set(timestamp, item);
    });
    const uniqueData = Array.from(dataMap.values());

  // Convert price data to candlestick format
    const candlestickData = uniqueData.map(d => ({
      time: new Date(d.date).getTime() / 1000, // Convert to seconds
    open: d.open_price,
    high: d.high_price,
    low: d.low_price,
    close: d.close_price,
    }));

    // Convert volume data with deduplication
    const volumeMap = new Map();
    uniqueData.forEach(d => {
      const timestamp = new Date(d.date).getTime() / 1000;
      volumeMap.set(timestamp, {
        time: timestamp,
        value: d.volume || 0,
        color: d.close_price >= d.open_price ? '#26a69a' : '#ef5350',
      });
    });
    const volumeData = Array.from(volumeMap.values());

    // Update series
    candlestickSeriesRef.current.setData(candlestickData);
    volumeSeriesRef.current.setData(volumeData);

    // Fit content to show all data
    chartRef.current.timeScale().fitContent();
  }, [chartReady, priceData, timeRange]);

  // Update forecast data
  useEffect(() => {
    if (!chartReady || !forecasts || !priceData || priceData.length === 0) return;

    // Get the last data point from the sorted unique data
    const filteredData = filterDataByTimeRange(priceData, timeRange);
    const sortedData = [...filteredData].sort((a, b) => new Date(a.date) - new Date(b.date));
    
    // Remove duplicates
    const dataMap = new Map();
    sortedData.forEach(item => {
      const timestamp = new Date(item.date).getTime() / 1000;
      dataMap.set(timestamp, item);
    });
    const uniqueData = Array.from(dataMap.values());
    
    const lastDataPoint = uniqueData[uniqueData.length - 1];
    const lastTime = new Date(lastDataPoint.date).getTime() / 1000;

    // Create forecast data with proper time spacing and deduplication
    const forecastMap = new Map();
    forecasts.predictions.forEach((prediction, index) => {
      const timestamp = lastTime + (index + 1) * 3600;
      forecastMap.set(timestamp, {
        time: timestamp,
        value: prediction,
      });
    });
    const forecastData = Array.from(forecastMap.values());

    // Create confidence interval data with deduplication
    const confidenceMap = new Map();
    
    // Add upper confidence bounds
    forecasts.predictions.forEach((prediction, index) => {
      const timestamp = lastTime + (index + 1) * 3600;
      confidenceMap.set(timestamp, {
        time: timestamp,
        value: forecasts.confidence_intervals.upper[index],
      });
    });
    
    // Add lower confidence bounds (reverse order for area chart)
    forecasts.predictions.forEach((prediction, index) => {
      const reverseIndex = forecasts.predictions.length - 1 - index;
      const reverseTimestamp = lastTime + (reverseIndex + 1) * 3600;
      confidenceMap.set(reverseTimestamp, {
        time: reverseTimestamp,
        value: forecasts.confidence_intervals.lower[reverseIndex],
      });
    });
    
    const confidenceData = Array.from(confidenceMap.values());

    // Ensure forecast data is sorted by time
    forecastData.sort((a, b) => a.time - b.time);
    confidenceData.sort((a, b) => a.time - b.time);

    forecastSeriesRef.current.setData(forecastData);
    confidenceSeriesRef.current.setData(confidenceData);
  }, [chartReady, forecasts, priceData, timeRange]);

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  const resetZoom = () => {
    if (chartRef.current) {
      chartRef.current.timeScale().fitContent();
    }
  };

  const zoomIn = () => {
    if (chartRef.current) {
      const timeScale = chartRef.current.timeScale();
      const visibleRange = timeScale.getVisibleRange();
      if (visibleRange) {
        const range = visibleRange.to - visibleRange.from;
        timeScale.setVisibleRange({
          from: visibleRange.from + range * 0.1,
          to: visibleRange.to - range * 0.1,
        });
      }
    }
  };

  const zoomOut = () => {
    if (chartRef.current) {
      const timeScale = chartRef.current.timeScale();
      const visibleRange = timeScale.getVisibleRange();
      if (visibleRange) {
        const range = visibleRange.to - visibleRange.from;
        timeScale.setVisibleRange({
          from: visibleRange.from - range * 0.1,
          to: visibleRange.to + range * 0.1,
        });
      }
    }
  };

  return (
    <div className={`glass-card p-6 ${isFullscreen ? 'fixed inset-0 z-50 m-0' : ''}`}>
      <div className="flex justify-between items-center mb-4">
        <h3 className="section-title">
          <TrendingUp />
          Interactive Price Chart
        </h3>
        <div className="flex items-center gap-2">
        <TimeRangeSelector 
          selectedRange={timeRange} 
            onRangeChange={onTimeRangeChange} 
          />
          <div className="flex gap-1">
            <button
              className="chart-control-btn"
              onClick={zoomIn}
              title="Zoom In"
            >
              <ZoomIn className="w-4 h-4" />
            </button>
            <button
              className="chart-control-btn"
              onClick={zoomOut}
              title="Zoom Out"
            >
              <ZoomOut className="w-4 h-4" />
            </button>
            <button
              className="chart-control-btn"
              onClick={resetZoom}
              title="Reset Zoom"
            >
              <RotateCcw className="w-4 h-4" />
            </button>
            <button
              className="chart-control-btn"
              onClick={toggleFullscreen}
              title="Toggle Fullscreen"
            >
              <Maximize2 className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
      
      <div className="chart-container">
        {priceData && priceData.length > 0 ? (
          <div 
            ref={chartContainerRef} 
            className="w-full h-full"
            style={{ height: isFullscreen ? 'calc(100vh - 120px)' : '500px' }}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <div className="text-center text-white">
              <TrendingUp className="w-16 h-16 mx-auto mb-4 opacity-50" />
              <h4 className="text-xl font-semibold mb-2">No Data Available</h4>
              <p className="text-sm opacity-75">
                Select an instrument to view price data
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Chart Legend */}
      {priceData && priceData.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-4 text-sm text-white/80">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-green-400 rounded"></div>
            <span>Bullish Candles</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-red-400 rounded"></div>
            <span>Bearish Candles</span>
          </div>
          {forecasts && (
            <>
              <div className="flex items-center gap-2">
                <div className="w-3 h-0.5 bg-yellow-400 border-dashed border-t-2"></div>
                <span>Forecast</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-yellow-400/20 rounded"></div>
                <span>Confidence Interval</span>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default CandlestickChart;