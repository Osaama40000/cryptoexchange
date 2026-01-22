"""
Order Matching Engine
"""
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from apps.trading.models import Order, Trade, TradingPair


class MatchingEngine:
    """Simple order matching engine"""
    
    @classmethod
    def create_order(cls, user, trading_pair, order_type, side, quantity, 
                     price=None, time_in_force='gtc', client_order_id=None):
        """Create and attempt to match an order"""
        
        with transaction.atomic():
            order = Order.objects.create(
                user=user,
                trading_pair=trading_pair,
                order_type=order_type,
                side=side,
                quantity=quantity,
                price=price,
                time_in_force=time_in_force,
                client_order_id=client_order_id or '',
                status=Order.Status.OPEN
            )
            
            trades = []
            if order_type == Order.OrderType.MARKET or order_type == Order.OrderType.LIMIT:
                trades = cls.match_order(order)
            
            return order, trades
    
    @classmethod
    def match_order(cls, order):
        """Attempt to match an order against the order book"""
        trades = []
        
        if order.side == Order.Side.BUY:
            # Match against sell orders (asks)
            opposite_orders = Order.objects.filter(
                trading_pair=order.trading_pair,
                side=Order.Side.SELL,
                status__in=[Order.Status.OPEN, Order.Status.PARTIALLY_FILLED]
            ).order_by('price', 'created_at')
            
            if order.order_type == Order.OrderType.LIMIT:
                opposite_orders = opposite_orders.filter(price__lte=order.price)
        else:
            # Match against buy orders (bids)
            opposite_orders = Order.objects.filter(
                trading_pair=order.trading_pair,
                side=Order.Side.BUY,
                status__in=[Order.Status.OPEN, Order.Status.PARTIALLY_FILLED]
            ).order_by('-price', 'created_at')
            
            if order.order_type == Order.OrderType.LIMIT:
                opposite_orders = opposite_orders.filter(price__gte=order.price)
        
        for opposite_order in opposite_orders:
            if order.remaining_quantity <= 0:
                break
            
            trade = cls._execute_trade(order, opposite_order)
            if trade:
                trades.append(trade)
        
        return trades
    
    @classmethod
    def _execute_trade(cls, taker_order, maker_order):
        """Execute a trade between two orders"""
        trade_quantity = min(taker_order.remaining_quantity, maker_order.remaining_quantity)
        trade_price = maker_order.price  # Maker's price
        
        if trade_quantity <= 0:
            return None
        
        # Determine buyer and seller
        if taker_order.side == Order.Side.BUY:
            buyer_order = taker_order
            seller_order = maker_order
        else:
            buyer_order = maker_order
            seller_order = taker_order
        
        # Calculate fees
        fee_rate = taker_order.trading_pair.taker_fee
        buyer_fee = trade_quantity * fee_rate
        seller_fee = (trade_quantity * trade_price) * fee_rate
        
        # Create trade
        trade = Trade.objects.create(
            trading_pair=taker_order.trading_pair,
            buyer_order=buyer_order,
            seller_order=seller_order,
            buyer=buyer_order.user,
            seller=seller_order.user,
            price=trade_price,
            quantity=trade_quantity,
            buyer_fee=buyer_fee,
            seller_fee=seller_fee,
            is_buyer_maker=(buyer_order == maker_order)
        )
        
        # Update orders
        for order in [taker_order, maker_order]:
            order.filled_quantity += trade_quantity
            if order.filled_quantity >= order.quantity:
                order.status = Order.Status.FILLED
            else:
                order.status = Order.Status.PARTIALLY_FILLED
            order.save()
        
        # Update trading pair last price
        taker_order.trading_pair.last_price = trade_price
        taker_order.trading_pair.save(update_fields=['last_price'])
        
        return trade
    
    @classmethod
    def cancel_order(cls, order):
        """Cancel an order"""
        if order.status not in [Order.Status.OPEN, Order.Status.PARTIALLY_FILLED, Order.Status.PENDING]:
            raise ValueError(f"Cannot cancel order with status {order.status}")
        
        order.status = Order.Status.CANCELLED
        order.save()
        return order
