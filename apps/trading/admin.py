"""
Trading Admin Configuration
"""

from django.contrib import admin
from .models import TradingPair, Order, Trade


@admin.register(TradingPair)
class TradingPairAdmin(admin.ModelAdmin):
    list_display = [
        'symbol', 'base_currency', 'quote_currency', 'is_active',
        'last_price', 'volume_24h', 'price_change_24h'
    ]
    list_filter = ['is_active', 'base_currency', 'quote_currency']
    search_fields = ['symbol']
    ordering = ['symbol']

    fieldsets = (
        (None, {'fields': ('symbol', 'base_currency', 'quote_currency', 'is_active')}),
        ('Order Constraints',
         {'fields': ('min_order_size', 'max_order_size', 'price_precision', 'quantity_precision')}),
        ('Fees', {'fields': ('maker_fee', 'taker_fee')}),
        ('Market Stats', {'fields': ('last_price', 'price_change_24h', 'high_24h', 'low_24h', 'volume_24h')}),
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'created_at', 'user', 'trading_pair', 'side', 'order_type',
        'price', 'quantity', 'filled_quantity', 'status'
    ]
    list_filter = ['status', 'side', 'order_type', 'trading_pair']
    search_fields = ['user__email', 'id', 'client_order_id']
    ordering = ['-created_at']
    readonly_fields = ['id', 'created_at', 'updated_at', 'filled_at', 'cancelled_at']


@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    list_display = [
        'created_at', 'trading_pair', 'price', 'quantity',
        'buyer', 'seller', 'buyer_fee', 'seller_fee'
    ]
    list_filter = ['trading_pair', 'created_at']
    search_fields = ['buyer__email', 'seller__email', 'id']
    ordering = ['-created_at']
    readonly_fields = ['id', 'created_at']