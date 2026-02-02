/**
 * P2P Crypto Transfer Component
 *
 * This component allows users to:
 * 1. Connect their MetaMask wallet
 * 2. View their real ETH and token balances
 * 3. Send crypto to any wallet address
 * 4. View transaction history
 *
 * ADD THIS FILE TO: frontend/src/components/P2PTransfer.jsx
 */

import React, { useState, useEffect, useCallback } from 'react';
import { ethers } from 'ethers';
import toast from 'react-hot-toast';

// ERC-20 Token ABI (minimal for transfers)
const ERC20_ABI = [
  'function balanceOf(address owner) view returns (uint256)',
  'function decimals() view returns (uint8)',
  'function symbol() view returns (string)',
  'function transfer(address to, uint256 amount) returns (bool)',
  'function name() view returns (string)'
];

// Common tokens on Ethereum Mainnet (add more as needed)
const SUPPORTED_TOKENS = {
  mainnet: {
    USDT: '0xdAC17F958D2ee523a2206206994597C13D831ec7',
    USDC: '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
    DAI: '0x6B175474E89094C44Da98b954EescdeCB5f560B2f3E',
  },
  sepolia: {
    // Sepolia testnet tokens (for testing)
    USDT: '0x7169D38820dfd117C3FA1f22a697dBA58d90BA06',
  }
};

// Network configurations
const NETWORKS = {
  1: { name: 'Ethereum Mainnet', symbol: 'ETH', explorer: 'https://etherscan.io' },
  11155111: { name: 'Sepolia Testnet', symbol: 'SepoliaETH', explorer: 'https://sepolia.etherscan.io' },
  137: { name: 'Polygon', symbol: 'MATIC', explorer: 'https://polygonscan.com' },
  56: { name: 'BSC', symbol: 'BNB', explorer: 'https://bscscan.com' },
};

