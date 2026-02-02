import React, { useState, useEffect } from 'react';
import { useAuthStore } from '../stores/authStore';
import { walletAPI } from '../services/api';
import { QRCodeSVG } from 'qrcode.react';
import {
  PaperAirplaneIcon,
  QrCodeIcon,
  MagnifyingGlassIcon,
  CheckCircleIcon,
  XCircleIcon,
} from '@heroicons/react/24/outline';

const TransferPage = () => {
  const { user } = useAuthStore();
  const [activeTab, setActiveTab] = useState('send');
  const [balances, setBalances] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [selectedRecipient, setSelectedRecipient] = useState(null);
  const [transferResult, setTransferResult] = useState(null);

  // Form state
  const [formData, setFormData] = useState({
    recipient_email: '',
    currency: 'USDT',
    amount: '',
    note: '',
  });

  // Fetch balances
  useEffect(() => {
    fetchBalances();
  }, []);

  const fetchBalances = async () => {
    try {
      const response = await walletAPI.getBalances();
      const balanceList = response.data.results || response.data || [];
      setBalances(balanceList);
    } catch (error) {
      console.error('Error fetching balances:', error);
    }
  };

  // Search users
  useEffect(() => {
    const searchUsers = async () => {
      if (searchQuery.length < 3) {
        setSearchResults([]);
        return;
      }
      try {
        const response = await fetch(
          `${process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1'}/wallets/transfer/search/?q=${searchQuery}`,
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
            },
          }
        );
        const data = await response.json();
        setSearchResults(data.users || []);
      } catch (error) {
        console.error('Error searching users:', error);
      }
    };

    const debounce = setTimeout(searchUsers, 300);
    return () => clearTimeout(debounce);
  }, [searchQuery]);

  const handleSelectRecipient = (recipient) => {
    setSelectedRecipient(recipient);
    setFormData({ ...formData, recipient_email: recipient.email });
    setSearchQuery('');
    setSearchResults([]);
  };

  const handleTransfer = async (e) => {
    e.preventDefault();
    setLoading(true);
    setTransferResult(null);

    try {
      const response = await fetch(
        `${process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1'}/wallets/transfer/`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          },
          body: JSON.stringify(formData),
        }
      );

      const data = await response.json();

      if (response.ok) {
        setTransferResult({ success: true, message: data.message, transaction: data.transaction });
        setFormData({ ...formData, amount: '', note: '' });
        setSelectedRecipient(null);
        fetchBalances(); // Refresh balances
      } else {
        setTransferResult({ success: false, message: data.error });
      }
    } catch (error) {
      setTransferResult({ success: false, message: 'Transfer failed. Please try again.' });
    } finally {
      setLoading(false);
    }
  };

  const getBalance = (symbol) => {
    const balance = balances.find(b => b.currency_symbol === symbol || b.currency?.symbol === symbol);
    return balance?.available || '0';
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-exchange-text mb-6">P2P Transfer</h1>

      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setActiveTab('send')}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            activeTab === 'send'
              ? 'bg-primary-500 text-white'
              : 'bg-exchange-card text-exchange-muted hover:text-exchange-text'
          }`}
        >
          <PaperAirplaneIcon className="w-5 h-5 inline mr-2" />
          Send
        </button>
        <button
          onClick={() => setActiveTab('receive')}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            activeTab === 'receive'
              ? 'bg-primary-500 text-white'
              : 'bg-exchange-card text-exchange-muted hover:text-exchange-text'
          }`}
        >
          <QrCodeIcon className="w-5 h-5 inline mr-2" />
          Receive
        </button>
      </div>

      {/* Transfer Result */}
      {transferResult && (
        <div className={`mb-6 p-4 rounded-lg flex items-start gap-3 ${
          transferResult.success ? 'bg-success/10 border border-success/30' : 'bg-danger/10 border border-danger/30'
        }`}>
          {transferResult.success ? (
            <CheckCircleIcon className="w-6 h-6 text-success flex-shrink-0" />
          ) : (
            <XCircleIcon className="w-6 h-6 text-danger flex-shrink-0" />
          )}
          <div>
            <p className={transferResult.success ? 'text-success' : 'text-danger'}>
              {transferResult.message}
            </p>
            {transferResult.transaction && (
              <p className="text-sm text-exchange-muted mt-1">
                Transaction ID: {transferResult.transaction.id}
              </p>
            )}
          </div>
        </div>
      )}

      {activeTab === 'send' ? (
        /* Send Tab */
        <div className="card p-6">
          <form onSubmit={handleTransfer} className="space-y-6">
            {/* Recipient Search */}
            <div>
              <label className="block text-sm font-medium text-exchange-muted mb-2">
                Recipient
              </label>
              {selectedRecipient ? (
                <div className="flex items-center justify-between p-3 bg-exchange-bg rounded-lg">
                  <div>
                    <p className="text-exchange-text font-medium">{selectedRecipient.display_name}</p>
                    <p className="text-sm text-exchange-muted">{selectedRecipient.email}</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      setSelectedRecipient(null);
                      setFormData({ ...formData, recipient_email: '' });
                    }}
                    className="text-danger hover:text-danger/80"
                  >
                    <XCircleIcon className="w-5 h-5" />
                  </button>
                </div>
              ) : (
                <div className="relative">
                  <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-exchange-muted" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search by email..."
                    className="input pl-10 w-full"
                  />
                  {searchResults.length > 0 && (
                    <div className="absolute top-full left-0 right-0 mt-1 bg-exchange-card border border-exchange-border rounded-lg shadow-lg z-10 max-h-48 overflow-y-auto">
                      {searchResults.map((user) => (
                        <button
                          key={user.email}
                          type="button"
                          onClick={() => handleSelectRecipient(user)}
                          className="w-full p-3 text-left hover:bg-exchange-bg transition-colors"
                        >
                          <p className="text-exchange-text">{user.display_name}</p>
                          <p className="text-sm text-exchange-muted">{user.email}</p>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )}
              <p className="text-xs text-exchange-muted mt-1">
                Or enter email directly:
              </p>
              <input
                type="email"
                value={formData.recipient_email}
                onChange={(e) => setFormData({ ...formData, recipient_email: e.target.value })}
                placeholder="recipient@email.com"
                className="input w-full mt-2"
                required
              />
            </div>

            {/* Currency Selection */}
            <div>
              <label className="block text-sm font-medium text-exchange-muted mb-2">
                Currency
              </label>
              <select
                value={formData.currency}
                onChange={(e) => setFormData({ ...formData, currency: e.target.value })}
                className="input w-full"
              >
                <option value="BTC">BTC - Bitcoin</option>
                <option value="ETH">ETH - Ethereum</option>
                <option value="USDT">USDT - Tether</option>
                <option value="SOL">SOL - Solana</option>
                <option value="XRP">XRP - Ripple</option>
                <option value="DOGE">DOGE - Dogecoin</option>
                <option value="ADA">ADA - Cardano</option>
                <option value="BNB">BNB - BNB</option>
                <option value="AVAX">AVAX - Avalanche</option>
                <option value="MATIC">MATIC - Polygon</option>
                <option value="DOT">DOT - Polkadot</option>
                <option value="LINK">LINK - Chainlink</option>
              </select>
              <p className="text-sm text-exchange-muted mt-1">
                Available: {getBalance(formData.currency)} {formData.currency}
              </p>
            </div>

            {/* Amount */}
            <div>
              <label className="block text-sm font-medium text-exchange-muted mb-2">
                Amount
              </label>
              <input
                type="number"
                step="any"
                value={formData.amount}
                onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                placeholder="0.00"
                className="input w-full"
                required
              />
              <button
                type="button"
                onClick={() => setFormData({ ...formData, amount: getBalance(formData.currency) })}
                className="text-sm text-primary-400 hover:text-primary-300 mt-1"
              >
                Use Max
              </button>
            </div>

            {/* Note */}
            <div>
              <label className="block text-sm font-medium text-exchange-muted mb-2">
                Note (optional)
              </label>
              <input
                type="text"
                value={formData.note}
                onChange={(e) => setFormData({ ...formData, note: e.target.value })}
                placeholder="What's this for?"
                className="input w-full"
                maxLength={100}
              />
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading || !formData.recipient_email || !formData.amount}
              className="btn-primary w-full py-3 disabled:opacity-50"
            >
              {loading ? 'Processing...' : `Send ${formData.amount || '0'} ${formData.currency}`}
            </button>
          </form>
        </div>
      ) : (
        /* Receive Tab */
        <div className="card p-6 text-center">
          <h2 className="text-lg font-medium text-exchange-text mb-4">Your Receive Address</h2>
          
          {/* QR Code */}
          <div className="bg-white p-4 rounded-lg inline-block mb-4">
            <QRCodeSVG
              value={JSON.stringify({
                platform: 'ToKeNlY',
                email: user?.email,
                type: 'transfer',
              })}
              size={200}
              level="H"
            />
          </div>

          {/* Email Display */}
          <div className="bg-exchange-bg rounded-lg p-4 mb-4">
            <p className="text-sm text-exchange-muted mb-1">Share this email to receive crypto:</p>
            <p className="text-lg font-mono text-exchange-text break-all">{user?.email}</p>
          </div>

          {/* Copy Button */}
          <button
            onClick={() => {
              navigator.clipboard.writeText(user?.email || '');
              alert('Email copied to clipboard!');
            }}
            className="btn-secondary"
          >
            Copy Email Address
          </button>

          <p className="text-sm text-exchange-muted mt-4">
            Other users can send you crypto by entering your email address
          </p>
        </div>
      )}
    </div>
  );
};

export default TransferPage;
