"""
Trading Models
==============
Models for trading pairs, orders, and executed trades.
"""

import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator

from apps.wallets.models import Currency


class TradingPair(models.Model):
    """
    Trading pair (e.g., ETH/USDT, BTC/USDT).

    - base_currency: The currency being traded (ETH in ETH/USDT)
    - quote_currency: The currency used for pricing (USDT in ETH/USDT)
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    symbol = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        help_text='Trading pair symbol (e.g., ETH_USDT)'
    )
    base_currency = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        related_name='base_pairs',
        help_text='Currency being traded'
    )
    quote_currency = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        related_name='quote_pairs',
        help_text='Currency used for pricing'
    )

    # Status
    is_active = models.BooleanField(default=True)

    # Order constraints
    min_order_size = models.DecimalField(
        max_digits=36, decimal_places=18, default=Decimal('0.0001'),
        help_text='Minimum order size in base currency'
    )
    max_order_size = models.DecimalField(
        max_digits=36, decimal_places=18, default=Decimal('1000000'),
        help_text='Maximum order size in base currency'
    )
    price_precision = models.IntegerField(
        default=8,
        help_text='Decimal places for price'
    )
    quantity_precision = models.IntegerField(
        default=8,
        help_text='Decimal places for quantity'
    )

    # Fees
    maker_fee = models.DecimalField(
        max_digits=10, decimal_places=6, default=Decimal('0.001'),
        help_text='Maker fee (0.001 = 0.1%)'
    )
    taker_fee = models.DecimalField(
        max_digits=10, decimal_places=6, default=Decimal('0.001'),
        help_text='Taker fee (0.001 = 0.1%)'
    )

    # Market stats (updated periodically)
    last_price = models.DecimalField(
        max_digits=36, decimal_places=18, null=True, blank=True
    )
    price_change_24h = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True,
        help_text='24h price change percentage'
    )
    high_24h = models.DecimalField(
        max_digits=36, decimal_places=18, null=True, blank=True
    )
    low_24h = models.DecimalField(
        max_digits=36, decimal_places=18, null=True, blank=True
    )
    volume_24h = models.DecimalField(
        max_digits=36, decimal_places=18, null=True, blank=True,
        help_text='24h volume in base currency'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Trading Pair'
        verbose_name_plural = 'Trading Pairs'
        unique_together = ['base_currency', 'quote_currency']
        ordering = ['symbol']

    def __str__(self):
        return self.symbol

    def save(self, *args, **kwargs):
        if not self.symbol:
            self.symbol = f"{self.base_currency.symbol}_{self.quote_currency.symbol}"
        super().save(*args, **kwargs)


class Order(models.Model):
    """
    User order in the order book.

    Order lifecycle:
    1. Created -> status='open', funds locked
    2. Partially filled -> status='partial'
    3. Fully filled -> status='filled'
    4. Cancelled -> status='cancelled', remaining funds unlocked
    """

    ORDER_TYPES = [
        ('limit', 'Limit Order'),
        ('market', 'Market Order'),
    ]

    SIDE_CHOICES = [
        ('buy', 'Buy'),
        ('sell', 'Sell'),
    ]

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('partial', 'Partially Filled'),
        ('filled', 'Filled'),
        ('cancelled', 'Cancelled'),
    ]

    TIME_IN_FORCE = [
        ('GTC', 'Good Till Cancelled'),
        ('IOC', 'Immediate Or Cancel'),
        ('FOK', 'Fill Or Kill'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    trading_pair = models.ForeignKey(
        TradingPair,
        on_delete=models.PROTECT,
        related_name='orders'
    )

    # Order details
    order_type = models.CharField(max_length=10, choices=ORDER_TYPES)
    side = models.CharField(max_length=4, choices=SIDE_CHOICES)
    price = models.DecimalField(
        max_digits=36, decimal_places=18,
        null=True, blank=True,
        help_text='Limit price (null for market orders)'
    )
    quantity = models.DecimalField(
        max_digits=36, decimal_places=18,
        validators=[MinValueValidator(Decimal('0'))],
        help_text='Original order quantity'
    )
    filled_quantity = models.DecimalField(
        max_digits=36, decimal_places=18,
        default=Decimal('0'),
        help_text='Quantity filled so far'
    )

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    time_in_force = models.CharField(max_length=10, choices=TIME_IN_FORCE, default='GTC')

    # Client reference
    client_order_id = models.CharField(
        max_length=64, blank=True, null=True,
        help_text='Client-provided order ID'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    filled_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['trading_pair', 'side', 'status', 'price']),
            models.Index(fields=['user', 'status']),
        ]

    def __str__(self):
        return f"{self.side.upper()} {self.quantity} {self.trading_pair.symbol} @ {self.price}"

    @property
    def remaining_quantity(self):
        """Quantity still to be filled."""
        return self.quantity - self.filled_quantity

    @property
    def is_fully_filled(self):
        """Check if order is completely filled."""
        return self.filled_quantity >= self.quantity

    @property
    def fill_percentage(self):
        """Percentage of order filled."""
        if self.quantity == 0:
            return Decimal('0')
        return (self.filled_quantity / self.quantity) * 100

    def get_locked_amount(self):
        """
        Calculate the amount that should be locked for this order.

        - Buy order: locks quote currency (price * remaining_quantity)
        - Sell order: locks base currency (remaining_quantity)
        """
        if self.side == 'buy':
            if self.price:
                return self.remaining_quantity * self.price
            return Decimal('0')  # Market orders handled differently
        else:
            return self.remaining_quantity


class Trade(models.Model):
    """
    Executed trade between two orders.

    Each trade involves:
    - A buy order and a sell order
    - A buyer and a seller
    - Transfer of base currency (seller -> buyer)
    - Transfer of quote currency (buyer -> seller)
    - Fees deducted from both parties
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trading_pair = models.ForeignKey(
        TradingPair,
        on_delete=models.PROTECT,
        related_name='trades'
    )

    # Orders involved
    buy_order = models.ForeignKey(
        Order,
        on_delete=models.PROTECT,
        related_name='buy_trades'
    )
    sell_order = models.ForeignKey(
        Order,
        on_delete=models.PROTECT,
        related_name='sell_trades'
    )

    # Users involved
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='buy_trades'
    )
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sell_trades'
    )

    # Trade details
    price = models.DecimalField(max_digits=36, decimal_places=18)
    quantity = models.DecimalField(max_digits=36, decimal_places=18)
    quote_quantity = models.DecimalField(
        max_digits=36, decimal_places=18,
        help_text='price * quantity'
    )

    # Fees
    buyer_fee = models.DecimalField(max_digits=36, decimal_places=18, default=Decimal('0'))
    seller_fee = models.DecimalField(max_digits=36, decimal_places=18, default=Decimal('0'))

    # Who was the maker (had the resting order)
    buyer_is_maker = models.BooleanField()

    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Trade'
        verbose_name_plural = 'Trades'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['trading_pair', '-created_at']),
            models.Index(fields=['buyer', '-created_at']),
            models.Index(fields=['seller', '-created_at']),
        ]

    def __str__(self):
        return f"{self.quantity} {self.trading_pair.base_currency.symbol} @ {self.price}"