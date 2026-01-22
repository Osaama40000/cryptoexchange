"""
Order Book Service
"""
from decimal import Decimal
from django.db.models import Sum
from django.utils import timezone
from apps.trading.models import Order, TradingPair


class OrderBookService:
    """Service for order book operations"""
    
    @classmethod
    def get_order_book(cls, trading_pair, depth=50):
        """Get order book for a trading pair"""
        
        # Get bids (buy orders) - highest price first
        bids = Order.objects.filter(
            trading_pair=trading_pair,
            side=Order.Side.BUY,
            status__in=[Order.Status.OPEN, Order.Status.PARTIALLY_FILLED],
            order_type=Order.OrderType.LIMIT
        ).values('price').annotate(
            quantity=Sum('quantity') - Sum('filled_quantity')
        ).order_by('-price')[:depth]
        
        # Get asks (sell orders) - lowest price first
        asks = Order.objects.filter(
            trading_pair=trading_pair,
            side=Order.Side.SELL,
            status__in=[Order.Status.OPEN, Order.Status.PARTIALLY_FILLED],
            order_type=Order.OrderType.LIMIT
        ).values('price').annotate(
            quantity=Sum('quantity') - Sum('filled_quantity')
        ).order_by('price')[:depth]
        
        # Format response
        def format_level(level):
            price = level['price']
            quantity = level['quantity']
            return {
                'price': str(price),
                'quantity': str(quantity),
                'total': str(price * quantity)
            }
        
        return {
            'symbol': trading_pair.symbol,
            'bids': [format_level(b) for b in bids],
            'asks': [format_level(a) for a in asks],
            'last_price': str(trading_pair.last_price) if trading_pair.last_price else None,
            'timestamp': timezone.now().isoformat()
        }
    
    @classmethod
    def get_spread(cls, trading_pair):
        """Get best bid, ask and spread"""
        best_bid = Order.objects.filter(
            trading_pair=trading_pair,
            side=Order.Side.BUY,
            status__in=[Order.Status.OPEN, Order.Status.PARTIALLY_FILLED],
            order_type=Order.OrderType.LIMIT
        ).order_by('-price').values_list('price', flat=True).first()
        
        best_ask = Order.objects.filter(
            trading_pair=trading_pair,
            side=Order.Side.SELL,
            status__in=[Order.Status.OPEN, Order.Status.PARTIALLY_FILLED],
            order_type=Order.OrderType.LIMIT
        ).order_by('price').values_list('price', flat=True).first()
        
        spread = None
        if best_bid and best_ask:
            spread = str(best_ask - best_bid)
        
        return {
            'best_bid': str(best_bid) if best_bid else None,
            'best_ask': str(best_ask) if best_ask else None,
            'spread': spread
        }
