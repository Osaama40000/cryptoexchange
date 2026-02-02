import TransferPage from './pages/TransferPage';
import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './stores/authStore';
import { PriceProvider } from './contexts/PriceContext';

// Layout
import Layout from './components/Layout/Layout';
import DemoBanner from './components/Layout/DemoBanner';

// Pages
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import TradingPage from './pages/TradingPage';
import WalletPage from './pages/WalletPage';
import OrdersPage from './pages/OrdersPage';
import SettingsPage from './pages/SettingsPage';
import AdminPage from './pages/AdminPage';
import SecurityPage from './pages/SecurityPage';
import MarketPage from './pages/MarketPage';

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated } = useAuthStore();
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return children;
};

// Public Route Component (redirect if logged in)
const PublicRoute = ({ children }) => {
  const { isAuthenticated } = useAuthStore();
  if (isAuthenticated) {
    return <Navigate to="/trade" replace />;
  }
  return children;
};

// Admin Route Component
const AdminRoute = ({ children }) => {
  const { isAuthenticated, user } = useAuthStore();
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  if (!user?.is_staff) {
    return <Navigate to="/trade" replace />;
  }
  return children;
};

function App() {
  return (
    <PriceProvider>
      <div className="min-h-screen bg-exchange-bg">
        <DemoBanner />
        <Routes>
          {/* Public Routes */}
          <Route path="/login" element={
            <PublicRoute>
              <LoginPage />
            </PublicRoute>
          } />
          <Route path="/register" element={
            <PublicRoute>
              <RegisterPage />
            </PublicRoute>
          } />

          {/* Protected Routes */}
          <Route path="/" element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }>
            <Route index element={<Navigate to="/trade" replace />} />
            <Route path="trade" element={<TradingPage />} />
            <Route path="trade/:symbol" element={<TradingPage />} />
            <Route path="market" element={<MarketPage />} />
            <Route path="transfer" element={<TransferPage />} />
            <Route path="wallet" element={<WalletPage />} />
            <Route path="orders" element={<OrdersPage />} />
            <Route path="settings" element={<SettingsPage />} />
            <Route path="security" element={<SecurityPage />} />
            <Route path="admin" element={
              <AdminRoute>
                <AdminPage />
              </AdminRoute>
            } />
          </Route>

          {/* Catch all */}
          <Route path="*" element={<Navigate to="/trade" replace />} />
        </Routes>
      </div>
    </PriceProvider>
  );
}

export default App;
