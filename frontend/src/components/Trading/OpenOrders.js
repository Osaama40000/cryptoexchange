/**
 * OpenOrders Component
 * ====================
 * Displays user's open orders with cancel functionality
 */

import React, { useState, useEffect } from 'react';
import { useAuthStore } from '../../stores/authStore';

const OpenOrders = ({ symbol }) => {
  const { isAuthenticated } = useAuthStore();
  const [orders, setOrders] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState('all'); // all, buy, sell

  useEffect(() => {
    if (!isAuthenticated) {
      setOrders([]);
      setIsLoading(false);
      return;
    }

    // Simulate fetching orders
    setIsLoading(true);
    const timer = setTimeout(() => {
      // Mock open orders
      const mockOrders = [
        {
          id: '1',
          symbol: 'BTC/USDT',
          side: 'buy',
          type: 'limit',
          price: 42500.00,
          quantity: 0.05,
          filled: 0.02,
          status: 'partial',
          createdAt: new Date(Date.now() - 3600000).toISOString(),
        },
        {
          id: '2',
          symbol: 'BTC/USDT',
          side: 'sell',
          type: 'limit',
          price: 45000.00,
          quantity: 0.1,
          filled: 0,
          status: 'open',
          createdAt: new Date(Date.now() - 7200000).toISOString(),
        },
        {
          id: '3',
          symbol: 'ETH/USDT',
          side: 'buy',
          type: 'limit',
          price: 2500.00,
          quantity: 1.5,
          filled: 0,
          status: 'open',
          createdAt: new Date(Date.now() - 1800000).toISOString(),
        },
      ];
      
      setOrders(mockOrders);
      setIsLoading(false);
    }, 500);

    return () => clearTimeout(timer);
  }, [isAuthenticated, symbol]);

  const handleCancelOrder = (orderId) => {
    // Simulate cancel order
    setOrders(prev => prev.filter(order => order.id !== orderId));
  };

  const handleCancelAll = () => {
    setOrders([]);
  };

  const filteredOrders = orders.filter(order => {
    if (filter === 'all') return true;
    return order.side === filter;
  });

  const formatPrice = (price) => {
    return price.toLocaleString('en-US', { 
      minimumFractionDigits: 2, 
      maximumFractionDigits: 2 
    });
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit',
      hour12: false 
    });
  };

  const getFilledPercent = (order) => {
    return ((order.filled / order.quantity) * 100).toFixed(1);
  };

  if (!isAuthenticated) {
    return (
      <div className="bg-[#0d1117] rounded-lg border border-gray-800 p-4">
        <h3 className="text-white font-semibold mb-4">Open Orders</h3>
        <div className="text-center py-8">
          <p className="text-gray-500 mb-4">Please login to view your orders</p>
          <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
            Login
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-[#0d1117] rounded-lg border border-gray-800">
      {/* Header */}
      <div className="p-4 border-b border-gray-800">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-white font-semibold">Open Orders</h3>
          {orders.length > 0 && (
            <button
              onClick={handleCancelAll}
              className="text-xs text-red-400 hover:text-red-300 transition-colors"
            >
              Cancel All
            </button>
          )}
        </div>
        
        {/* Filter Tabs */}
        <div className="flex gap-2">
          {['all', 'buy', 'sell'].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1 text-xs font-medium rounded transition-colors ${
                filter === f
                  ? 'bg-gray-700 text-white'
                  : 'text-gray-500 hover:text-white'
              }`}
            >
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Orders List */}
      <div className="max-h-80 overflow-y-auto">
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin h-6 w-6 border-2 border-blue-500 border-t-transparent rounded-full"></div>
          </div>
        ) : filteredOrders.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <svg className="w-12 h-12 mx-auto mb-3 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            <p>No open orders</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-800">
            {filteredOrders.map((order) => (
              <div key={order.id} className="p-4 hover:bg-gray-800/30 transition-colors">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className={`text-xs font-medium px-2 py-0.5 rounded ${
                      order.side === 'buy' 
                        ? 'bg-green-500/20 text-green-400' 
                        : 'bg-red-500/20 text-red-400'
                    }`}>
                      {order.side.toUpperCase()}
                    </span>
                    <span className="text-white text-sm font-medium">{order.symbol}</span>
                    <span className="text-gray-500 text-xs">{order.type}</span>
                  </div>
                  <button
                    onClick={() => handleCancelOrder(order.id)}
                    className="text-gray-500 hover:text-red-400 transition-colors"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
                
                <div className="grid grid-cols-3 gap-2 text-sm">
                  <div>
                    <span className="text-gray-500 text-xs">Price</span>
                    <p className="text-white font-mono">${formatPrice(order.price)}</p>
                  </div>
                  <div>
                    <span className="text-gray-500 text-xs">Amount</span>
                    <p className="text-white font-mono">{order.quantity}</p>
                  </div>
                  <div>
                    <span className="text-gray-500 text-xs">Filled</span>
                    <p className="text-white font-mono">{getFilledPercent(order)}%</p>
                  </div>
                </div>
                
                {/* Progress Bar */}
                <div className="mt-2 h-1 bg-gray-800 rounded-full overflow-hidden">
                  <div 
                    className={`h-full ${order.side === 'buy' ? 'bg-green-500' : 'bg-red-500'}`}
                    style={{ width: `${getFilledPercent(order)}%` }}
                  />
                </div>
                
                <div className="mt-2 text-xs text-gray-500">
                  {formatDate(order.createdAt)}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default OpenOrders;
