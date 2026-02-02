/**
 * Live Price Ticker Component
 *
 * Displays real-time cryptocurrency prices with auto-refresh.
 * Shows price, 24h change, and market cap.
 *
 * ADD THIS FILE TO: frontend/src/components/LivePriceTicker.jsx
 */

import React, { useState, useEffect, useCallback } from 'react';
import { getPrices, formatPrice, formatPercentage, formatLargeNumber } from '../services/priceService';

const DEFAULT_COINS = ['BTC', 'ETH', 'USDT', 'BNB', 'SOL', 'XRP'];

const LivePriceTicker = ({
  coins = DEFAULT_COINS,
  refreshInterval = 30000,
  compact = false,
  showChange = true,
  onPriceUpdate = null
}) => {
  const [prices, setPrices] = useState({});
  const [isLoading, setIsLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [error, setError] = useState(null);

  const fetchPrices = useCallback(async () => {
    try {
      const data = await getPrices(coins);
      setPrices(data);
      setLastUpdate(new Date());
      setError(null);
      if (onPriceUpdate) onPriceUpdate(data);
    } catch (err) {
      console.error('Failed to fetch prices:', err);
      setError('Failed to load prices');
    } finally {
      setIsLoading(false);
    }
  }, [coins, onPriceUpdate]);

  useEffect(() => {
    fetchPrices();
    const interval = setInterval(fetchPrices, refreshInterval);
    return () => clearInterval(interval);
  }, [fetchPrices, refreshInterval]);

  const getCoinIcon = (symbol) => {
    const icons = {
      BTC: '₿', ETH: 'Ξ', USDT: '₮', BNB: '◆', SOL: '◎', XRP: '✕',
      ADA: '₳', DOGE: 'Ð', MATIC: '⬡', DOT: '●', DAI: '◇', LINK: '⬡',
      UNI: '🦄', AVAX: '🔺', ATOM: '⚛', LTC: 'Ł'
    };
    return icons[symbol] || '●';
  };

  const getChangeColor = (change) => {
    if (change > 0) return '#22c55e';
    if (change < 0) return '#ef4444';
    return '#94a3b8';
  };

  if (compact) {
    return (
      <div style={{
        display: 'flex',
        overflowX: 'auto',
        gap: '16px',
        padding: '12px',
        background: '#1e293b',
        borderRadius: '8px'
      }}>
        {isLoading ? (
          <div style={{ color: '#94a3b8' }}>Loading prices...</div>
        ) : (
          coins.map(symbol => {
            const data = prices[symbol];
            if (!data) return null;
            return (
              <div key={symbol} style={{ display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0 }}>
                <span style={{ fontWeight: 600, color: 'white' }}>{symbol}</span>
                <span style={{ color: '#e2e8f0' }}>{formatPrice(data.price)}</span>
                {showChange && (
                  <span style={{
                    fontSize: '12px', padding: '2px 6px', borderRadius: '4px',
                    color: getChangeColor(data.change24h),
                    background: `${getChangeColor(data.change24h)}20`
                  }}>
                    {formatPercentage(data.change24h)}
                  </span>
                )}
              </div>
            );
          })
        )}
      </div>
    );
  }

  return (
    <div style={{
      background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
      borderRadius: '16px',
      padding: '20px',
      color: 'white'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h3 style={{ fontSize: '18px', fontWeight: 600, margin: 0 }}>Live Prices</h3>
        <div style={{ fontSize: '12px', color: '#64748b', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <div style={{
            width: '8px', height: '8px', borderRadius: '50%', background: '#22c55e',
            animation: 'pulse 2s infinite'
          }}></div>
          <span>{lastUpdate ? `Updated ${lastUpdate.toLocaleTimeString()}` : 'Connecting...'}</span>
          <button onClick={fetchPrices} style={{
            background: 'transparent', border: 'none', color: '#6366f1',
            cursor: 'pointer', padding: '4px 8px', borderRadius: '4px', fontSize: '12px'
          }}>↻ Refresh</button>
        </div>
      </div>

      {error ? (
        <div style={{ textAlign: 'center', padding: '20px', color: '#ef4444' }}>
          {error}
          <button onClick={fetchPrices} style={{ marginLeft: '8px', color: '#6366f1', background: 'none', border: 'none', cursor: 'pointer' }}>
            Try Again
          </button>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '12px' }}>
          {coins.map(symbol => {
            const data = prices[symbol];

            if (isLoading) {
              return (
                <div key={symbol} style={{
                  background: 'rgba(255, 255, 255, 0.05)',
                  borderRadius: '12px',
                  padding: '16px',
                  height: '120px'
                }}>
                  <div style={{
                    background: 'linear-gradient(90deg, #374151 25%, #4b5563 50%, #374151 75%)',
                    height: '100%',
                    borderRadius: '8px'
                  }}></div>
                </div>
              );
            }

            if (!data) return null;

            return (
              <div key={symbol} style={{
                background: 'rgba(255, 255, 255, 0.05)',
                borderRadius: '12px',
                padding: '16px',
                transition: 'all 0.2s',
                cursor: 'pointer'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
                  <div style={{
                    width: '36px', height: '36px', borderRadius: '50%',
                    background: 'rgba(99, 102, 241, 0.2)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: '18px', fontWeight: 'bold', color: '#818cf8'
                  }}>
                    {getCoinIcon(symbol)}
                  </div>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '16px' }}>{symbol}</div>
                  </div>
                </div>

                <div style={{ fontSize: '24px', fontWeight: 700, marginBottom: '8px' }}>
                  {formatPrice(data.price)}
                </div>

                <span style={{
                  display: 'inline-flex', alignItems: 'center', gap: '4px',
                  padding: '4px 8px', borderRadius: '6px', fontSize: '13px', fontWeight: 500,
                  color: getChangeColor(data.change24h),
                  background: `${getChangeColor(data.change24h)}15`
                }}>
                  {data.change24h >= 0 ? '↑' : '↓'} {formatPercentage(data.change24h)}
                </span>

                <div style={{
                  marginTop: '12px', paddingTop: '12px',
                  borderTop: '1px solid rgba(255, 255, 255, 0.1)',
                  display: 'flex', justifyContent: 'space-between', fontSize: '12px'
                }}>
                  <span style={{ color: '#64748b' }}>Vol 24h</span>
                  <span style={{ color: '#e2e8f0' }}>{formatLargeNumber(data.volume24h)}</span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
      `}</style>
    </div>
  );
};

export default LivePriceTicker;