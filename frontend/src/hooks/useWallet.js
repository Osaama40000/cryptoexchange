/**
 * useWallet Hook
 *
 * A reusable React hook for MetaMask wallet integration.
 * Use this hook in any component that needs wallet functionality.
 *
 * ADD THIS FILE TO: frontend/src/hooks/useWallet.js
 *
 * Usage:
 * const {
 *   isConnected,
 *   address,
 *   connect,
 *   disconnect,
 *   ethBalance,
 *   chainId,
 *   sendTransaction
 * } = useWallet();
 */

import { useState, useEffect, useCallback } from 'react';
import { ethers } from 'ethers';
import toast from 'react-hot-toast';

// Network configurations
const NETWORKS = {
  1: { name: 'Ethereum Mainnet', symbol: 'ETH', explorer: 'https://etherscan.io', rpc: 'https://eth.llamarpc.com' },
  11155111: { name: 'Sepolia Testnet', symbol: 'SepoliaETH', explorer: 'https://sepolia.etherscan.io', rpc: 'https://rpc.sepolia.org' },
  137: { name: 'Polygon', symbol: 'MATIC', explorer: 'https://polygonscan.com', rpc: 'https://polygon-rpc.com' },
  56: { name: 'BSC', symbol: 'BNB', explorer: 'https://bscscan.com', rpc: 'https://bsc-dataseed.binance.org' },
  42161: { name: 'Arbitrum One', symbol: 'ETH', explorer: 'https://arbiscan.io', rpc: 'https://arb1.arbitrum.io/rpc' },
  10: { name: 'Optimism', symbol: 'ETH', explorer: 'https://optimistic.etherscan.io', rpc: 'https://mainnet.optimism.io' },
};

