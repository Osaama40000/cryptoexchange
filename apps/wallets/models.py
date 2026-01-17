"""
Wallets Models
==============
Internal ledger system for managing user balances.
All trading happens off-chain using this internal ledger.
On-chain wallets are ONLY used for deposits and withdrawals.
"""

import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator


class Currency(models.Model):
    """
    Supported currencies/tokens on the exchange.
    """

    CURRENCY_TYPES = [
        ('native', 'Native (ETH)'),
        ('erc20', 'ERC-20 Token'),
        ('internal', 'Internal Only'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    symbol = models.CharField(max_length=10, unique=True, db_index=True)
    name = models.CharField(max_length=100)
    currency_type = models.CharField(max_length=20, choices=CURRENCY_TYPES, default='erc20')
    contract_address = models.CharField(
        max_length=42,
        blank=True,
        null=True,
        help_text='ERC-20 contract address (null for native ETH)'
    )
    decimals = models.IntegerField(default=18)
    chain_id = models.IntegerField(default=1)

    # Status
    is_active = models.BooleanField(default=True)
    is_deposit_enabled = models.BooleanField(default=True)
    is_withdrawal_enabled = models.BooleanField(default=True)

    # Limits
    min_deposit = models.DecimalField(
        max_digits=36, decimal_places=18, default=Decimal('0')
    )
    min_withdrawal = models.DecimalField(
        max_digits=36, decimal_places=18, default=Decimal('0')
    )
    withdrawal_fee = models.DecimalField(
        max_digits=36, decimal_places=18, default=Decimal('0')
    )

    # Display
    icon_url = models.URLField(blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Currency'
        verbose_name_plural = 'Currencies'
        ordering = ['symbol']

    def __str__(self):
        return f"{self.symbol} - {self.name}"


class Balance(models.Model):
    """
    User's internal balance for each currency.
    This is the INTERNAL LEDGER - not on-chain balance.

    - available: Can be used for trading or withdrawal
    - locked: Reserved for open orders
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='balances'
    )
    currency = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        related_name='balances'
    )

    # Balance fields
    available = models.DecimalField(
        max_digits=36,
        decimal_places=18,
        default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))],
        help_text='Available for trading/withdrawal'
    )
    locked = models.DecimalField(
        max_digits=36,
        decimal_places=18,
        default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))],
        help_text='Locked in open orders'
    )

    # Optimistic locking for concurrent updates
    version = models.IntegerField(default=1)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Balance'
        verbose_name_plural = 'Balances'
        unique_together = ['user', 'currency']
        ordering = ['currency__symbol']

    def __str__(self):
        return f"{self.user.email} - {self.currency.symbol}: {self.total}"

    @property
    def total(self):
        """Total balance (available + locked)."""
        return self.available + self.locked

    def lock_amount(self, amount):
        """Lock amount for an order."""
        amount = Decimal(str(amount))
        if amount > self.available:
            raise ValueError('Insufficient available balance')
        self.available -= amount
        self.locked += amount
        self.version += 1
        self.save()

    def unlock_amount(self, amount):
        """Unlock amount (order cancelled)."""
        amount = Decimal(str(amount))
        if amount > self.locked:
            raise ValueError('Insufficient locked balance')
        self.locked -= amount
        self.available += amount
        self.version += 1
        self.save()

    def deduct_locked(self, amount):
        """Deduct from locked (order filled)."""
        amount = Decimal(str(amount))
        if amount > self.locked:
            raise ValueError('Insufficient locked balance')
        self.locked -= amount
        self.version += 1
        self.save()

    def credit(self, amount):
        """Credit amount to available balance."""
        amount = Decimal(str(amount))
        self.available += amount
        self.version += 1
        self.save()


class LedgerEntry(models.Model):
    """
    Immutable ledger of all balance changes.
    Used for auditing and reconciliation.
    """

    ENTRY_TYPES = [
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('trade_buy', 'Trade Buy'),
        ('trade_sell', 'Trade Sell'),
        ('fee', 'Trading Fee'),
        ('order_lock', 'Order Lock'),
        ('order_unlock', 'Order Unlock'),
        ('admin_credit', 'Admin Credit'),
        ('admin_debit', 'Admin Debit'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ledger_entries'
    )
    currency = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        related_name='ledger_entries'
    )

    entry_type = models.CharField(max_length=30, choices=ENTRY_TYPES)
    amount = models.DecimalField(
        max_digits=36,
        decimal_places=18,
        help_text='Positive for credit, negative for debit'
    )
    balance_before = models.DecimalField(max_digits=36, decimal_places=18)
    balance_after = models.DecimalField(max_digits=36, decimal_places=18)

    # Reference to related object
    reference_type = models.CharField(max_length=50, blank=True, null=True)
    reference_id = models.UUIDField(blank=True, null=True)

    description = models.TextField(blank=True, null=True)

    # Who made this entry (for admin actions)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_ledger_entries'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Ledger Entry'
        verbose_name_plural = 'Ledger Entries'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'currency']),
            models.Index(fields=['reference_type', 'reference_id']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.entry_type} - {self.amount} {self.currency.symbol}"


class Deposit(models.Model):
    """
    Incoming deposit records.
    Deposits are detected on-chain and credited to internal balance.
    """

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirming', 'Confirming'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='deposits'
    )
    currency = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        related_name='deposits'
    )

    # Transaction details
    tx_hash = models.CharField(max_length=66, db_index=True)
    from_address = models.CharField(max_length=42)
    to_address = models.CharField(max_length=42)
    amount = models.DecimalField(max_digits=36, decimal_places=18)

    # Confirmation tracking
    confirmations = models.IntegerField(default=0)
    required_confirmations = models.IntegerField(default=12)
    block_number = models.BigIntegerField(null=True, blank=True)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    credited_at = models.DateTimeField(null=True, blank=True)

    # Network
    chain_id = models.IntegerField(default=1)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Deposit'
        verbose_name_plural = 'Deposits'
        unique_together = ['tx_hash', 'chain_id']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.amount} {self.currency.symbol} - {self.status}"


class Withdrawal(models.Model):
    """
    Outgoing withdrawal requests.
    Withdrawals are requested internally and processed on-chain.
    """

    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='withdrawals'
    )
    currency = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        related_name='withdrawals'
    )

    # Withdrawal details
    to_address = models.CharField(max_length=42)
    amount = models.DecimalField(max_digits=36, decimal_places=18)
    fee = models.DecimalField(max_digits=36, decimal_places=18, default=Decimal('0'))

    # Transaction (after processing)
    tx_hash = models.CharField(max_length=66, blank=True, null=True)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Approval
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_withdrawals'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True)

    # Processing
    processed_at = models.DateTimeField(null=True, blank=True)

    # Network
    chain_id = models.IntegerField(default=1)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Withdrawal'
        verbose_name_plural = 'Withdrawals'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.amount} {self.currency.symbol} to {self.to_address[:10]}... - {self.status}"

    @property
    def net_amount(self):
        """Amount after fee deduction."""
        return self.amount - self.fee