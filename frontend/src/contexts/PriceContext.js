/**
 * Price Context - Provides real-time prices to all components
 * FIXED VERSION: Properly loads all coins needed for Market page
 *
 * REPLACE: src/contexts/PriceContext.js
 */
import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { fetchRealTimePrices } from '../services/priceService';

// All coins to fetch prices for
const TRACKED_COINS = ['BTC', 'ETH', 'USDT', 'SOL', 'XRP', 'DOGE', 'ADA', 'BNB', 'AVAX', 'MATIC', 'DOT', 'LINK'];

const PriceContext = createContext({
  prices: {},
  loading: true,
  error: null,
  refreshPrices: () => {},
});

export const PriceProvider = ({ children }) => {
  const [prices, setPrices] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchPrices = useCallback(async () => {
    try {
      const data = await fetchRealTimePrices(TRACKED_COINS);

      if (data && Object.keys(data).length > 0) {
        // Transform the data to match what MarketPage expects
        const formattedPrices = {};

        for (const [symbol, priceData] of Object.entries(data)) {
          formattedPrices[symbol] = {
            price: priceData.price || priceData.usd || 0,
            change_24h: priceData.change24h || priceData.change_24h || 0,
            volume_24h: priceData.volume24h || priceData.volume_24h || 0,
            market_cap: priceData.marketCap || priceData.market_cap || 0,
          };
        }

        setPrices(formattedPrices);
        setError(null);
      }
    } catch (err) {
      console.error('Error fetching prices:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial fetch
  useEffect(() => {
    fetchPrices();
  }, [fetchPrices]);

  // Set up polling every 30 seconds
  useEffect(() => {
    const interval = setInterval(fetchPrices, 30000);
    return () => clearInterval(interval);
  }, [fetchPrices]);

  const refreshPrices = useCallback(() => {
    setLoading(true);
    fetchPrices();
  }, [fetchPrices]);

  return (
    <PriceContext.Provider value={{ prices, loading, error, refreshPrices }}>
      {children}
    </PriceContext.Provider>
  );
};

export const usePrices = () => {
  const context = useContext(PriceContext);
  return context;
};

export default PriceContext;