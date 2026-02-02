/**
 * Price Service - COMPLETE VERSION
 *
 * Copy this ENTIRE file and replace your:
 * frontend/src/services/priceService.js
 */

const COINGECKO_IDS = {
  BTC: 'bitcoin',
  ETH: 'ethereum',
  USDT: 'tether',
  USDC: 'usd-coin',
  BNB: 'binancecoin',
  XRP: 'ripple',
  SOL: 'solana',
  ADA: 'cardano',
  DOGE: 'dogecoin',
  MATIC: 'matic-network',
  DOT: 'polkadot',
  DAI: 'dai',
  SHIB: 'shiba-inu',
  TRX: 'tron',
  AVAX: 'avalanche-2',
  LINK: 'chainlink',
  ATOM: 'cosmos',
  UNI: 'uniswap',
  LTC: 'litecoin',
  ETC: 'ethereum-classic',
  WETH: 'weth',
  WBTC: 'wrapped-bitcoin'
};

const COINGECKO_BASE_URL = 'https://api.coingecko.com/api/v3';

let priceCache = {};
let lastFetchTime = 0;
const CACHE_DURATION = 30000;

// ============================================================
// THESE ARE THE FUNCTIONS YOUR tradingStore.js NEEDS
// ============================================================

export const fetchRealTimePrices = async (symbols = ['BTC', 'ETH', 'USDT', 'SOL', 'XRP']) => {
  try {
    const ids = symbols
      .map(s => COINGECKO_IDS[s.toUpperCase()])
      .filter(Boolean)
      .join(',');

    if (!ids) {
      console.warn('No valid coin IDs found for symbols:', symbols);
      return {};
    }

    const response = await fetch(
      `${COINGECKO_BASE_URL}/simple/price?ids=${ids}&vs_currencies=usd&include_24hr_change=true&include_24hr_vol=true&include_market_cap=true`
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();

    const prices = {};
    for (const [symbol, geckoId] of Object.entries(COINGECKO_IDS)) {
      if (data[geckoId]) {
        prices[symbol] = {
          price: data[geckoId].usd || 0,
          usd: data[geckoId].usd || 0,
          change24h: data[geckoId].usd_24h_change || 0,
          volume24h: data[geckoId].usd_24h_vol || 0,
          marketCap: data[geckoId].usd_market_cap || 0
        };
      }
    }

    priceCache = { ...priceCache, ...prices };
    lastFetchTime = Date.now();

    return prices;
  } catch (error) {
    console.error('Failed to fetch real-time prices:', error);
    return priceCache;
  }
};

export const getPairPrice = async (pair) => {
  try {
    const [base, quote] = pair.split('/');

    if (!base) {
      console.warn('Invalid pair format:', pair);
      return 0;
    }

    if (quote === 'USDT' || quote === 'USD' || !quote) {
      const prices = await fetchRealTimePrices([base]);
      return prices[base]?.price || prices[base]?.usd || 0;
    }

    const prices = await fetchRealTimePrices([base, quote]);
    const basePrice = prices[base]?.price || prices[base]?.usd || 0;
    const quotePrice = prices[quote]?.price || prices[quote]?.usd || 0;

    if (quotePrice === 0) return 0;
    return basePrice / quotePrice;
  } catch (error) {
    console.error('Failed to get pair price:', error);
    return 0;
  }
};

// ============================================================
// FUNCTIONS FOR P2P TRANSFER & LIVE TICKER
// ============================================================

export const getPrices = async (symbols = ['BTC', 'ETH', 'USDT'], currency = 'usd') => {
  const now = Date.now();

  if (now - lastFetchTime < CACHE_DURATION && Object.keys(priceCache).length > 0) {
    const result = {};
    for (const symbol of symbols) {
      if (priceCache[symbol]) {
        result[symbol] = priceCache[symbol];
      }
    }
    if (Object.keys(result).length === symbols.length) {
      return result;
    }
  }

  try {
    const ids = symbols
      .map(s => COINGECKO_IDS[s.toUpperCase()])
      .filter(Boolean)
      .join(',');

    if (!ids) {
      console.warn('No valid coin IDs found');
      return priceCache;
    }

    const response = await fetch(
      `${COINGECKO_BASE_URL}/simple/price?ids=${ids}&vs_currencies=${currency}&include_24hr_change=true&include_24hr_vol=true&include_market_cap=true`
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();

    const prices = {};
    for (const [symbol, geckoId] of Object.entries(COINGECKO_IDS)) {
      if (data[geckoId]) {
        prices[symbol] = {
          price: data[geckoId][currency] || 0,
          usd: data[geckoId][currency] || 0,
          change24h: data[geckoId][`${currency}_24h_change`] || 0,
          volume24h: data[geckoId][`${currency}_24h_vol`] || 0,
          marketCap: data[geckoId][`${currency}_market_cap`] || 0
        };
      }
    }

    priceCache = { ...priceCache, ...prices };
    lastFetchTime = now;

    return prices;
  } catch (error) {
    console.error('Failed to fetch prices:', error);
    return priceCache;
  }
};

export const getPrice = async (symbol, currency = 'usd') => {
  const prices = await getPrices([symbol], currency);
  return prices[symbol.toUpperCase()]?.price || 0;
};

export const getCoinDetails = async (symbol) => {
  const geckoId = COINGECKO_IDS[symbol.toUpperCase()];
  if (!geckoId) {
    throw new Error(`Unknown coin symbol: ${symbol}`);
  }

  try {
    const response = await fetch(
      `${COINGECKO_BASE_URL}/coins/${geckoId}?localization=false&tickers=false&community_data=false&developer_data=false`
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();

    return {
      id: data.id,
      symbol: data.symbol.toUpperCase(),
      name: data.name,
      image: data.image?.large || data.image?.small,
      currentPrice: data.market_data?.current_price?.usd || 0,
      marketCap: data.market_data?.market_cap?.usd || 0,
      marketCapRank: data.market_cap_rank,
      totalVolume: data.market_data?.total_volume?.usd || 0,
      high24h: data.market_data?.high_24h?.usd || 0,
      low24h: data.market_data?.low_24h?.usd || 0,
      priceChange24h: data.market_data?.price_change_24h || 0,
      priceChangePercentage24h: data.market_data?.price_change_percentage_24h || 0,
      circulatingSupply: data.market_data?.circulating_supply || 0,
      totalSupply: data.market_data?.total_supply || 0,
      ath: data.market_data?.ath?.usd || 0,
      athDate: data.market_data?.ath_date?.usd,
      atl: data.market_data?.atl?.usd || 0,
      atlDate: data.market_data?.atl_date?.usd,
      description: data.description?.en || ''
    };
  } catch (error) {
    console.error('Failed to fetch coin details:', error);
    throw error;
  }
};

export const getHistoricalPrices = async (symbol, days = 7, currency = 'usd') => {
  const geckoId = COINGECKO_IDS[symbol.toUpperCase()];
  if (!geckoId) {
    throw new Error(`Unknown coin symbol: ${symbol}`);
  }

  try {
    const response = await fetch(
      `${COINGECKO_BASE_URL}/coins/${geckoId}/market_chart?vs_currency=${currency}&days=${days}`
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();

    return {
      prices: data.prices || [],
      marketCaps: data.market_caps || [],
      volumes: data.total_volumes || []
    };
  } catch (error) {
    console.error('Failed to fetch historical prices:', error);
    throw error;
  }
};

export const getTrendingCoins = async () => {
  try {
    const response = await fetch(`${COINGECKO_BASE_URL}/search/trending`);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();

    return data.coins?.map(item => ({
      id: item.item.id,
      symbol: item.item.symbol.toUpperCase(),
      name: item.item.name,
      marketCapRank: item.item.market_cap_rank,
      image: item.item.small,
      score: item.item.score
    })) || [];
  } catch (error) {
    console.error('Failed to fetch trending coins:', error);
    return [];
  }
};

export const subscribeToPrices = (symbols, callback, interval = 30000) => {
  let isActive = true;

  const fetchPricesLoop = async () => {
    if (!isActive) return;

    try {
      const prices = await getPrices(symbols);
      if (isActive) {
        callback(prices);
      }
    } catch (error) {
      console.error('Price subscription error:', error);
    }
  };

  fetchPricesLoop();
  const intervalId = setInterval(fetchPricesLoop, interval);

  return () => {
    isActive = false;
    clearInterval(intervalId);
  };
};

// ============================================================
// FORMATTING UTILITIES
// ============================================================

export const formatPrice = (price, currency = 'USD') => {
  if (price === undefined || price === null) return '$0.00';

  const options = {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: price < 1 ? 6 : 2
  };

  return new Intl.NumberFormat('en-US', options).format(price);
};

export const formatPercentage = (value) => {
  if (value === undefined || value === null) return '0.00%';
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}%`;
};

export const formatLargeNumber = (value) => {
  if (value === undefined || value === null) return '0';

  if (value >= 1e12) {
    return `$${(value / 1e12).toFixed(2)}T`;
  } else if (value >= 1e9) {
    return `$${(value / 1e9).toFixed(2)}B`;
  } else if (value >= 1e6) {
    return `$${(value / 1e6).toFixed(2)}M`;
  } else if (value >= 1e3) {
    return `$${(value / 1e3).toFixed(2)}K`;
  }
  return `$${value.toFixed(2)}`;
};

// ============================================================
// DEFAULT EXPORT
// ============================================================

export default {
  fetchRealTimePrices,
  getPairPrice,
  getPrices,
  getPrice,
  getCoinDetails,
  getHistoricalPrices,
  getTrendingCoins,
  subscribeToPrices,
  formatPrice,
  formatPercentage,
  formatLargeNumber,
  COINGECKO_IDS
};