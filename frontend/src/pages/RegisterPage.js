import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import WalletConnectButton from '../components/Auth/WalletConnectButton';
import toast from 'react-hot-toast';

const RegisterPage = () => {
  const navigate = useNavigate();
  const { register, isLoading, error, clearError } = useAuthStore();

  const [formData, setFormData] = useState({
    email: '',
    password: '',
    passwordConfirm: '',
  });

  const handleChange = (e) => {
    clearError();
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (formData.password !== formData.passwordConfirm) {
      toast.error('Passwords do not match');
      return;
    }

    if (formData.password.length < 10) {
      toast.error('Password must be at least 10 characters');
      return;
    }

    const result = await register(
      formData.email,
      formData.password,
      formData.passwordConfirm
    );

    if (result.success) {
      toast.success('Account created successfully!');
      navigate('/trade');
    } else {
      toast.error(result.error);
    }
  };

  const handleWalletSuccess = (result) => {
    if (result.isNewUser) {
      toast.success('Account created with wallet!');
    }
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
            Create Account
          </h1>
          <p className="text-exchange-muted mt-2">
            Start trading in minutes
          </p>
        </div>

        {/* Register Form */}
        <div className="card p-6">
          {/* Wallet Signup */}
          <div className="mb-6">
            <WalletConnectButton onSuccess={handleWalletSuccess} mode="signup" />
          </div>

          {/* Divider */}
          <div className="relative mb-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-exchange-border"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-4 bg-exchange-card text-exchange-muted">or sign up with email</span>
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
                placeholder="At least 10 characters"
                required
                minLength={10}
              />
            </div>

            {/* Confirm Password */}
            <div>
              <label className="block text-sm text-exchange-muted mb-2">
                Confirm Password
              </label>
              <input
                type="password"
                name="passwordConfirm"
                value={formData.passwordConfirm}
                onChange={handleChange}
                className="input"
                placeholder="Confirm your password"
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
              {isLoading ? 'Creating account...' : 'Create Account'}
            </button>
          </form>

          {/* Login link */}
          <div className="mt-6 text-center text-exchange-muted">
            Already have an account?{' '}
            <Link to="/login" className="text-primary-400 hover:text-primary-300">
              Sign in
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RegisterPage;