"""
Trading serializers
"""
from rest_framework import serializers
from .models import TradingPair, Order, Trade


class TradingPairSerializer(serializers.ModelSerializer):
    class Meta:
        model = TradingPair
        fields = [
            'id', 'symbol', 'base_currency', 'quote_currency',
            'min_quantity', 'max_quantity', 'quantity_step',
            'min_price', 'max_price', 'price_step', 'min_notional',
            'maker_fee', 'taker_fee', 'is_active',
            'last_price', 'price_change_24h', 'high_24h', 'low_24h', 'volume_24h',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class OrderSerializer(serializers.ModelSerializer):
    symbol = serializers.CharField(source='trading_pair.symbol', read_only=True)
    remaining_quantity = serializers.DecimalField(max_digits=20, decimal_places=8, read_only=True)
    is_stop_order = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'symbol', 'order_type', 'side', 'status', 'time_in_force',
            'quantity', 'price', 'filled_quantity', 'remaining_quantity',
            'average_fill_price', 'fee', 'fee_currency',
            'stop_price', 'take_profit_price', 'stop_loss_price',
            'trailing_stop_percent', 'highest_price_seen', 'lowest_price_seen',
            'triggered_at', 'is_stop_order',
            'client_order_id', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'status', 'filled_quantity', 'average_fill_price',
            'fee', 'fee_currency', 'highest_price_seen', 'lowest_price_seen',
            'triggered_at', 'created_at', 'updated_at'
        ]


class OrderCreateSerializer(serializers.Serializer):
    symbol = serializers.CharField(max_length=20)
    side = serializers.ChoiceField(choices=Order.Side.choices)
    order_type = serializers.ChoiceField(choices=Order.OrderType.choices, default=Order.OrderType.LIMIT)
    quantity = serializers.DecimalField(max_digits=20, decimal_places=8)
    price = serializers.DecimalField(max_digits=20, decimal_places=8, required=False, allow_null=True)
    time_in_force = serializers.ChoiceField(choices=Order.TimeInForce.choices, default=Order.TimeInForce.GTC)
    client_order_id = serializers.CharField(max_length=50, required=False, allow_blank=True)
    
    def validate(self, data):
        # Get trading pair
        try:
            data['trading_pair'] = TradingPair.objects.get(symbol=data['symbol'].upper(), is_active=True)
        except TradingPair.DoesNotExist:
            raise serializers.ValidationError({'symbol': 'Trading pair not found or inactive'})
        return data


class TradeSerializer(serializers.ModelSerializer):
    symbol = serializers.CharField(source='trading_pair.symbol', read_only=True)
    total = serializers.DecimalField(max_digits=30, decimal_places=8, read_only=True)
    
    class Meta:
        model = Trade
        fields = [
            'id', 'symbol', 'price', 'quantity', 'total',
            'buyer_fee', 'seller_fee', 'is_buyer_maker',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class UserTradeSerializer(serializers.ModelSerializer):
    """Serializer for user's trade history"""
    symbol = serializers.CharField(source='trading_pair.symbol', read_only=True)
    total = serializers.DecimalField(max_digits=30, decimal_places=8, read_only=True)
    side = serializers.SerializerMethodField()
    fee = serializers.SerializerMethodField()
    
    class Meta:
        model = Trade
        fields = [
            'id', 'symbol', 'side', 'price', 'quantity', 'total',
            'fee', 'is_buyer_maker', 'created_at'
        ]
    
    def get_side(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            if obj.buyer == request.user:
                return 'buy'
            return 'sell'
        return None
    
    def get_fee(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            if obj.buyer == request.user:
                return str(obj.buyer_fee)
            return str(obj.seller_fee)
        return None


class OrderBookEntrySerializer(serializers.Serializer):
    price = serializers.DecimalField(max_digits=20, decimal_places=8)
    quantity = serializers.DecimalField(max_digits=20, decimal_places=8)
    total = serializers.DecimalField(max_digits=30, decimal_places=8)


class OrderBookSerializer(serializers.Serializer):
    symbol = serializers.CharField()
    bids = OrderBookEntrySerializer(many=True)
    asks = OrderBookEntrySerializer(many=True)
    last_price = serializers.DecimalField(max_digits=20, decimal_places=8)
    timestamp = serializers.DateTimeField()