const P2PTransfer = () => {
  // Wallet state
  const [isConnected, setIsConnected] = useState(false);
  const [walletAddress, setWalletAddress] = useState('');
  const [chainId, setChainId] = useState(null);
  const [provider, setProvider] = useState(null);
  const [signer, setSigner] = useState(null);

  // Balance state
  const [ethBalance, setEthBalance] = useState('0');
  const [tokenBalances, setTokenBalances] = useState({});
  const [isLoadingBalances, setIsLoadingBalances] = useState(false);

  // Transfer state
  const [recipientAddress, setRecipientAddress] = useState('');
  const [transferAmount, setTransferAmount] = useState('');
  const [selectedAsset, setSelectedAsset] = useState('ETH');
  const [isTransferring, setIsTransferring] = useState(false);
  const [gasEstimate, setGasEstimate] = useState(null);

  // Transaction history
  const [transactions, setTransactions] = useState([]);

  // UI state
  const [activeTab, setActiveTab] = useState('send'); // 'send' | 'receive' | 'history'

  // Check if MetaMask is installed
  const isMetaMaskInstalled = typeof window !== 'undefined' && window.ethereum;

  // Connect wallet
  const connectWallet = async () => {
    if (!isMetaMaskInstalled) {
      toast.error('Please install MetaMask to use this feature');
      window.open('https://metamask.io/download/', '_blank');
      return;
    }

    try {
      const accounts = await window.ethereum.request({
        method: 'eth_requestAccounts'
      });

      if (accounts.length > 0) {
        const web3Provider = new ethers.BrowserProvider(window.ethereum);
        const web3Signer = await web3Provider.getSigner();
        const network = await web3Provider.getNetwork();

        setProvider(web3Provider);
        setSigner(web3Signer);
        setWalletAddress(accounts[0]);
        setChainId(Number(network.chainId));
        setIsConnected(true);

        toast.success('Wallet connected successfully!');

        // Load balances after connection
        await loadBalances(accounts[0], web3Provider, Number(network.chainId));
      }
    } catch (error) {
      console.error('Connection error:', error);
      if (error.code === 4001) {
        toast.error('Connection rejected by user');
      } else {
        toast.error('Failed to connect wallet');
      }
    }
  };

  // Disconnect wallet
  const disconnectWallet = () => {
    setIsConnected(false);
    setWalletAddress('');
    setProvider(null);
    setSigner(null);
    setEthBalance('0');
    setTokenBalances({});
    toast.success('Wallet disconnected');
  };

  // Load balances
  const loadBalances = async (address, providerInstance, network) => {
    if (!address || !providerInstance) return;

    setIsLoadingBalances(true);
    try {
      // Get ETH balance
      const balance = await providerInstance.getBalance(address);
      setEthBalance(ethers.formatEther(balance));

      // Get token balances based on network
      const networkTokens = network === 1 ? SUPPORTED_TOKENS.mainnet : SUPPORTED_TOKENS.sepolia;
      const balances = {};

      for (const [symbol, tokenAddress] of Object.entries(networkTokens)) {
        try {
          const tokenContract = new ethers.Contract(tokenAddress, ERC20_ABI, providerInstance);
          const tokenBalance = await tokenContract.balanceOf(address);
          const decimals = await tokenContract.decimals();
          balances[symbol] = ethers.formatUnits(tokenBalance, decimals);
        } catch (err) {
          console.log(`Could not load ${symbol} balance:`, err.message);
          balances[symbol] = '0';
        }
      }

      setTokenBalances(balances);
    } catch (error) {
      console.error('Error loading balances:', error);
      toast.error('Failed to load balances');
    } finally {
      setIsLoadingBalances(false);
    }
  };

  // Estimate gas for transfer
  const estimateGas = useCallback(async () => {
    if (!signer || !recipientAddress || !transferAmount || !ethers.isAddress(recipientAddress)) {
      setGasEstimate(null);
      return;
    }

    try {
      const amountWei = ethers.parseEther(transferAmount);

      if (selectedAsset === 'ETH') {
        const gasLimit = await provider.estimateGas({
          to: recipientAddress,
          value: amountWei,
        });
        const feeData = await provider.getFeeData();
        const gasCost = gasLimit * feeData.gasPrice;
        setGasEstimate(ethers.formatEther(gasCost));
      } else {
        // Token transfer gas estimation
        const networkTokens = chainId === 1 ? SUPPORTED_TOKENS.mainnet : SUPPORTED_TOKENS.sepolia;
        const tokenAddress = networkTokens[selectedAsset];
        if (tokenAddress) {
          const tokenContract = new ethers.Contract(tokenAddress, ERC20_ABI, signer);
          const decimals = await tokenContract.decimals();
          const tokenAmount = ethers.parseUnits(transferAmount, decimals);
          const gasLimit = await tokenContract.transfer.estimateGas(recipientAddress, tokenAmount);
          const feeData = await provider.getFeeData();
          const gasCost = gasLimit * feeData.gasPrice;
          setGasEstimate(ethers.formatEther(gasCost));
        }
      }
    } catch (error) {
      console.log('Gas estimation failed:', error.message);
      setGasEstimate(null);
    }
  }, [signer, provider, recipientAddress, transferAmount, selectedAsset, chainId]);

  // Effect to estimate gas when inputs change
  useEffect(() => {
    const timer = setTimeout(() => {
      estimateGas();
    }, 500);
    return () => clearTimeout(timer);
  }, [estimateGas]);

  // Send ETH
  const sendETH = async () => {
    if (!signer || !recipientAddress || !transferAmount) {
      toast.error('Please fill in all fields');
      return;
    }

    if (!ethers.isAddress(recipientAddress)) {
      toast.error('Invalid recipient address');
      return;
    }

    const amount = parseFloat(transferAmount);
    const balance = parseFloat(ethBalance);

    if (amount <= 0) {
      toast.error('Amount must be greater than 0');
      return;
    }

    if (amount > balance) {
      toast.error('Insufficient ETH balance');
      return;
    }

    setIsTransferring(true);
    const toastId = toast.loading('Sending ETH...');

    try {
      const tx = await signer.sendTransaction({
        to: recipientAddress,
        value: ethers.parseEther(transferAmount),
      });

      toast.loading('Transaction submitted. Waiting for confirmation...', { id: toastId });

      const receipt = await tx.wait();

      // Add to transaction history
      const newTx = {
        hash: receipt.hash,
        type: 'send',
        asset: 'ETH',
        amount: transferAmount,
        to: recipientAddress,
        timestamp: new Date().toISOString(),
        status: 'confirmed',
      };
      setTransactions(prev => [newTx, ...prev]);

      toast.success(`Successfully sent ${transferAmount} ETH!`, { id: toastId });

      // Clear form
      setRecipientAddress('');
      setTransferAmount('');

      // Reload balances
      await loadBalances(walletAddress, provider, chainId);
    } catch (error) {
      console.error('Transfer error:', error);
      if (error.code === 'ACTION_REJECTED' || error.code === 4001) {
        toast.error('Transaction rejected by user', { id: toastId });
      } else if (error.message.includes('insufficient funds')) {
        toast.error('Insufficient funds for gas', { id: toastId });
      } else {
        toast.error(`Transfer failed: ${error.message}`, { id: toastId });
      }
    } finally {
      setIsTransferring(false);
    }
  };

  // Send Token
  const sendToken = async () => {
    if (!signer || !recipientAddress || !transferAmount) {
      toast.error('Please fill in all fields');
      return;
    }

    if (!ethers.isAddress(recipientAddress)) {
      toast.error('Invalid recipient address');
      return;
    }

    const networkTokens = chainId === 1 ? SUPPORTED_TOKENS.mainnet : SUPPORTED_TOKENS.sepolia;
    const tokenAddress = networkTokens[selectedAsset];

    if (!tokenAddress) {
      toast.error(`${selectedAsset} not supported on this network`);
      return;
    }

    const amount = parseFloat(transferAmount);
    const balance = parseFloat(tokenBalances[selectedAsset] || '0');

    if (amount <= 0) {
      toast.error('Amount must be greater than 0');
      return;
    }

    if (amount > balance) {
      toast.error(`Insufficient ${selectedAsset} balance`);
      return;
    }

    setIsTransferring(true);
    const toastId = toast.loading(`Sending ${selectedAsset}...`);

    try {
      const tokenContract = new ethers.Contract(tokenAddress, ERC20_ABI, signer);
      const decimals = await tokenContract.decimals();
      const tokenAmount = ethers.parseUnits(transferAmount, decimals);

      const tx = await tokenContract.transfer(recipientAddress, tokenAmount);

      toast.loading('Transaction submitted. Waiting for confirmation...', { id: toastId });

      const receipt = await tx.wait();

      // Add to transaction history
      const newTx = {
        hash: receipt.hash,
        type: 'send',
        asset: selectedAsset,
        amount: transferAmount,
        to: recipientAddress,
        timestamp: new Date().toISOString(),
        status: 'confirmed',
      };
      setTransactions(prev => [newTx, ...prev]);

      toast.success(`Successfully sent ${transferAmount} ${selectedAsset}!`, { id: toastId });

      // Clear form
      setRecipientAddress('');
      setTransferAmount('');

      // Reload balances
      await loadBalances(walletAddress, provider, chainId);
    } catch (error) {
      console.error('Token transfer error:', error);
      if (error.code === 'ACTION_REJECTED' || error.code === 4001) {
        toast.error('Transaction rejected by user', { id: toastId });
      } else {
        toast.error(`Transfer failed: ${error.message}`, { id: toastId });
      }
    } finally {
      setIsTransferring(false);
    }
  };

  // Handle transfer
  const handleTransfer = () => {
    if (selectedAsset === 'ETH') {
      sendETH();
    } else {
      sendToken();
    }
  };

  // Set max amount
  const setMaxAmount = () => {
    if (selectedAsset === 'ETH') {
      // Leave some for gas
      const maxEth = Math.max(0, parseFloat(ethBalance) - 0.005);
      setTransferAmount(maxEth.toFixed(6));
    } else {
      setTransferAmount(tokenBalances[selectedAsset] || '0');
    }
  };

  // Copy address to clipboard
  const copyAddress = () => {
    navigator.clipboard.writeText(walletAddress);
    toast.success('Address copied to clipboard!');
  };

  // Listen for account/network changes
  useEffect(() => {
    if (!isMetaMaskInstalled) return;

    const handleAccountsChanged = (accounts) => {
      if (accounts.length === 0) {
        disconnectWallet();
      } else if (accounts[0] !== walletAddress) {
        setWalletAddress(accounts[0]);
        if (provider && chainId) {
          loadBalances(accounts[0], provider, chainId);
        }
      }
    };

    const handleChainChanged = (newChainId) => {
      const chainIdNum = parseInt(newChainId, 16);
      setChainId(chainIdNum);
      if (walletAddress && provider) {
        loadBalances(walletAddress, provider, chainIdNum);
      }
    };

    window.ethereum.on('accountsChanged', handleAccountsChanged);
    window.ethereum.on('chainChanged', handleChainChanged);

    return () => {
      window.ethereum.removeListener('accountsChanged', handleAccountsChanged);
      window.ethereum.removeListener('chainChanged', handleChainChanged);
    };
  }, [isMetaMaskInstalled, walletAddress, provider, chainId]);

  // Check if already connected on mount
  useEffect(() => {
    const checkConnection = async () => {
      if (isMetaMaskInstalled) {
        try {
          const accounts = await window.ethereum.request({ method: 'eth_accounts' });
          if (accounts.length > 0) {
            const web3Provider = new ethers.BrowserProvider(window.ethereum);
            const web3Signer = await web3Provider.getSigner();
            const network = await web3Provider.getNetwork();

            setProvider(web3Provider);
            setSigner(web3Signer);
            setWalletAddress(accounts[0]);
            setChainId(Number(network.chainId));
            setIsConnected(true);

            await loadBalances(accounts[0], web3Provider, Number(network.chainId));
          }
        } catch (error) {
          console.log('Auto-connect check failed:', error);
        }
      }
    };

    checkConnection();
  }, [isMetaMaskInstalled]);

  // Get current network info
  const currentNetwork = NETWORKS[chainId] || { name: 'Unknown Network', symbol: 'ETH', explorer: '' };

  // Format address for display
  const formatAddress = (addr) => {
    if (!addr) return '';
    return `${addr.slice(0, 6)}...${addr.slice(-4)}`;
  };

  return (
    <div className="p2p-transfer-container">
      <style>{`
        .p2p-transfer-container {
          max-width: 480px;
          margin: 0 auto;
          font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        .wallet-card {
          background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
          border-radius: 20px;
          padding: 24px;
          color: white;
          margin-bottom: 20px;
          box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
        }

        .wallet-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
        }

        .wallet-status {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .status-dot {
          width: 10px;
          height: 10px;
          border-radius: 50%;
          background: #22c55e;
          animation: pulse 2s infinite;
        }

        .status-dot.disconnected {
          background: #ef4444;
          animation: none;
        }

        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }

        .network-badge {
          background: rgba(255, 255, 255, 0.1);
          padding: 6px 12px;
          border-radius: 20px;
          font-size: 12px;
          color: #94a3b8;
        }

        .wallet-address {
          background: rgba(255, 255, 255, 0.05);
          border-radius: 12px;
          padding: 16px;
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
        }

        .address-text {
          font-family: 'JetBrains Mono', monospace;
          font-size: 14px;
          color: #e2e8f0;
        }

        .copy-btn {
          background: rgba(99, 102, 241, 0.2);
          border: none;
          color: #818cf8;
          padding: 8px 12px;
          border-radius: 8px;
          cursor: pointer;
          transition: all 0.2s;
        }

        .copy-btn:hover {
          background: rgba(99, 102, 241, 0.3);
        }

        .balance-grid {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 12px;
        }

        .balance-item {
          background: rgba(255, 255, 255, 0.05);
          border-radius: 12px;
          padding: 16px;
        }

        .balance-label {
          font-size: 12px;
          color: #94a3b8;
          margin-bottom: 4px;
        }

        .balance-value {
          font-size: 20px;
          font-weight: 600;
          color: white;
        }

        .balance-value.loading {
          background: linear-gradient(90deg, #374151 25%, #4b5563 50%, #374151 75%);
          background-size: 200% 100%;
          animation: shimmer 1.5s infinite;
          border-radius: 4px;
          height: 28px;
          width: 80%;
        }

        @keyframes shimmer {
          0% { background-position: 200% 0; }
          100% { background-position: -200% 0; }
        }

        .connect-btn {
          width: 100%;
          background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
          border: none;
          color: white;
          padding: 16px;
          border-radius: 12px;
          font-size: 16px;
          font-weight: 600;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 10px;
          transition: all 0.3s;
        }

        .connect-btn:hover {
          transform: translateY(-2px);
          box-shadow: 0 10px 30px rgba(99, 102, 241, 0.4);
        }

        .connect-btn.disconnect {
          background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        }

        .transfer-card {
          background: #ffffff;
          border-radius: 20px;
          padding: 24px;
          box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        }

        .tabs {
          display: flex;
          background: #f1f5f9;
          border-radius: 12px;
          padding: 4px;
          margin-bottom: 24px;
        }

        .tab {
          flex: 1;
          padding: 12px;
          border: none;
          background: transparent;
          color: #64748b;
          font-weight: 500;
          cursor: pointer;
          border-radius: 10px;
          transition: all 0.2s;
        }

        .tab.active {
          background: white;
          color: #1e293b;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }

        .form-group {
          margin-bottom: 20px;
        }

        .form-label {
          display: block;
          font-size: 14px;
          font-weight: 500;
          color: #374151;
          margin-bottom: 8px;
        }

        .input-wrapper {
          position: relative;
        }

        .form-input {
          width: 100%;
          padding: 14px 16px;
          border: 2px solid #e5e7eb;
          border-radius: 12px;
          font-size: 16px;
          transition: all 0.2s;
          box-sizing: border-box;
        }

        .form-input:focus {
          outline: none;
          border-color: #6366f1;
          box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
        }

        .form-input.error {
          border-color: #ef4444;
        }

        .asset-selector {
          display: flex;
          gap: 8px;
          margin-bottom: 20px;
        }

        .asset-btn {
          flex: 1;
          padding: 12px;
          border: 2px solid #e5e7eb;
          background: white;
          border-radius: 12px;
          cursor: pointer;
          transition: all 0.2s;
          font-weight: 500;
        }

        .asset-btn.active {
          border-color: #6366f1;
          background: rgba(99, 102, 241, 0.05);
          color: #6366f1;
        }

        .asset-btn:hover:not(.active) {
          border-color: #c7d2fe;
        }

        .amount-row {
          display: flex;
          gap: 8px;
          align-items: center;
        }

        .max-btn {
          background: #f1f5f9;
          border: none;
          padding: 14px 16px;
          border-radius: 12px;
          color: #6366f1;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
        }

        .max-btn:hover {
          background: #e2e8f0;
        }

        .gas-estimate {
          background: #f8fafc;
          border-radius: 12px;
          padding: 12px 16px;
          margin-bottom: 20px;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .gas-label {
          color: #64748b;
          font-size: 14px;
        }

        .gas-value {
          color: #1e293b;
          font-weight: 500;
        }

        .send-btn {
          width: 100%;
          background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
          border: none;
          color: white;
          padding: 16px;
          border-radius: 12px;
          font-size: 16px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.3s;
        }

        .send-btn:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 10px 30px rgba(99, 102, 241, 0.4);
        }

        .send-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .receive-section {
          text-align: center;
          padding: 20px;
        }

        .qr-placeholder {
          width: 200px;
          height: 200px;
          background: #f1f5f9;
          border-radius: 16px;
          margin: 0 auto 20px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 48px;
        }

        .receive-address {
          background: #f8fafc;
          border-radius: 12px;
          padding: 16px;
          font-family: 'JetBrains Mono', monospace;
          font-size: 12px;
          word-break: break-all;
          color: #374151;
          margin-bottom: 16px;
        }

        .history-item {
          background: #f8fafc;
          border-radius: 12px;
          padding: 16px;
          margin-bottom: 12px;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .history-left {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .history-icon {
          width: 40px;
          height: 40px;
          border-radius: 10px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 18px;
        }

        .history-icon.send {
          background: #fef2f2;
        }

        .history-icon.receive {
          background: #f0fdf4;
        }

        .history-details h4 {
          margin: 0 0 4px 0;
          font-size: 14px;
          color: #1e293b;
        }

        .history-details p {
          margin: 0;
          font-size: 12px;
          color: #64748b;
        }

        .history-amount {
          text-align: right;
        }

        .history-amount .value {
          font-weight: 600;
          color: #1e293b;
        }

        .history-amount .status {
          font-size: 12px;
          color: #22c55e;
        }

        .tx-link {
          color: #6366f1;
          text-decoration: none;
          font-size: 12px;
        }

        .tx-link:hover {
          text-decoration: underline;
        }

        .empty-state {
          text-align: center;
          padding: 40px;
          color: #64748b;
        }

        .empty-state-icon {
          font-size: 48px;
          margin-bottom: 12px;
        }

        .not-connected-overlay {
          background: rgba(255, 255, 255, 0.9);
          border-radius: 20px;
          padding: 40px;
          text-align: center;
        }

        .not-connected-overlay h3 {
          margin: 0 0 12px 0;
          color: #1e293b;
        }

        .not-connected-overlay p {
          margin: 0 0 20px 0;
          color: #64748b;
        }
      `}</style>

      {/* Wallet Card */}
      <div className="wallet-card">
        <div className="wallet-header">
          <div className="wallet-status">
            <div className={`status-dot ${!isConnected ? 'disconnected' : ''}`}></div>
            <span>{isConnected ? 'Connected' : 'Disconnected'}</span>
          </div>
          {isConnected && chainId && (
            <div className="network-badge">{currentNetwork.name}</div>
          )}
        </div>

        {isConnected ? (
          <>
            <div className="wallet-address">
              <span className="address-text">{formatAddress(walletAddress)}</span>
              <button className="copy-btn" onClick={copyAddress}>
                📋 Copy
              </button>
            </div>

            <div className="balance-grid">
              <div className="balance-item">
                <div className="balance-label">{currentNetwork.symbol} Balance</div>
                <div className={`balance-value ${isLoadingBalances ? 'loading' : ''}`}>
                  {!isLoadingBalances && `${parseFloat(ethBalance).toFixed(4)}`}
                </div>
              </div>
              {Object.entries(tokenBalances).map(([symbol, balance]) => (
                <div className="balance-item" key={symbol}>
                  <div className="balance-label">{symbol} Balance</div>
                  <div className={`balance-value ${isLoadingBalances ? 'loading' : ''}`}>
                    {!isLoadingBalances && `${parseFloat(balance).toFixed(2)}`}
                  </div>
                </div>
              ))}
            </div>

            <button
              className="connect-btn disconnect"
              onClick={disconnectWallet}
              style={{ marginTop: '20px' }}
            >
              🔌 Disconnect Wallet
            </button>
          </>
        ) : (
          <button className="connect-btn" onClick={connectWallet}>
            🦊 Connect MetaMask
          </button>
        )}
      </div>

      {/* Transfer Card */}
      <div className="transfer-card">
        <div className="tabs">
          <button
            className={`tab ${activeTab === 'send' ? 'active' : ''}`}
            onClick={() => setActiveTab('send')}
          >
            Send
          </button>
          <button
            className={`tab ${activeTab === 'receive' ? 'active' : ''}`}
            onClick={() => setActiveTab('receive')}
          >
            Receive
          </button>
          <button
            className={`tab ${activeTab === 'history' ? 'active' : ''}`}
            onClick={() => setActiveTab('history')}
          >
            History
          </button>
        </div>

        {!isConnected ? (
          <div className="not-connected-overlay">
            <h3>Connect Your Wallet</h3>
            <p>Connect your MetaMask wallet to send and receive crypto</p>
            <button className="connect-btn" onClick={connectWallet}>
              🦊 Connect MetaMask
            </button>
          </div>
        ) : (
          <>
            {activeTab === 'send' && (
              <>
                <div className="form-group">
                  <label className="form-label">Select Asset</label>
                  <div className="asset-selector">
                    <button
                      className={`asset-btn ${selectedAsset === 'ETH' ? 'active' : ''}`}
                      onClick={() => setSelectedAsset('ETH')}
                    >
                      ETH
                    </button>
                    {Object.keys(tokenBalances).map(symbol => (
                      <button
                        key={symbol}
                        className={`asset-btn ${selectedAsset === symbol ? 'active' : ''}`}
                        onClick={() => setSelectedAsset(symbol)}
                      >
                        {symbol}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="form-group">
                  <label className="form-label">Recipient Address</label>
                  <input
                    type="text"
                    className={`form-input ${recipientAddress && !ethers.isAddress(recipientAddress) ? 'error' : ''}`}
                    placeholder="0x..."
                    value={recipientAddress}
                    onChange={(e) => setRecipientAddress(e.target.value)}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Amount</label>
                  <div className="amount-row">
                    <input
                      type="number"
                      className="form-input"
                      placeholder="0.00"
                      value={transferAmount}
                      onChange={(e) => setTransferAmount(e.target.value)}
                      step="0.0001"
                      min="0"
                    />
                    <button className="max-btn" onClick={setMaxAmount}>
                      MAX
                    </button>
                  </div>
                </div>

                {gasEstimate && (
                  <div className="gas-estimate">
                    <span className="gas-label">Estimated Gas Fee</span>
                    <span className="gas-value">~{parseFloat(gasEstimate).toFixed(6)} ETH</span>
                  </div>
                )}

                <button
                  className="send-btn"
                  onClick={handleTransfer}
                  disabled={
                    isTransferring ||
                    !recipientAddress ||
                    !transferAmount ||
                    !ethers.isAddress(recipientAddress)
                  }
                >
                  {isTransferring ? 'Sending...' : `Send ${selectedAsset}`}
                </button>
              </>
            )}

            {activeTab === 'receive' && (
              <div className="receive-section">
                <div className="qr-placeholder">📱</div>
                <p style={{ color: '#64748b', marginBottom: '12px' }}>
                  Share your address to receive crypto
                </p>
                <div className="receive-address">{walletAddress}</div>
                <button className="connect-btn" onClick={copyAddress}>
                  📋 Copy Address
                </button>
              </div>
            )}

            {activeTab === 'history' && (
              <>
                {transactions.length === 0 ? (
                  <div className="empty-state">
                    <div className="empty-state-icon">📭</div>
                    <p>No transactions yet</p>
                  </div>
                ) : (
                  transactions.map((tx, index) => (
                    <div className="history-item" key={index}>
                      <div className="history-left">
                        <div className={`history-icon ${tx.type}`}>
                          {tx.type === 'send' ? '↗️' : '↙️'}
                        </div>
                        <div className="history-details">
                          <h4>{tx.type === 'send' ? 'Sent' : 'Received'} {tx.asset}</h4>
                          <p>To: {formatAddress(tx.to)}</p>
                          {tx.hash && currentNetwork.explorer && (
                            <a
                              href={`${currentNetwork.explorer}/tx/${tx.hash}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="tx-link"
                            >
                              View on Explorer →
                            </a>
                          )}
                        </div>
                      </div>
                      <div className="history-amount">
                        <div className="value">-{tx.amount} {tx.asset}</div>
                        <div className="status">✓ {tx.status}</div>
                      </div>
                    </div>
                  ))
                )}
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default P2PTransfer;