import axios from 'axios';

// API Base URL - MUST include /api/v1
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

console.log('API_BASE_URL:', API_BASE_URL);

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: false,
});

// Request interceptor - add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    console.log('API Request:', config.method.toUpperCase(), config.baseURL + config.url);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor - handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    console.log('API Error:', error.response?.status, error.response?.data);

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/auth/token/refresh/`, {
            refresh: refreshToken,
          });

          const { access } = response.data;
          localStorage.setItem('access_token', access);

          originalRequest.headers.Authorization = `Bearer ${access}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);

// =============================================================================
// AUTH API
// =============================================================================

export const authAPI = {
  register: (data) => api.post('/auth/register/', data),
  login: (data) => api.post('/auth/login/', data),
  logout: (data) => api.post('/auth/logout/', data),
  getProfile: () => api.get('/auth/profile/'),
  updateProfile: (data) => api.patch('/auth/profile/', data),
  changePassword: (data) => api.post('/auth/change-password/', data),

  // Wallet auth
  getWalletNonce: (walletAddress) => api.post('/auth/wallet/nonce/', { wallet_address: walletAddress }),
  verifyWallet: (data) => api.post('/auth/wallet/verify/', data),
  connectWallet: (data) => api.post('/auth/wallet/connect/', data),
  disconnectWallet: (walletId) => api.delete(`/auth/wallet/${walletId}/disconnect/`),
  getWallets: () => api.get('/auth/wallets/'),
};

// =============================================================================
// WALLET API
// =============================================================================

export const walletAPI = {
  getCurrencies: () => api.get('/wallets/currencies/'),
  getBalances: () => api.get('/wallets/balances/'),
  getBalance: (symbol) => api.get(`/wallets/balances/${symbol}/`),
  getLedger: (params) => api.get('/wallets/ledger/', { params }),

  getDepositAddress: (symbol) => api.get(`/wallets/deposit-address/${symbol}/`),
  getDeposits: () => api.get('/wallets/deposits/'),

  getWithdrawals: () => api.get('/wallets/withdrawals/'),
  createWithdrawal: (data) => api.post('/wallets/withdrawals/create/', data),
  p2pTransfer: (data) => api.post('/wallets/p2p-transfer/', data),
  getTransfers: () => api.get('/wallets/transfers/'),
  getTransferById: (id) => api.get(`/wallets/transfers/${id}/`),
  };

// =============================================================================
// TRADING API
// =============================================================================

export const tradingAPI = {
  getTradingPairs: () => api.get('/trading/pairs/'),
  getTradingPair: (symbol) => api.get(`/trading/pairs/${symbol}/`),
  getOrderBook: (symbol, depth = 50) => api.get(`/trading/orderbook/${symbol}/`, { params: { depth } }),
  getRecentTrades: (symbol) => api.get(`/trading/trades/${symbol}/`),
  getTicker: (symbol) => api.get(`/trading/ticker/${symbol}/`),
  getAllTickers: () => api.get('/trading/ticker/'),

  createOrder: (data) => api.post('/trading/orders/create/', data),
  cancelOrder: (orderId) => api.post(`/trading/orders/${orderId}/cancel/`),
  getOrders: (params) => api.get('/trading/orders/', { params }),
  getOpenOrders: () => api.get('/trading/orders/open/'),

  getUserTrades: (params) => api.get('/trading/user/trades/', { params }),
};

export default api;
