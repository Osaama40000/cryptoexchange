import { create } from 'zustand';
import { tradingAPI } from '../services/api';
import { fetchRealTimePrices, getPairPrice } from '../services/priceService';

export const useTradingStore = create((set, get) => ({
  // State
  tradingPairs: [],
  currentPair: null,
  orderBook: { bids: [], asks: [] },
  recentTrades: [],
  ticker: null,
  realPrices: {},
  isLoading: false,
  error: null,

  // Order form state
  orderForm: {
    side: 'buy',
    type: 'limit',
    price: '',
    quantity: '',
  },

  // Actions
  setCurrentPair: (pair) => set({ currentPair: pair }),
  
  setOrderForm: (updates) => set((state) => ({
    orderForm: { ...state.orderForm, ...updates }
  })),

  resetOrderForm: () => set({
    orderForm: {
      side: 'buy',
      type: 'limit',
      price: '',
      quantity: '',
    }
  }),

  // Fetch real-time prices from CoinGecko
  fetchRealPrices: async () => {
    try {
      const prices = await fetchRealTimePrices();
      set({ realPrices: prices });
      
      // Update current pair's ticker with real price
      const currentPair = get().currentPair;
      if (currentPair) {
        const priceData = await getPairPrice(currentPair.base_currency, currentPair.quote_currency);
        if (priceData) {
          set({ 
            ticker: {
              last_price: priceData.price,
              price_change_24h: priceData.change_24h,
              high_24h: priceData.price * 1.02,
              low_24h: priceData.price * 0.98,
              volume_24h: 0,
            }
          });
        }
      }
      return prices;
    } catch (error) {
      console.error('Error fetching real prices:', error);
      return {};
    }
  },

  // Fetch trading pairs
  fetchTradingPairs: async () => {
    try {
      const response = await tradingAPI.getTradingPairs();
      // Handle paginated response
      const pairs = response.data.results || response.data || [];
      
      // Fetch real prices
      const realPrices = await fetchRealTimePrices();
      
      // Update pairs with real prices
      const updatedPairs = pairs.map(pair => {
        const basePrice = realPrices[pair.base_currency];
        const quotePrice = realPrices[pair.quote_currency];
        
        let realPrice = pair.last_price;
        let realChange = pair.price_change_24h;
        
        if (basePrice && (pair.quote_currency === 'USDT' || pair.quote_currency === 'USD')) {
          realPrice = basePrice.price;
          realChange = basePrice.change_24h;
        } else if (basePrice && quotePrice) {
          realPrice = basePrice.price / quotePrice.price;
          realChange = basePrice.change_24h - quotePrice.change_24h;
        }
        
        return {
          ...pair,
          last_price: realPrice,
          price_change_24h: realChange,
        };
      });
      
      set({ tradingPairs: updatedPairs, realPrices });
      
      // Set first pair as current if none selected
      if (!get().currentPair && updatedPairs.length > 0) {
        set({ currentPair: updatedPairs[0] });
      }
      
      return updatedPairs;
    } catch (error) {
      console.error('Error fetching trading pairs:', error);
      set({ tradingPairs: [] });
      return [];
    }
  },

  // Fetch order book
  fetchOrderBook: async (symbol) => {
    try {
      const response = await tradingAPI.getOrderBook(symbol);
      set({ orderBook: response.data });
      return response.data;
    } catch (error) {
      console.error('Error fetching order book:', error);
      // Generate mock order book based on real price
      const currentPair = get().currentPair;
      const realPrices = get().realPrices;
      
      if (currentPair && realPrices[currentPair.base_currency]) {
        const basePrice = realPrices[currentPair.base_currency].price;
        const mockOrderBook = generateMockOrderBook(basePrice);
        set({ orderBook: mockOrderBook });
        return mockOrderBook;
      }
      
      set({ orderBook: { bids: [], asks: [] } });
      return null;
    }
  },

  // Fetch recent trades
  fetchRecentTrades: async (symbol) => {
    try {
      const response = await tradingAPI.getRecentTrades(symbol);
      // Handle paginated response
      const trades = response.data.results || response.data || [];
      set({ recentTrades: trades });
      return trades;
    } catch (error) {
      console.error('Error fetching recent trades:', error);
      set({ recentTrades: [] });
      return [];
    }
  },

  // Fetch ticker - now uses real prices
  fetchTicker: async (symbol) => {
    try {
      // First try the API
      const response = await tradingAPI.getTicker(symbol);
      set({ ticker: response.data });
      return response.data;
    } catch (error) {
      // Fallback to real prices from CoinGecko
      console.log('Using real-time prices for ticker');
      const currentPair = get().currentPair;
      
      if (currentPair) {
        const priceData = await getPairPrice(currentPair.base_currency, currentPair.quote_currency);
        if (priceData) {
          const ticker = {
            last_price: priceData.price,
            price_change_24h: priceData.change_24h,
            high_24h: priceData.price * 1.02,
            low_24h: priceData.price * 0.98,
            volume_24h: Math.random() * 1000000,
          };
          set({ ticker });
          return ticker;
        }
      }
      
      set({ ticker: null });
      return null;
    }
  },

  // Create order
  createOrder: async (orderData) => {
    set({ isLoading: true, error: null });
    try {
      const response = await tradingAPI.createOrder(orderData);
      set({ isLoading: false });
      
      // Refresh order book after placing order
      if (get().currentPair) {
        get().fetchOrderBook(get().currentPair.symbol);
      }
      
      return { success: true, data: response.data };
    } catch (error) {
      const message = error.response?.data?.error ||
                     Object.values(error.response?.data || {})[0]?.[0] ||
                     'Order failed';
      set({ error: message, isLoading: false });
      return { success: false, error: message };
    }
  },

  // Cancel order
  cancelOrder: async (orderId) => {
    try {
      await tradingAPI.cancelOrder(orderId);
      return { success: true };
    } catch (error) {
      const message = error.response?.data?.error || 'Cancel failed';
      return { success: false, error: message };
    }
  },
}));

// Helper function to generate mock order book based on real price
function generateMockOrderBook(basePrice) {
  const bids = [];
  const asks = [];
  
  for (let i = 0; i < 10; i++) {
    const bidPrice = basePrice * (1 - (i + 1) * 0.001);
    const askPrice = basePrice * (1 + (i + 1) * 0.001);
    const quantity = Math.random() * 2;
    
    bids.push({
      price: bidPrice.toFixed(2),
      quantity: quantity.toFixed(6),
      total: (bidPrice * quantity).toFixed(2),
    });
    
    asks.push({
      price: askPrice.toFixed(2),
      quantity: quantity.toFixed(6),
      total: (askPrice * quantity).toFixed(2),
    });
  }
  
  return { bids, asks };
}
