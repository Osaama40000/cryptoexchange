/**
 * PriceTicker Component
 * =====================
 * Scrolling price ticker for top of page
 */

import React, { useState, useEffect } from 'react';

const TICKERS = [
  { symbol: 'BTC', name: 'Bitcoin', basePrice: 43500 },
  { symbol: 'ETH', name: 'Ethereum', basePrice: 2650 },
  { symbol: 'SOL', name: 'Solana', basePrice: 98 },
  { symbol: 'XRP', name: 'Ripple', basePrice: 0.62 },
  { symbol: 'ADA', name: 'Cardano', basePrice: 0.58 },
  { symbol: 'DOGE', name: 'Dogecoin', basePrice: 0.085 },
  { symbol: 'DOT', name: 'Polkadot', basePrice: 7.85 },
  { symbol: 'MATIC', name: 'Polygon', basePrice: 0.92 },
];

const PriceTicker = () => {
  const [prices, setPrices] = useState([]);

  useEffect(() => {
    // Initialize prices
    const initialPrices = TICKERS.map(ticker => ({
      ...ticker,
      price: ticker.basePrice * (1 + (Math.random() - 0.5) * 0.02),
      change: (Math.random() - 0.45) * 8,
    }));
    setPrices(initialPrices);

    // Simulate real-time updates
    const interval = setInterval(() => {
      setPrices(prev => prev.map(ticker => {
        const priceChange = (Math.random() - 0.5) * ticker.basePrice * 0.001;
        return {
          ...ticker,
          price: ticker.price + priceChange,
          change: ticker.change + (Math.random() - 0.5) * 0.1,
        };
      }));
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  const formatPrice = (price) => {
    if (price >= 1000) return price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    if (price >= 1) return price.toFixed(2);
    return price.toFixed(4);
  };

  // Duplicate for seamless scroll
  const tickerItems = [...prices, ...prices];

  return (
    <div className="bg-[#0a0e14] border-b border-gray-800 overflow-hidden">
      <div className="animate-ticker flex items-center py-2">
        {tickerItems.map((ticker, index) => (
          <div
            key={`${ticker.symbol}-${index}`}
            className="flex items-center gap-3 px-6 border-r border-gray-800 whitespace-nowrap"
          >
            <span className="text-white font-semibold">{ticker.symbol}</span>
            <span className="text-white font-mono">${formatPrice(ticker.price)}</span>
            <span className={`text-sm ${
              ticker.change >= 0 ? 'text-green-400' : 'text-red-400'
            }`}>
              {ticker.change >= 0 ? '+' : ''}{ticker.change.toFixed(2)}%
            </span>
          </div>
        ))}
      </div>
      
      <style jsx>{`
        @keyframes ticker {
          0% { transform: translateX(0); }
          100% { transform: translateX(-50%); }
        }
        .animate-ticker {
          animation: ticker 30s linear infinite;
        }
        .animate-ticker:hover {
          animation-play-state: paused;
        }
      `}</style>
    </div>
  );
};

export default PriceTicker;
