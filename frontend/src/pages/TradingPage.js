/**
 * TradingPage Component
 * =====================
 * Main trading interface with charts, order book, and trade form
 */

import React, { useState } from 'react';
import TradingChart from '../components/Trading/TradingChart';
import MarketOverview from '../components/Trading/MarketOverview';
import PriceTicker from '../components/Trading/PriceTicker';
import OrderBook from '../components/Trading/OrderBook';
import TradeForm from '../components/Trading/TradeForm';
import RecentTrades from '../components/Trading/RecentTrades';
import OpenOrders from '../components/Trading/OpenOrders';

const TradingPage = () => {
  const [selectedSymbol, setSelectedSymbol] = useState('BTC/USDT');
  const [currentPrice, setCurrentPrice] = useState(null);
  const [activeTab, setActiveTab] = useState('chart'); // For mobile

  const handleSelectMarket = (symbol) => {
    setSelectedSymbol(symbol);
  };

  const handlePriceUpdate = (price) => {
    setCurrentPrice(price);
  };

  return (
    <div className="min-h-screen bg-[#0a0e14]">
      {/* Price Ticker */}
      <PriceTicker />
      
      <div className="container mx-auto px-4 py-6">
        {/* Market Overview */}
        <div className="mb-6">
          <h2 className="text-lg font-semibold text-white mb-4">Markets</h2>
          <MarketOverview onSelectMarket={handleSelectMarket} />
        </div>
        
        {/* Mobile Tab Selector */}
        <div className="lg:hidden flex gap-2 mb-4 overflow-x-auto pb-2">
          {['chart', 'orderbook', 'trades', 'orders'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
                activeTab === tab
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-800 text-gray-400 hover:text-white'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>
        
        {/* Main Trading Interface */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
          {/* Left Column - Order Book (Desktop) */}
          <div className="hidden lg:block lg:col-span-3">
            <OrderBook symbol={selectedSymbol} />
          </div>
          
          {/* Center Column - Chart & Trade Form */}
          <div className="lg:col-span-6 space-y-4">
            {/* Chart - Show on desktop or when chart tab active on mobile */}
            <div className={`${activeTab !== 'chart' ? 'hidden lg:block' : ''}`}>
              <TradingChart 
                symbol={selectedSymbol} 
                onPriceUpdate={handlePriceUpdate}
              />
            </div>
            
            {/* Trade Form */}
            <div className="bg-[#0d1117] rounded-lg border border-gray-800 p-4">
              <TradeForm 
                symbol={selectedSymbol} 
                currentPrice={currentPrice}
              />
            </div>
            
            {/* Open Orders */}
            <div className={`${activeTab !== 'orders' ? 'hidden lg:block' : ''}`}>
              <OpenOrders symbol={selectedSymbol} />
            </div>
          </div>
          
          {/* Right Column - Recent Trades (Desktop) */}
          <div className="hidden lg:block lg:col-span-3">
            <RecentTrades symbol={selectedSymbol} />
          </div>
          
          {/* Mobile Views */}
          <div className="lg:hidden col-span-1">
            {activeTab === 'orderbook' && <OrderBook symbol={selectedSymbol} />}
            {activeTab === 'trades' && <RecentTrades symbol={selectedSymbol} />}
            {activeTab === 'orders' && <OpenOrders symbol={selectedSymbol} />}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TradingPage;
