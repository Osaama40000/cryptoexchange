/**
 * Token Service
 *
 * Service for interacting with ERC-20 tokens.
 * Handles balance queries, transfers, and approvals.
 *
 * ADD THIS FILE TO: frontend/src/services/tokenService.js
 */

import { ethers } from 'ethers';

// Standard ERC-20 ABI
const ERC20_ABI = [
  // Read functions
  'function name() view returns (string)',
  'function symbol() view returns (string)',
  'function decimals() view returns (uint8)',
  'function totalSupply() view returns (uint256)',
  'function balanceOf(address owner) view returns (uint256)',
  'function allowance(address owner, address spender) view returns (uint256)',

  // Write functions
  'function transfer(address to, uint256 amount) returns (bool)',
  'function approve(address spender, uint256 amount) returns (bool)',
  'function transferFrom(address from, address to, uint256 amount) returns (bool)',

  // Events
  'event Transfer(address indexed from, address indexed to, uint256 value)',
  'event Approval(address indexed owner, address indexed spender, uint256 value)'
];

// Popular tokens by network
export const TOKENS = {
  // Ethereum Mainnet (chainId: 1)
  1: {
    USDT: {
      address: '0xdAC17F958D2ee523a2206206994597C13D831ec7',
      decimals: 6,
      name: 'Tether USD',
      symbol: 'USDT',
      logo: '💵'
    },
    USDC: {
      address: '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
      decimals: 6,
      name: 'USD Coin',
      symbol: 'USDC',
      logo: '💲'
    },
    DAI: {
      address: '0x6B175474E89094C44Da98b954EescdeCB5f560B2f3E',
      decimals: 18,
      name: 'Dai Stablecoin',
      symbol: 'DAI',
      logo: '🔶'
    },
    WETH: {
      address: '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
      decimals: 18,
      name: 'Wrapped Ether',
      symbol: 'WETH',
      logo: '💎'
    },
    LINK: {
      address: '0x514910771AF9Ca656af840dff83E8264EcF986CA',
      decimals: 18,
      name: 'Chainlink',
      symbol: 'LINK',
      logo: '🔗'
    },
    UNI: {
      address: '0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984',
      decimals: 18,
      name: 'Uniswap',
      symbol: 'UNI',
      logo: '🦄'
    }
  },

  // Sepolia Testnet (chainId: 11155111)
  11155111: {
    USDT: {
      address: '0x7169D38820dfd117C3FA1f22a697dBA58d90BA06',
      decimals: 6,
      name: 'Test USDT',
      symbol: 'USDT',
      logo: '💵'
    },
    LINK: {
      address: '0x779877A7B0D9E8603169DdbD7836e478b4624789',
      decimals: 18,
      name: 'Chainlink',
      symbol: 'LINK',
      logo: '🔗'
    }
  },

  // Polygon (chainId: 137)
  137: {
    USDT: {
      address: '0xc2132D05D31c914a87C6611C10748AEb04B58e8F',
      decimals: 6,
      name: 'Tether USD',
      symbol: 'USDT',
      logo: '💵'
    },
    USDC: {
      address: '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174',
      decimals: 6,
      name: 'USD Coin',
      symbol: 'USDC',
      logo: '💲'
    },
    WMATIC: {
      address: '0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270',
      decimals: 18,
      name: 'Wrapped MATIC',
      symbol: 'WMATIC',
      logo: '💜'
    }
  },

  // BSC (chainId: 56)
  56: {
    USDT: {
      address: '0x55d398326f99059fF775485246999027B3197955',
      decimals: 18,
      name: 'Tether USD',
      symbol: 'USDT',
      logo: '💵'
    },
    BUSD: {
      address: '0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56',
      decimals: 18,
      name: 'Binance USD',
      symbol: 'BUSD',
      logo: '💛'
    },
    WBNB: {
      address: '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c',
      decimals: 18,
      name: 'Wrapped BNB',
      symbol: 'WBNB',
      logo: '🟡'
    }
  }
};

/**
 * Token Service Class
 */
class TokenService {
  constructor(provider, signer = null) {
    this.provider = provider;
    this.signer = signer;
  }

  /**
   * Update signer (after wallet connection)
   */
  setSigner(signer) {
    this.signer = signer;
  }

  /**
   * Get contract instance
   */
  getContract(tokenAddress, withSigner = false) {
    const contract = new ethers.Contract(
      tokenAddress,
      ERC20_ABI,
      withSigner && this.signer ? this.signer : this.provider
    );
    return contract;
  }

  /**
   * Get token info
   */
  async getTokenInfo(tokenAddress) {
    try {
      const contract = this.getContract(tokenAddress);
      const [name, symbol, decimals] = await Promise.all([
        contract.name(),
        contract.symbol(),
        contract.decimals()
      ]);
      return { name, symbol, decimals: Number(decimals), address: tokenAddress };
    } catch (error) {
      console.error('Failed to get token info:', error);
      throw error;
    }
  }

