import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import WalletConnectButton from '../components/Auth/WalletConnectButton';
import toast from 'react-hot-toast';

const LoginPage = () => {
  const navigate = useNavigate();
  const { login, isLoading, error, clearError } = useAuthStore();

  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });

  const handleChange = (e) => {
    clearError();
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    const result = await login(formData.email, formData.password);

    if (result.success) {
      toast.success('Login successful!');
      navigate('/trade');
    } else {
      toast.error(result.error);
    }
  };

  const handleWalletSuccess = () => {
    navigate('/trade');
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="max-w-md w-full">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 mb-4">
            <div className="w-12 h-12 bg-primary-500 rounded-xl flex items-center justify-center">
              <span className="text-white text-2xl font-bold">TK</span>
            </div>
          </div>
          <h1 className="text-3xl font-bold text-exchange-text">
            Welcome Back
          </h1>
          <p className="text-exchange-muted mt-2">
            Sign in to your account
          </p>
        </div>

        {/* Login Form */}
        <div className="card p-6">
          {/* Wallet Login */}
          <div className="mb-6">
            <WalletConnectButton onSuccess={handleWalletSuccess} mode="login" />
          </div>

          {/* Divider */}
          <div className="relative mb-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-exchange-border"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-4 bg-exchange-card text-exchange-muted">or continue with email</span>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Email */}
            <div>
              <label className="block text-sm text-exchange-muted mb-2">
                Email
              </label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                className="input"
                placeholder="Enter your email"
                required
              />
            </div>

            {/* Password */}
            <div>
              <label className="block text-sm text-exchange-muted mb-2">
                Password
              </label>
              <input
                type="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                className="input"
                placeholder="Enter your password"
                required
              />
            </div>

            {/* Error message */}
            {error && (
              <div className="text-danger text-sm">
                {error}
              </div>
            )}

            {/* Submit */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full btn btn-primary py-3"
            >
              {isLoading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          {/* Register link */}
          <div className="mt-6 text-center text-exchange-muted">
            Don't have an account?{' '}
            <Link to="/register" className="text-primary-400 hover:text-primary-300">
              Sign up
            </Link>
          </div>
        </div>

        {/* Demo notice */}
        <div className="mt-6 text-center text-sm text-exchange-muted">
          <p>🔧 Demo Mode - Use email or MetaMask to login</p>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;