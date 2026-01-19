/**
 * TradingChart Component
 * ======================
 * Professional candlestick chart using TradingView's lightweight-charts
 */

import React, { useEffect, useRef, useState, useCallback } from 'react';
import { createChart, CrosshairMode } from 'lightweight-charts';

const TIMEFRAMES = [
  { label: '1m', value: '1m', seconds: 60 },
  { label: '5m', value: '5m', seconds: 300 },
  { label: '15m', value: '15m', seconds: 900 },
  { label: '1H', value: '1h', seconds: 3600 },
  { label: '4H', value: '4h', seconds: 14400 },
  { label: '1D', value: '1d', seconds: 86400 },
  { label: '1W', value: '1w', seconds: 604800 },
];

const TradingChart = ({ symbol = 'BTC/USDT', onPriceUpdate }) => {
  const chartContainerRef = useRef(null);
  const chartRef = useRef(null);
  const candlestickSeriesRef = useRef(null);
  const volumeSeriesRef = useRef(null);
  const [selectedTimeframe, setSelectedTimeframe] = useState('1h');
  const [chartData, setChartData] = useState([]);
  const [currentPrice, setCurrentPrice] = useState(null);
  const [priceChange, setPriceChange] = useState({ value: 0, percent: 0 });
  const [stats, setStats] = useState({ high: 0, low: 0, volume: 0 });
  const [isLoading, setIsLoading] = useState(true);

  // Generate realistic mock data
  const generateMockData = useCallback((timeframe) => {
    const data = [];
    const volumeData = [];
    const now = Math.floor(Date.now() / 1000);
    const tf = TIMEFRAMES.find(t => t.value === timeframe);
    const interval = tf?.seconds || 3600;
    const points = 200;
    
    // Starting price based on symbol
    let basePrice = symbol.includes('BTC') ? 43500 : 
                    symbol.includes('ETH') ? 2650 : 
                    symbol.includes('SOL') ? 98 : 100;
    
    let price = basePrice;
    let prevClose = price;
    
    for (let i = points; i >= 0; i--) {
      const time = now - (i * interval);
      
      // Random walk with trend
      const volatility = basePrice * 0.002; // 0.2% volatility
      const trend = Math.sin(i / 50) * volatility * 0.5;
      const random = (Math.random() - 0.5) * volatility * 2;
      
      const open = prevClose;
      const change = trend + random;
      const close = open + change;
      const high = Math.max(open, close) + Math.random() * volatility;
      const low = Math.min(open, close) - Math.random() * volatility;
      
      data.push({
        time,
        open: parseFloat(open.toFixed(2)),
        high: parseFloat(high.toFixed(2)),
        low: parseFloat(low.toFixed(2)),
        close: parseFloat(close.toFixed(2)),
      });
      
      volumeData.push({
        time,
        value: Math.floor(Math.random() * 1000000) + 500000,
        color: close >= open ? 'rgba(38, 166, 154, 0.5)' : 'rgba(239, 83, 80, 0.5)',
      });
      
      prevClose = close;
    }
    
    // Calculate stats
    const closes = data.map(d => d.close);
    const highs = data.map(d => d.high);
    const lows = data.map(d => d.low);
    const volumes = volumeData.map(d => d.value);
    
    const currentClose = closes[closes.length - 1];
    const openPrice = data[0].open;
    const change = currentClose - openPrice;
    const changePercent = (change / openPrice) * 100;
    
    setCurrentPrice(currentClose);
    setPriceChange({ value: change, percent: changePercent });
    setStats({
      high: Math.max(...highs),
      low: Math.min(...lows),
      volume: volumes.reduce((a, b) => a + b, 0),
    });
    
    if (onPriceUpdate) {
      onPriceUpdate(currentClose);
    }
    
    return { candles: data, volume: volumeData };
  }, [symbol, onPriceUpdate]);

  // Initialize chart
  useEffect(() => {
    if (!chartContainerRef.current) return;

    // Create chart
    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: 'solid', color: '#0d1117' },
        textColor: '#d1d5db',
      },
      grid: {
        vertLines: { color: '#1f2937' },
        horzLines: { color: '#1f2937' },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: {
          width: 1,
          color: '#6b7280',
          style: 2,
          labelBackgroundColor: '#374151',
        },
        horzLine: {
          width: 1,
          color: '#6b7280',
          style: 2,
          labelBackgroundColor: '#374151',
        },
      },
      rightPriceScale: {
        borderColor: '#374151',
        scaleMargins: {
          top: 0.1,
          bottom: 0.2,
        },
      },
      timeScale: {
        borderColor: '#374151',
        timeVisible: true,
        secondsVisible: false,
      },
      handleScroll: {
        vertTouchDrag: false,
      },
    });

    // Candlestick series
    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#22c55e',
      downColor: '#ef4444',
      borderDownColor: '#ef4444',
      borderUpColor: '#22c55e',
      wickDownColor: '#ef4444',
      wickUpColor: '#22c55e',
    });

    // Volume series
    const volumeSeries = chart.addHistogramSeries({
      color: '#26a69a',
      priceFormat: {
        type: 'volume',
      },
      priceScaleId: '',
      scaleMargins: {
        top: 0.85,
        bottom: 0,
      },
    });

    chartRef.current = chart;
    candlestickSeriesRef.current = candlestickSeries;
    volumeSeriesRef.current = volumeSeries;

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({
          width: chartContainerRef.current.clientWidth,
          height: chartContainerRef.current.clientHeight,
        });
      }
    };

    window.addEventListener('resize', handleResize);
    handleResize();

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, []);

  // Load data when timeframe changes
  useEffect(() => {
    setIsLoading(true);
    
    // Simulate API call delay
    const timer = setTimeout(() => {
      const { candles, volume } = generateMockData(selectedTimeframe);
      setChartData(candles);
      
      if (candlestickSeriesRef.current && volumeSeriesRef.current) {
        candlestickSeriesRef.current.setData(candles);
        volumeSeriesRef.current.setData(volume);
      }
      
      setIsLoading(false);
    }, 300);
    
    return () => clearTimeout(timer);
  }, [selectedTimeframe, generateMockData]);

  // Simulate real-time updates
  useEffect(() => {
    if (!candlestickSeriesRef.current || chartData.length === 0) return;
    
    const interval = setInterval(() => {
      const lastCandle = chartData[chartData.length - 1];
      if (!lastCandle) return;
      
      // Small random price movement
      const change = (Math.random() - 0.5) * lastCandle.close * 0.001;
      const newClose = lastCandle.close + change;
      
      const updatedCandle = {
        ...lastCandle,
        close: parseFloat(newClose.toFixed(2)),
        high: Math.max(lastCandle.high, newClose),
        low: Math.min(lastCandle.low, newClose),
      };
      
      candlestickSeriesRef.current.update(updatedCandle);
      setCurrentPrice(updatedCandle.close);
      
      // Update price change
      const openPrice = chartData[0]?.open || updatedCandle.open;
      const priceChangeValue = updatedCandle.close - openPrice;
      const priceChangePercent = (priceChangeValue / openPrice) * 100;
      setPriceChange({ value: priceChangeValue, percent: priceChangePercent });
      
      if (onPriceUpdate) {
        onPriceUpdate(updatedCandle.close);
      }
    }, 2000);
    
    return () => clearInterval(interval);
  }, [chartData, onPriceUpdate]);

  const formatNumber = (num, decimals = 2) => {
    if (num >= 1e9) return (num / 1e9).toFixed(decimals) + 'B';
    if (num >= 1e6) return (num / 1e6).toFixed(decimals) + 'M';
    if (num >= 1e3) return (num / 1e3).toFixed(decimals) + 'K';
    return num.toFixed(decimals);
  };

  const formatPrice = (price) => {
    if (!price) return '0.00';
    if (price >= 1000) return price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    if (price >= 1) return price.toFixed(2);
    return price.toFixed(6);
  };

  return (
    <div className="bg-[#0d1117] rounded-lg border border-gray-800 overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-gray-800">
        <div className="flex flex-wrap items-center justify-between gap-4">
          {/* Symbol & Price */}
          <div className="flex items-center gap-4">
            <div>
              <h2 className="text-xl font-bold text-white">{symbol}</h2>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-2xl font-mono font-bold text-white">
                  ${formatPrice(currentPrice)}
                </span>
                <span className={`text-sm font-medium px-2 py-0.5 rounded ${
                  priceChange.percent >= 0 
                    ? 'text-green-400 bg-green-400/10' 
                    : 'text-red-400 bg-red-400/10'
                }`}>
                  {priceChange.percent >= 0 ? '+' : ''}{priceChange.percent.toFixed(2)}%
                </span>
              </div>
            </div>
          </div>
          
          {/* Stats */}
          <div className="flex items-center gap-6 text-sm">
            <div>
              <span className="text-gray-500">24h High</span>
              <p className="text-white font-mono">${formatPrice(stats.high)}</p>
            </div>
            <div>
              <span className="text-gray-500">24h Low</span>
              <p className="text-white font-mono">${formatPrice(stats.low)}</p>
            </div>
            <div>
              <span className="text-gray-500">24h Volume</span>
              <p className="text-white font-mono">${formatNumber(stats.volume)}</p>
            </div>
          </div>
        </div>
        
        {/* Timeframe Selector */}
        <div className="flex items-center gap-1 mt-4">
          {TIMEFRAMES.map((tf) => (
            <button
              key={tf.value}
              onClick={() => setSelectedTimeframe(tf.value)}
              className={`px-3 py-1.5 text-sm font-medium rounded transition-colors ${
                selectedTimeframe === tf.value
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800'
              }`}
            >
              {tf.label}
            </button>
          ))}
        </div>
      </div>
      
      {/* Chart Container */}
      <div className="relative">
        {isLoading && (
          <div className="absolute inset-0 bg-[#0d1117]/80 flex items-center justify-center z-10">
            <div className="flex items-center gap-2 text-gray-400">
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              <span>Loading chart...</span>
            </div>
          </div>
        )}
        <div 
          ref={chartContainerRef} 
          className="w-full"
          style={{ height: '400px' }}
        />
      </div>
      
      {/* Chart Legend */}
      <div className="px-4 py-2 border-t border-gray-800 flex items-center gap-4 text-xs text-gray-500">
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 bg-green-500 rounded-sm"></span> Bullish
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 bg-red-500 rounded-sm"></span> Bearish
        </span>
        <span className="ml-auto">Powered by TradingView</span>
      </div>
    </div>
  );
};

export default TradingChart;
