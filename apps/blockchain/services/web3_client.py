"""
Web3 Client Service
===================
Service for interacting with Ethereum-compatible blockchains.

IMPORTANT: This service is READ-ONLY for security.
We never store or handle private keys.
All transactions are verified via signature verification.
"""

import logging
from decimal import Decimal
from typing import Optional, Dict, Any
from web3 import Web3
from web3.middleware import geth_poa_middleware
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger('apps.blockchain')


class Web3Client:
    """
    Web3 client for blockchain interactions.

    Features:
    - Read blockchain data (balances, transactions)
    - Verify transaction confirmations
    - Monitor addresses for deposits

    NEVER handles private keys or signs transactions.
    """

    _instances: Dict[int, 'Web3Client'] = {}

    def __init__(self, chain_id: int = None):
        """
        Initialize Web3 client for a specific chain.

        Args:
            chain_id: Blockchain network ID. Defaults to active chain from settings.
        """
        if chain_id is None:
            chain_id = settings.BLOCKCHAIN_CONFIG['ACTIVE_CHAIN_ID']

        self.chain_id = chain_id
        self.network_config = settings.BLOCKCHAIN_CONFIG['NETWORKS'].get(chain_id, {})

        rpc_url = self.network_config.get('rpc_url') or settings.BLOCKCHAIN_CONFIG['ACTIVE_RPC_URL']

        if not rpc_url:
            logger.warning(f"No RPC URL configured for chain {chain_id}")
            self.w3 = None
            return

        self.w3 = Web3(Web3.HTTPProvider(rpc_url))

        # Add PoA middleware for testnets like Sepolia
        if self.network_config.get('is_testnet', False):
            self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)

        logger.info(f"Web3 client initialized for chain {chain_id}")

    @classmethod
    def get_instance(cls, chain_id: int = None) -> 'Web3Client':
        """Get or create a Web3Client instance for a chain."""
        if chain_id is None:
            chain_id = settings.BLOCKCHAIN_CONFIG['ACTIVE_CHAIN_ID']

        if chain_id not in cls._instances:
            cls._instances[chain_id] = cls(chain_id)

        return cls._instances[chain_id]

    @property
    def is_connected(self) -> bool:
        """Check if connected to the blockchain."""
        if not self.w3:
            return False
        try:
            return self.w3.is_connected()
        except Exception:
            return False

    def get_current_block(self) -> Optional[int]:
        """Get the current block number."""
        if not self.is_connected:
            return None

        try:
            return self.w3.eth.block_number
        except Exception as e:
            logger.error(f"Error getting current block: {e}")
            return None

    def get_eth_balance(self, address: str) -> Optional[Decimal]:
        """
        Get ETH balance of an address.

        Args:
            address: Ethereum address

        Returns:
            Balance in ETH (not Wei)
        """
        if not self.is_connected:
            return None

        try:
            checksum_address = Web3.to_checksum_address(address)
            balance_wei = self.w3.eth.get_balance(checksum_address)
            balance_eth = self.w3.from_wei(balance_wei, 'ether')
            return Decimal(str(balance_eth))
        except Exception as e:
            logger.error(f"Error getting ETH balance for {address}: {e}")
            return None

    def get_token_balance(
            self,
            token_address: str,
            wallet_address: str,
            decimals: int = 18
    ) -> Optional[Decimal]:
        """
        Get ERC-20 token balance.

        Args:
            token_address: Token contract address
            wallet_address: Wallet to check
            decimals: Token decimals

        Returns:
            Token balance
        """
        if not self.is_connected:
            return None

        try:
            # ERC-20 balanceOf ABI
            abi = [{
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function"
            }]

            contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(token_address),
                abi=abi
            )

            balance = contract.functions.balanceOf(
                Web3.to_checksum_address(wallet_address)
            ).call()

            return Decimal(balance) / Decimal(10 ** decimals)
        except Exception as e:
            logger.error(f"Error getting token balance: {e}")
            return None

    def get_transaction(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """
        Get transaction details.

        Args:
            tx_hash: Transaction hash

        Returns:
            Transaction details dict
        """
        if not self.is_connected:
            return None

        try:
            tx = self.w3.eth.get_transaction(tx_hash)
            if tx:
                return dict(tx)
            return None
        except Exception as e:
            logger.error(f"Error getting transaction {tx_hash}: {e}")
            return None

    def get_transaction_receipt(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """
        Get transaction receipt (for confirmation status).

        Args:
            tx_hash: Transaction hash

        Returns:
            Transaction receipt dict
        """
        if not self.is_connected:
            return None

        try:
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            if receipt:
                return dict(receipt)
            return None
        except Exception as e:
            logger.error(f"Error getting receipt for {tx_hash}: {e}")
            return None

    def get_transaction_confirmations(self, tx_hash: str) -> Optional[int]:
        """
        Get number of confirmations for a transaction.

        Args:
            tx_hash: Transaction hash

        Returns:
            Number of confirmations
        """
        if not self.is_connected:
            return None

        try:
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            if not receipt or not receipt.get('blockNumber'):
                return 0

            current_block = self.w3.eth.block_number
            tx_block = receipt['blockNumber']

            return max(0, current_block - tx_block + 1)
        except Exception as e:
            logger.error(f"Error getting confirmations for {tx_hash}: {e}")
            return None

    def is_valid_address(self, address: str) -> bool:
        """Check if an address is valid."""
        try:
            Web3.to_checksum_address(address)
            return True
        except Exception:
            return False

    def to_checksum_address(self, address: str) -> str:
        """Convert address to checksum format."""
        return Web3.to_checksum_address(address)

    def get_gas_price(self) -> Optional[int]:
        """Get current gas price in Wei."""
        if not self.is_connected:
            return None

        try:
            return self.w3.eth.gas_price
        except Exception as e:
            logger.error(f"Error getting gas price: {e}")
            return None

    def get_network_info(self) -> Dict[str, Any]:
        """Get network information."""
        return {
            'chain_id': self.chain_id,
            'name': self.network_config.get('name', 'Unknown'),
            'is_testnet': self.network_config.get('is_testnet', False),
            'explorer': self.network_config.get('explorer', ''),
            'is_connected': self.is_connected,
            'current_block': self.get_current_block(),
        }