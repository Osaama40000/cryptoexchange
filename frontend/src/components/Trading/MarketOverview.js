/**
 * MarketOverview Component
 * ========================
 * Shows market cards with mini charts
 */

import React, { useState, useEffect } from 'react';
import MiniChart from './MiniChart';

const MARKETS = [
  { symbol: 'BTC/USDT', name: 'Bitcoin', icon: '₿', basePrice: 43500 },
  { symbol: 'ETH/USDT', name: 'Ethereum', icon: 'Ξ', basePrice: 2650 },
  { symbol: 'SOL/USDT', name: 'Solana', icon: '◎', basePrice: 98 },
  { symbol: 'XRP/USDT', name: 'Ripple', icon: '✕', basePrice: 0.62 },
];

const MarketOverview = ({ onSelectMarket }) => {
  const [marketData, setMarketData] = useState([]);

  useEffect(() => {
    // Generate mock market data
    const data = MARKETS.map(market => {
      const changePercent = (Math.random() - 0.45) * 10;
      const price = market.basePrice * (1 + changePercent / 100);
      const volume = Math.random() * 1000000000 + 100000000;
      
      // Generate chart data
      const chartData = [];
      const now = Math.floor(Date.now() / 1000);
      let value = market.basePrice * 0.98;
      
      for (let i = 48; i >= 0; i--) {
        value += (Math.random() - 0.48) * market.basePrice * 0.005;
        chartData.push({
          time: now - i * 3600,
          value: value,
        });
      }
      
      return {
        ...market,
        price,
        changePercent,
        volume,
        chartData,
      };
    });
    
    setMarketData(data);
    
    // Simulate real-time updates
    const interval = setInterval(() => {
      setMarketData(prev => prev.map(market => {
        const change = (Math.random() - 0.5) * market.basePrice * 0.001;
        return {
          ...market,
          price: market.price + change,
          changePercent: market.changePercent + (Math.random() - 0.5) * 0.1,
        };
      }));
    }, 3000);
    
    return () => clearInterval(interval);
  }, []);

  const formatPrice = (price) => {
    if (price >= 1000) return price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    if (price >= 1) return price.toFixed(2);
    return price.toFixed(4);
  };

  const formatVolume = (volume) => {
    if (volume >= 1e9) return (volume / 1e9).toFixed(2) + 'B';
    if (volume >= 1e6) return (volume / 1e6).toFixed(2) + 'M';
    return (volume / 1e3).toFixed(2) + 'K';
  };

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {marketData.map((market) => (
        <div
          key={market.symbol}
          onClick={() => onSelectMarket?.(market.symbol)}
          className="bg-[#0d1117] rounded-lg border border-gray-800 p-4 cursor-pointer hover:border-gray-700 transition-colors"
        >
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <span className="text-2xl">{market.icon}</span>
              <div>
                <h3 className="text-white font-semibold">{market.symbol}</h3>
                <p className="text-gray-500 text-xs">{market.name}</p>
              </div>
            </div>
            <span className={`text-sm font-medium px-2 py-0.5 rounded ${
              market.changePercent >= 0 
                ? 'text-green-400 bg-green-400/10' 
                : 'text-red-400 bg-red-400/10'
            }`}>
              {market.changePercent >= 0 ? '+' : ''}{market.changePercent.toFixed(2)}%
            </span>
          </div>
          
          <div className="my-2">
            <MiniChart 
              data={market.chartData} 
              color={market.changePercent >= 0 ? '#22c55e' : '#ef4444'}
              height={50}
            />
          </div>
          
          <div className="flex items-center justify-between mt-2">
            <span className="text-white font-mono font-bold">
              ${formatPrice(market.price)}
            </span>
            <span className="text-gray-500 text-xs">
              Vol: ${formatVolume(market.volume)}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
};

export default MarketOverview;
