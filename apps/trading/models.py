"""
Trading models - Orders, Trades, Order Book
"""
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.core.models import BaseModel


class TradingPair(BaseModel):
    """Trading pair (e.g., BTC/USDT)"""
    base_currency = models.CharField(max_length=10)
    quote_currency = models.CharField(max_length=10)
    symbol = models.CharField(max_length=20, unique=True)
    
    min_quantity = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('0.00001'))
    max_quantity = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('1000000'))
    quantity_step = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('0.00001'))
    
    min_price = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('0.00000001'))
    max_price = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('1000000'))
    price_step = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('0.01'))
    
    min_notional = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('10'))
    
    maker_fee = models.DecimalField(max_digits=5, decimal_places=4, default=Decimal('0.001'))
    taker_fee = models.DecimalField(max_digits=5, decimal_places=4, default=Decimal('0.001'))
    
    is_active = models.BooleanField(default=True)
    
    last_price = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('0'))
    price_change_24h = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    high_24h = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('0'))
    low_24h = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('0'))
    volume_24h = models.DecimalField(max_digits=30, decimal_places=8, default=Decimal('0'))
    
    class Meta:
        db_table = 'trading_pairs'
        ordering = ['symbol']
    
    def __str__(self):
        return self.symbol


class Order(BaseModel):
    """Trading order"""
    
    class OrderType(models.TextChoices):
        MARKET = 'market', 'Market'
        LIMIT = 'limit', 'Limit'
        STOP_LOSS = 'stop_loss', 'Stop Loss'
        STOP_LIMIT = 'stop_limit', 'Stop Limit'
        TAKE_PROFIT = 'take_profit', 'Take Profit'
        TAKE_PROFIT_LIMIT = 'take_profit_limit', 'Take Profit Limit'
        TRAILING_STOP = 'trailing_stop', 'Trailing Stop'
        OCO = 'oco', 'One Cancels Other'
    
    class Side(models.TextChoices):
        BUY = 'buy', 'Buy'
        SELL = 'sell', 'Sell'
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        OPEN = 'open', 'Open'
        PARTIALLY_FILLED = 'partially_filled', 'Partially Filled'
        FILLED = 'filled', 'Filled'
        CANCELLED = 'cancelled', 'Cancelled'
        EXPIRED = 'expired', 'Expired'
        TRIGGERED = 'triggered', 'Triggered'
    
    class TimeInForce(models.TextChoices):
        GTC = 'gtc', 'Good Till Cancelled'
        IOC = 'ioc', 'Immediate or Cancel'
        FOK = 'fok', 'Fill or Kill'
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    trading_pair = models.ForeignKey(TradingPair, on_delete=models.CASCADE, related_name='orders')
    
    order_type = models.CharField(max_length=20, choices=OrderType.choices, default=OrderType.LIMIT)
    side = models.CharField(max_length=4, choices=Side.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    time_in_force = models.CharField(max_length=3, choices=TimeInForce.choices, default=TimeInForce.GTC)
    
    quantity = models.DecimalField(max_digits=20, decimal_places=8)
    price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    
    # Stop order fields
    stop_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    take_profit_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    stop_loss_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    trailing_stop_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    highest_price_seen = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    lowest_price_seen = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    triggered_at = models.DateTimeField(null=True, blank=True)
    
    parent_order = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='child_orders')
    
    filled_quantity = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('0'))
    average_fill_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    
    fee = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('0'))
    fee_currency = models.CharField(max_length=10, blank=True)
    
    client_order_id = models.CharField(max_length=50, blank=True)
    
    class Meta:
        db_table = 'orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['trading_pair', 'status', 'side']),
            models.Index(fields=['status', 'order_type']),
        ]
    
    def __str__(self):
        return f"{self.side} {self.quantity} {self.trading_pair.symbol} @ {self.price or 'MARKET'}"
    
    @property
    def remaining_quantity(self):
        return self.quantity - self.filled_quantity
    
    @property
    def is_stop_order(self):
        return self.order_type in [
            self.OrderType.STOP_LOSS,
            self.OrderType.STOP_LIMIT,
            self.OrderType.TAKE_PROFIT,
            self.OrderType.TAKE_PROFIT_LIMIT,
            self.OrderType.TRAILING_STOP,
        ]
    
    def should_trigger(self, current_price):
        """Check if stop order should trigger"""
        if not self.is_stop_order or self.status != self.Status.PENDING:
            return False
        
        current_price = Decimal(str(current_price))
        
        if self.order_type in [self.OrderType.STOP_LOSS, self.OrderType.STOP_LIMIT]:
            if self.side == self.Side.SELL:
                return current_price <= self.stop_price
            return current_price >= self.stop_price
        
        if self.order_type in [self.OrderType.TAKE_PROFIT, self.OrderType.TAKE_PROFIT_LIMIT]:
            if self.side == self.Side.SELL:
                return current_price >= self.take_profit_price
            return current_price <= self.take_profit_price
        
        if self.order_type == self.OrderType.TRAILING_STOP:
            if not self.trailing_stop_percent:
                return False
            if self.side == self.Side.SELL:
                if self.highest_price_seen is None or current_price > self.highest_price_seen:
                    self.highest_price_seen = current_price
                    self.save(update_fields=['highest_price_seen'])
                trigger_price = self.highest_price_seen * (1 - self.trailing_stop_percent / 100)
                return current_price <= trigger_price
            else:
                if self.lowest_price_seen is None or current_price < self.lowest_price_seen:
                    self.lowest_price_seen = current_price
                    self.save(update_fields=['lowest_price_seen'])
                trigger_price = self.lowest_price_seen * (1 + self.trailing_stop_percent / 100)
                return current_price >= trigger_price
        
        return False
    
    def trigger(self):
        """Trigger a stop order"""
        if not self.is_stop_order:
            return
        
        self.triggered_at = timezone.now()
        
        if self.order_type in [self.OrderType.STOP_LOSS, self.OrderType.TAKE_PROFIT, self.OrderType.TRAILING_STOP]:
            self.order_type = self.OrderType.MARKET
            self.status = self.Status.OPEN
        elif self.order_type in [self.OrderType.STOP_LIMIT, self.OrderType.TAKE_PROFIT_LIMIT]:
            self.order_type = self.OrderType.LIMIT
            self.status = self.Status.OPEN
        
        self.save()


class Trade(BaseModel):
    """Executed trade between two orders"""
    
    trading_pair = models.ForeignKey(TradingPair, on_delete=models.CASCADE, related_name='trades')
    
    # Make these nullable for existing data
    buyer_order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='buy_trades', null=True, blank=True)
    seller_order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='sell_trades', null=True, blank=True)
    
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='buy_trades')
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sell_trades')
    
    price = models.DecimalField(max_digits=20, decimal_places=8)
    quantity = models.DecimalField(max_digits=20, decimal_places=8)
    
    buyer_fee = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('0'))
    seller_fee = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('0'))
    
    is_buyer_maker = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'trades'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['trading_pair', '-created_at']),
            models.Index(fields=['buyer', '-created_at']),
            models.Index(fields=['seller', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.quantity} {self.trading_pair.symbol} @ {self.price}"
    
    @property
    def total(self):
        return self.price * self.quantity