export const useWallet = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [address, setAddress] = useState(null);
  const [chainId, setChainId] = useState(null);
  const [provider, setProvider] = useState(null);
  const [signer, setSigner] = useState(null);
  const [ethBalance, setEthBalance] = useState('0');
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState(null);

  // Check if MetaMask is available
  const isMetaMaskInstalled = typeof window !== 'undefined' && Boolean(window.ethereum);

  // Get current network info
  const network = NETWORKS[chainId] || { name: 'Unknown', symbol: 'ETH', explorer: '' };

  // Load ETH balance
  const loadBalance = useCallback(async (addr, prov) => {
    if (!addr || !prov) return;
    try {
      const balance = await prov.getBalance(addr);
      setEthBalance(ethers.formatEther(balance));
    } catch (err) {
      console.error('Failed to load balance:', err);
    }
  }, []);

  // Connect wallet
  const connect = useCallback(async () => {
    if (!isMetaMaskInstalled) {
      toast.error('MetaMask is not installed. Please install it first.');
      window.open('https://metamask.io/download/', '_blank');
      return false;
    }

    setIsConnecting(true);
    setError(null);

    try {
      // Request accounts
      const accounts = await window.ethereum.request({
        method: 'eth_requestAccounts'
      });

      if (accounts.length === 0) {
        throw new Error('No accounts found');
      }

      // Create provider and signer
      const web3Provider = new ethers.BrowserProvider(window.ethereum);
      const web3Signer = await web3Provider.getSigner();
      const networkInfo = await web3Provider.getNetwork();

      // Update state
      setProvider(web3Provider);
      setSigner(web3Signer);
      setAddress(accounts[0]);
      setChainId(Number(networkInfo.chainId));
      setIsConnected(true);

      // Load balance
      await loadBalance(accounts[0], web3Provider);

      toast.success('Wallet connected!');
      return true;
    } catch (err) {
      console.error('Connection error:', err);
      setError(err.message);

      if (err.code === 4001) {
        toast.error('Connection rejected');
      } else {
        toast.error('Failed to connect wallet');
      }
      return false;
    } finally {
      setIsConnecting(false);
    }
  }, [isMetaMaskInstalled, loadBalance]);

  // Disconnect wallet
  const disconnect = useCallback(() => {
    setIsConnected(false);
    setAddress(null);
    setProvider(null);
    setSigner(null);
    setEthBalance('0');
    setChainId(null);
    toast.success('Wallet disconnected');
  }, []);

  // Send transaction
  const sendTransaction = useCallback(async (to, value, data = null) => {
    if (!signer) {
      toast.error('Wallet not connected');
      return null;
    }

    if (!ethers.isAddress(to)) {
      toast.error('Invalid recipient address');
      return null;
    }

    try {
      const txParams = {
        to,
        value: ethers.parseEther(value.toString()),
      };

      if (data) {
        txParams.data = data;
      }

      const tx = await signer.sendTransaction(txParams);
      toast.loading('Transaction pending...', { id: tx.hash });

      const receipt = await tx.wait();
      toast.success('Transaction confirmed!', { id: tx.hash });

      // Refresh balance
      await loadBalance(address, provider);

      return receipt;
    } catch (err) {
      console.error('Transaction error:', err);

      if (err.code === 'ACTION_REJECTED' || err.code === 4001) {
        toast.error('Transaction rejected');
      } else if (err.message.includes('insufficient funds')) {
        toast.error('Insufficient funds');
      } else {
        toast.error('Transaction failed');
      }
      return null;
    }
  }, [signer, address, provider, loadBalance]);

  // Sign message
  const signMessage = useCallback(async (message) => {
    if (!signer) {
      toast.error('Wallet not connected');
      return null;
    }

    try {
      const signature = await signer.signMessage(message);
      return signature;
    } catch (err) {
      console.error('Signing error:', err);
      if (err.code === 'ACTION_REJECTED' || err.code === 4001) {
        toast.error('Signing rejected');
      } else {
        toast.error('Failed to sign message');
      }
      return null;
    }
  }, [signer]);

  // Switch network
  const switchNetwork = useCallback(async (targetChainId) => {
    if (!isMetaMaskInstalled) return false;

    const chainIdHex = `0x${targetChainId.toString(16)}`;

    try {
      await window.ethereum.request({
        method: 'wallet_switchEthereumChain',
        params: [{ chainId: chainIdHex }],
      });
      return true;
    } catch (err) {
      // Chain not added, try to add it
      if (err.code === 4902) {
        const networkConfig = NETWORKS[targetChainId];
        if (networkConfig && networkConfig.rpc) {
          try {
            await window.ethereum.request({
              method: 'wallet_addEthereumChain',
              params: [{
                chainId: chainIdHex,
                chainName: networkConfig.name,
                nativeCurrency: {
                  name: networkConfig.symbol,
                  symbol: networkConfig.symbol,
                  decimals: 18,
                },
                rpcUrls: [networkConfig.rpc],
                blockExplorerUrls: [networkConfig.explorer],
              }],
            });
            return true;
          } catch (addErr) {
            console.error('Failed to add network:', addErr);
            toast.error('Failed to add network');
            return false;
          }
        }
      }
      console.error('Failed to switch network:', err);
      toast.error('Failed to switch network');
      return false;
    }
  }, [isMetaMaskInstalled]);

  // Format address for display
  const formatAddress = useCallback((addr) => {
    if (!addr) return '';
    return `${addr.slice(0, 6)}...${addr.slice(-4)}`;
  }, []);

  // Get explorer URL for transaction
  const getExplorerUrl = useCallback((txHash) => {
    if (!network.explorer || !txHash) return '';
    return `${network.explorer}/tx/${txHash}`;
  }, [network]);

  // Listen for wallet events
  useEffect(() => {
    if (!isMetaMaskInstalled) return;

    const handleAccountsChanged = async (accounts) => {
      if (accounts.length === 0) {
        disconnect();
      } else if (accounts[0] !== address) {
        setAddress(accounts[0]);
        if (provider) {
          await loadBalance(accounts[0], provider);
        }
      }
    };

    const handleChainChanged = (newChainId) => {
      const chainIdNum = parseInt(newChainId, 16);
      setChainId(chainIdNum);
      // Reload the page is recommended by MetaMask
      // But we'll just refresh the balance instead
      if (address && provider) {
        loadBalance(address, provider);
      }
    };

    const handleDisconnect = () => {
      disconnect();
    };

    window.ethereum.on('accountsChanged', handleAccountsChanged);
    window.ethereum.on('chainChanged', handleChainChanged);
    window.ethereum.on('disconnect', handleDisconnect);

    return () => {
      window.ethereum.removeListener('accountsChanged', handleAccountsChanged);
      window.ethereum.removeListener('chainChanged', handleChainChanged);
      window.ethereum.removeListener('disconnect', handleDisconnect);
    };
  }, [isMetaMaskInstalled, address, provider, disconnect, loadBalance]);

  // Auto-connect if previously connected
  useEffect(() => {
    const autoConnect = async () => {
      if (!isMetaMaskInstalled) return;

      try {
        const accounts = await window.ethereum.request({ method: 'eth_accounts' });
        if (accounts.length > 0) {
          const web3Provider = new ethers.BrowserProvider(window.ethereum);
          const web3Signer = await web3Provider.getSigner();
          const networkInfo = await web3Provider.getNetwork();

          setProvider(web3Provider);
          setSigner(web3Signer);
          setAddress(accounts[0]);
          setChainId(Number(networkInfo.chainId));
          setIsConnected(true);

          await loadBalance(accounts[0], web3Provider);
        }
      } catch (err) {
        console.log('Auto-connect failed:', err);
      }
    };

    autoConnect();
  }, [isMetaMaskInstalled, loadBalance]);

  return {
    // State
    isConnected,
    isConnecting,
    address,
    chainId,
    provider,
    signer,
    ethBalance,
    network,
    error,
    isMetaMaskInstalled,

    // Actions
    connect,
    disconnect,
    sendTransaction,
    signMessage,
    switchNetwork,
    refreshBalance: () => loadBalance(address, provider),

    // Utilities
    formatAddress,
    getExplorerUrl,
  };
};

export default useWallet;