  /**
   * Get token balance for an address
   */
  async getBalance(tokenAddress, walletAddress) {
    try {
      const contract = this.getContract(tokenAddress);
      const [balance, decimals] = await Promise.all([
        contract.balanceOf(walletAddress),
        contract.decimals()
      ]);
      return ethers.formatUnits(balance, decimals);
    } catch (error) {
      console.error('Failed to get balance:', error);
      return '0';
    }
  }

  /**
   * Get balances for multiple tokens
   */
  async getMultipleBalances(tokenAddresses, walletAddress) {
    const balances = {};

    await Promise.all(
      tokenAddresses.map(async (tokenAddress) => {
        try {
          const contract = this.getContract(tokenAddress);
          const [balance, decimals, symbol] = await Promise.all([
            contract.balanceOf(walletAddress),
            contract.decimals(),
            contract.symbol()
          ]);
          balances[symbol] = {
            address: tokenAddress,
            balance: ethers.formatUnits(balance, decimals),
            decimals: Number(decimals)
          };
        } catch (error) {
          console.log(`Failed to get balance for ${tokenAddress}:`, error.message);
        }
      })
    );

    return balances;
  }

  /**
   * Get all supported token balances for a network
   */
  async getAllBalances(chainId, walletAddress) {
    const networkTokens = TOKENS[chainId] || {};
    const balances = {};

    for (const [symbol, tokenInfo] of Object.entries(networkTokens)) {
      try {
        const balance = await this.getBalance(tokenInfo.address, walletAddress);
        balances[symbol] = {
          ...tokenInfo,
          balance
        };
      } catch (error) {
        console.log(`Failed to get ${symbol} balance:`, error.message);
        balances[symbol] = {
          ...tokenInfo,
          balance: '0'
        };
      }
    }

    return balances;
  }

  /**
   * Transfer tokens
   */
  async transfer(tokenAddress, toAddress, amount) {
    if (!this.signer) {
      throw new Error('Signer required for transfers');
    }

    if (!ethers.isAddress(toAddress)) {
      throw new Error('Invalid recipient address');
    }

    const contract = this.getContract(tokenAddress, true);
    const decimals = await contract.decimals();
    const parsedAmount = ethers.parseUnits(amount.toString(), decimals);

    // Estimate gas first
    const gasEstimate = await contract.transfer.estimateGas(toAddress, parsedAmount);

    // Execute transfer
    const tx = await contract.transfer(toAddress, parsedAmount, {
      gasLimit: gasEstimate * 120n / 100n // Add 20% buffer
    });

    return tx;
  }

  /**
   * Check allowance
   */
  async getAllowance(tokenAddress, ownerAddress, spenderAddress) {
    const contract = this.getContract(tokenAddress);
    const [allowance, decimals] = await Promise.all([
      contract.allowance(ownerAddress, spenderAddress),
      contract.decimals()
    ]);
    return ethers.formatUnits(allowance, decimals);
  }

  /**
   * Approve spender
   */
  async approve(tokenAddress, spenderAddress, amount = 'max') {
    if (!this.signer) {
      throw new Error('Signer required for approvals');
    }

    const contract = this.getContract(tokenAddress, true);
    const decimals = await contract.decimals();

    let parsedAmount;
    if (amount === 'max') {
      parsedAmount = ethers.MaxUint256;
    } else {
      parsedAmount = ethers.parseUnits(amount.toString(), decimals);
    }

    const tx = await contract.approve(spenderAddress, parsedAmount);
    return tx;
  }

  /**
   * Estimate gas for transfer
   */
  async estimateTransferGas(tokenAddress, toAddress, amount) {
    try {
      const contract = this.getContract(tokenAddress, true);
      const decimals = await contract.decimals();
      const parsedAmount = ethers.parseUnits(amount.toString(), decimals);

      const gasLimit = await contract.transfer.estimateGas(toAddress, parsedAmount);
      const feeData = await this.provider.getFeeData();
      const gasCost = gasLimit * feeData.gasPrice;

      return {
        gasLimit: gasLimit.toString(),
        gasPrice: ethers.formatUnits(feeData.gasPrice, 'gwei'),
        gasCostWei: gasCost.toString(),
        gasCostEth: ethers.formatEther(gasCost)
      };
    } catch (error) {
      console.error('Gas estimation failed:', error);
      return null;
    }
  }
}

/**
 * Create a TokenService instance
 */
export const createTokenService = (provider, signer = null) => {
  return new TokenService(provider, signer);
};

/**
 * Get supported tokens for a network
 */
export const getSupportedTokens = (chainId) => {
  return TOKENS[chainId] || {};
};

/**
 * Check if a token is supported on a network
 */
export const isTokenSupported = (chainId, symbol) => {
  return TOKENS[chainId] && TOKENS[chainId][symbol] !== undefined;
};

/**
 * Get token address
 */
export const getTokenAddress = (chainId, symbol) => {
  const networkTokens = TOKENS[chainId];
  if (!networkTokens || !networkTokens[symbol]) return null;
  return networkTokens[symbol].address;
};

export default TokenService;