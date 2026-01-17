"""
Wallet Authentication Service
=============================
Handles signature verification for MetaMask/WalletConnect authentication.
NEVER handles private keys - only verifies signatures.
"""

import logging
from eth_account.messages import encode_defunct
from web3 import Web3
from django.utils import timezone

from apps.accounts.models import AuthNonce, WalletConnection, User

logger = logging.getLogger('apps.accounts')


class WalletAuthService:
    """
    Service for wallet-based authentication.

    Flow:
    1. User requests nonce for their wallet address
    2. User signs the message containing the nonce
    3. Backend verifies the signature
    4. If valid, user is authenticated or account is created
    """

    @staticmethod
    def create_nonce(wallet_address: str) -> AuthNonce:
        """
        Create a new authentication nonce for a wallet address.

        Args:
            wallet_address: Ethereum wallet address

        Returns:
            AuthNonce object with message to sign
        """
        # Normalize address to checksum format
        checksum_address = Web3.to_checksum_address(wallet_address)

        # Delete any existing unused nonces for this wallet
        AuthNonce.objects.filter(
            wallet_address=checksum_address.lower(),
            is_used=False
        ).delete()

        # Create new nonce
        nonce = AuthNonce.create_for_wallet(checksum_address)

        logger.info(f"Created auth nonce for wallet {checksum_address[:10]}...")
        return nonce

    @staticmethod
    def verify_signature(wallet_address: str, signature: str, nonce: str) -> bool:
        """
        Verify a wallet signature.

        Args:
            wallet_address: Claimed wallet address
            signature: Signature from wallet
            nonce: Nonce that was signed

        Returns:
            True if signature is valid, False otherwise
        """
        try:
            checksum_address = Web3.to_checksum_address(wallet_address)

            # Get the nonce record
            nonce_record = AuthNonce.objects.filter(
                wallet_address=checksum_address.lower(),
                nonce=nonce,
                is_used=False
            ).first()

            if not nonce_record:
                logger.warning(f"Nonce not found for wallet {checksum_address[:10]}...")
                return False

            if nonce_record.is_expired:
                logger.warning(f"Nonce expired for wallet {checksum_address[:10]}...")
                return False

            # Verify the signature
            message = encode_defunct(text=nonce_record.message)

            w3 = Web3()
            recovered_address = w3.eth.account.recover_message(
                message,
                signature=signature
            )

            # Compare addresses (case-insensitive)
            if recovered_address.lower() != checksum_address.lower():
                logger.warning(
                    f"Signature mismatch: expected {checksum_address[:10]}..., "
                    f"got {recovered_address[:10]}..."
                )
                return False

            # Mark nonce as used
            nonce_record.is_used = True
            nonce_record.save()

            logger.info(f"Signature verified for wallet {checksum_address[:10]}...")
            return True

        except Exception as e:
            logger.error(f"Signature verification error: {str(e)}")
            return False

    @staticmethod
    def get_or_create_user_for_wallet(wallet_address: str) -> tuple[User, bool]:
        """
        Get existing user or create new user for a wallet address.

        Args:
            wallet_address: Verified wallet address

        Returns:
            Tuple of (User, created: bool)
        """
        checksum_address = Web3.to_checksum_address(wallet_address)

        # Check if wallet is already connected to a user
        wallet_connection = WalletConnection.objects.filter(
            wallet_address=checksum_address
        ).select_related('user').first()

        if wallet_connection:
            wallet_connection.mark_as_used()
            return wallet_connection.user, False

        # Create new user with wallet
        email = f"{checksum_address.lower()}@wallet.local"
        user = User.objects.create_user(
            email=email,
            password=None,  # No password for wallet-only users
            is_email_verified=True  # Wallet verification counts
        )

        # Create wallet connection
        WalletConnection.objects.create(
            user=user,
            wallet_address=checksum_address,
            is_primary=True,
            is_verified=True
        )

        logger.info(f"Created new user for wallet {checksum_address[:10]}...")
        return user, True

    @staticmethod
    def connect_wallet_to_user(
            user: User,
            wallet_address: str,
            wallet_type: str = 'metamask',
            chain_id: int = 1
    ) -> WalletConnection:
        """
        Connect a verified wallet to an existing user account.

        Args:
            user: User to connect wallet to
            wallet_address: Verified wallet address
            wallet_type: Type of wallet (metamask/walletconnect)
            chain_id: Blockchain network ID

        Returns:
            WalletConnection object
        """
        checksum_address = Web3.to_checksum_address(wallet_address)

        # Check if wallet is already connected to another user
        existing = WalletConnection.objects.filter(
            wallet_address=checksum_address
        ).exclude(user=user).first()

        if existing:
            raise ValueError('Wallet is already connected to another account.')

        # Create or update wallet connection
        wallet_connection, created = WalletConnection.objects.update_or_create(
            wallet_address=checksum_address,
            defaults={
                'user': user,
                'wallet_type': wallet_type,
                'chain_id': chain_id,
                'is_verified': True
            }
        )

        # If this is the user's first wallet, make it primary
        if not WalletConnection.objects.filter(user=user, is_primary=True).exists():
            wallet_connection.is_primary = True
            wallet_connection.save()

        logger.info(
            f"Connected wallet {checksum_address[:10]}... to user {user.email}"
        )
        return wallet_connection