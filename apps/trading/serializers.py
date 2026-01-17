"""
Trading Serializers
===================
"""

from rest_framework import serializers
from decimal import Decimal

from .models import TradingPair, Order, Trade


class TradingPairSerializer(serializers.ModelSerializer):
    """Serializer for trading pairs."""

    base_currency_symbol = serializers.CharField(source='base_currency.symbol', read_only=True)
    quote_currency_symbol = serializers.CharField(source='quote_currency.symbol', read_only=True)

    class Meta:
        model = TradingPair
        fields = [
            'id', 'symbol', 'base_currency_symbol', 'quote_currency_symbol',
            'is_active', 'min_order_size', 'max_order_size',
            'price_precision', 'quantity_precision',
            'maker_fee', 'taker_fee',
            'last_price', 'price_change_24h', 'high_24h', 'low_24h', 'volume_24h'
        ]


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for orders."""

    trading_pair_symbol = serializers.CharField(source='trading_pair.symbol', read_only=True)
    remaining_quantity = serializers.DecimalField(
        max_digits=36, decimal_places=18, read_only=True
    )
    fill_percentage = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = Order
        fields = [
            'id', 'trading_pair', 'trading_pair_symbol', 'order_type', 'side',
            'price', 'quantity', 'filled_quantity', 'remaining_quantity',
            'fill_percentage', 'status', 'time_in_force', 'client_order_id',
            'created_at', 'updated_at', 'filled_at', 'cancelled_at'
        ]
        read_only_fields = [
            'id', 'filled_quantity', 'status', 'created_at',
            'updated_at', 'filled_at', 'cancelled_at'
        ]


class CreateOrderSerializer(serializers.Serializer):
    """Serializer for creating new orders."""

    trading_pair_id = serializers.UUIDField()
    order_type = serializers.ChoiceField(choices=['limit', 'market'])
    side = serializers.ChoiceField(choices=['buy', 'sell'])
    price = serializers.DecimalField(
        max_digits=36, decimal_places=18,
        required=False, allow_null=True
    )
    quantity = serializers.DecimalField(max_digits=36, decimal_places=18)
    time_in_force = serializers.ChoiceField(
        choices=['GTC', 'IOC', 'FOK'],
        default='GTC'
    )
    client_order_id = serializers.CharField(max_length=64, required=False, allow_null=True)

    def validate_quantity(self, value):
        if value <= Decimal('0'):
            raise serializers.ValidationError('Quantity must be greater than 0.')
        return value

    def validate_price(self, value):
        if value is not None and value <= Decimal('0'):
            raise serializers.ValidationError('Price must be greater than 0.')
        return value

    def validate(self, attrs):
        # Limit orders require a price
        if attrs['order_type'] == 'limit' and not attrs.get('price'):
            raise serializers.ValidationError({
                'price': 'Price is required for limit orders.'
            })

        # Get trading pair
        try:
            trading_pair = TradingPair.objects.get(id=attrs['trading_pair_id'])
        except TradingPair.DoesNotExist:
            raise serializers.ValidationError({
                'trading_pair_id': 'Trading pair not found.'
            })

        if not trading_pair.is_active:
            raise serializers.ValidationError({
                'trading_pair_id': 'Trading pair is not active.'
            })

        # Validate order size
        if attrs['quantity'] < trading_pair.min_order_size:
            raise serializers.ValidationError({
                'quantity': f'Minimum order size is {trading_pair.min_order_size}.'
            })

        if attrs['quantity'] > trading_pair.max_order_size:
            raise serializers.ValidationError({
                'quantity': f'Maximum order size is {trading_pair.max_order_size}.'
            })

        attrs['trading_pair'] = trading_pair
        return attrs


class CancelOrderSerializer(serializers.Serializer):
    """Serializer for cancelling orders."""

    order_id = serializers.UUIDField()


class TradeSerializer(serializers.ModelSerializer):
    """Serializer for trades."""

    trading_pair_symbol = serializers.CharField(source='trading_pair.symbol', read_only=True)

    class Meta:
        model = Trade
        fields = [
            'id', 'trading_pair_symbol', 'price', 'quantity', 'quote_quantity',
            'buyer_fee', 'seller_fee', 'buyer_is_maker', 'created_at'
        ]


class UserTradeSerializer(serializers.ModelSerializer):
    """Serializer for user's trade history."""

    trading_pair_symbol = serializers.CharField(source='trading_pair.symbol', read_only=True)
    side = serializers.SerializerMethodField()
    fee = serializers.SerializerMethodField()
    is_maker = serializers.SerializerMethodField()

    class Meta:
        model = Trade
        fields = [
            'id', 'trading_pair_symbol', 'side', 'price', 'quantity',
            'quote_quantity', 'fee', 'is_maker', 'created_at'
        ]

    def get_side(self, obj):
        user = self.context.get('request').user
        return 'buy' if obj.buyer_id == user.id else 'sell'

    def get_fee(self, obj):
        user = self.context.get('request').user
        return str(obj.buyer_fee if obj.buyer_id == user.id else obj.seller_fee)

    def get_is_maker(self, obj):
        user = self.context.get('request').user
        if obj.buyer_id == user.id:
            return obj.buyer_is_maker
        return not obj.buyer_is_maker


class OrderBookEntrySerializer(serializers.Serializer):
    """Serializer for order book entries."""

    price = serializers.DecimalField(max_digits=36, decimal_places=18)
    quantity = serializers.DecimalField(max_digits=36, decimal_places=18)
    total = serializers.DecimalField(max_digits=36, decimal_places=18)
    order_count = serializers.IntegerField()


class OrderBookSerializer(serializers.Serializer):
    """Serializer for complete order book."""

    trading_pair = serializers.CharField()
    bids = OrderBookEntrySerializer(many=True)
    asks = OrderBookEntrySerializer(many=True)
    last_price = serializers.DecimalField(max_digits=36, decimal_places=18, allow_null=True)
    timestamp = serializers.DateTimeField()