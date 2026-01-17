"""
Accounts Models
===============
Custom User model and Wallet Connection for Web3 authentication.
"""

import uuid
import secrets
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication."""

    def create_user(self, email, password=None, **extra_fields):
        """Create and return a regular user."""
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and return a superuser."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_email_verified', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Custom User Model
    -----------------
    Uses email as the primary identifier instead of username.
    Supports both email/password and wallet-based authentication.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    email = models.EmailField(
        unique=True,
        db_index=True,
        verbose_name='Email Address'
    )
    username = models.CharField(
        max_length=150,
        unique=True,
        blank=True,
        null=True
    )

    # Profile fields
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)

    # Verification status
    is_email_verified = models.BooleanField(default=False)
    is_2fa_enabled = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Use email as the login field
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        """Auto-generate username from email if not provided."""
        if not self.username:
            base_username = self.email.split('@')[0]
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exclude(pk=self.pk).exists():
                username = f"{base_username}{counter}"
                counter += 1
            self.username = username
        super().save(*args, **kwargs)


class WalletConnection(models.Model):
    """
    Wallet Connection Model
    -----------------------
    Stores connected Web3 wallets (MetaMask, WalletConnect).
    Uses signature-based verification - NEVER stores private keys.
    """

    WALLET_TYPES = [
        ('metamask', 'MetaMask'),
        ('walletconnect', 'WalletConnect'),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='wallet_connections'
    )
    wallet_address = models.CharField(
        max_length=42,
        db_index=True,
        help_text='Ethereum wallet address (checksummed)'
    )
    chain_id = models.IntegerField(
        default=1,
        help_text='Blockchain network ID'
    )
    wallet_type = models.CharField(
        max_length=20,
        choices=WALLET_TYPES,
        default='metamask'
    )
    is_primary = models.BooleanField(
        default=False,
        help_text='Primary wallet for this user'
    )
    is_verified = models.BooleanField(
        default=False,
        help_text='Wallet ownership verified via signature'
    )

    # Nonce for signature verification
    nonce = models.CharField(
        max_length=64,
        default=secrets.token_hex,
        help_text='Random nonce for signature verification'
    )

    # Timestamps
    last_used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Wallet Connection'
        verbose_name_plural = 'Wallet Connections'
        unique_together = ['wallet_address', 'chain_id']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.wallet_address[:8]}...{self.wallet_address[-6:]}"

    def regenerate_nonce(self):
        """Generate a new nonce after each signature verification."""
        self.nonce = secrets.token_hex(32)
        self.save(update_fields=['nonce', 'updated_at'])
        return self.nonce

    def mark_as_used(self):
        """Update last_used_at timestamp."""
        self.last_used_at = timezone.now()
        self.save(update_fields=['last_used_at'])


class AuthNonce(models.Model):
    """
    Authentication Nonce
    --------------------
    Temporary nonces for wallet authentication flow.
    Expires after 5 minutes.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    wallet_address = models.CharField(
        max_length=42,
        db_index=True
    )
    nonce = models.CharField(
        max_length=64,
        unique=True,
        default=secrets.token_hex
    )
    message = models.TextField(
        help_text='The message that needs to be signed'
    )
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Auth Nonce'
        verbose_name_plural = 'Auth Nonces'
        ordering = ['-created_at']

    def __str__(self):
        return f"Nonce for {self.wallet_address[:8]}..."

    @property
    def is_expired(self):
        """Check if nonce has expired."""
        return timezone.now() > self.expires_at

    @property
    def is_valid(self):
        """Check if nonce is still valid (not used and not expired)."""
        return not self.is_used and not self.is_expired

    @classmethod
    def create_for_wallet(cls, wallet_address, expiry_minutes=5):
        """Create a new nonce for wallet authentication."""
        from datetime import timedelta

        nonce = secrets.token_hex(32)
        expires_at = timezone.now() + timedelta(minutes=expiry_minutes)

        message = (
            f"Sign this message to authenticate with CryptoExchange Demo.\n\n"
            f"Wallet: {wallet_address}\n"
            f"Nonce: {nonce}\n"
            f"Timestamp: {timezone.now().isoformat()}\n\n"
            f"This signature will not trigger any blockchain transaction."
        )

        return cls.objects.create(
            wallet_address=wallet_address.lower(),
            nonce=nonce,
            message=message,
            expires_at=expires_at
        )