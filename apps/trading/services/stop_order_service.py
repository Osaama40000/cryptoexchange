"""
Stop Order Service
"""
from decimal import Decimal
from typing import List, Optional
from django.db import transaction
from django.utils import timezone
from apps.trading.models import Order, TradingPair


class StopOrderService:
    """Service to manage stop-loss, take-profit, and trailing stop orders"""
    
    @classmethod
    def create_stop_loss_order(cls, user, trading_pair, side, quantity, stop_price, limit_price=None):
        """Create a stop-loss order"""
        order_type = Order.OrderType.STOP_LIMIT if limit_price else Order.OrderType.STOP_LOSS
        
        return Order.objects.create(
            user=user,
            trading_pair=trading_pair,
            order_type=order_type,
            side=side,
            status=Order.Status.PENDING,
            quantity=quantity,
            price=limit_price,
            stop_price=stop_price,
        )
    
    @classmethod
    def create_take_profit_order(cls, user, trading_pair, side, quantity, take_profit_price, limit_price=None):
        """Create a take-profit order"""
        order_type = Order.OrderType.TAKE_PROFIT_LIMIT if limit_price else Order.OrderType.TAKE_PROFIT
        
        return Order.objects.create(
            user=user,
            trading_pair=trading_pair,
            order_type=order_type,
            side=side,
            status=Order.Status.PENDING,
            quantity=quantity,
            price=limit_price,
            take_profit_price=take_profit_price,
        )
    
    @classmethod
    def create_trailing_stop_order(cls, user, trading_pair, side, quantity, trailing_percent, current_price):
        """Create a trailing stop order"""
        return Order.objects.create(
            user=user,
            trading_pair=trading_pair,
            order_type=Order.OrderType.TRAILING_STOP,
            side=side,
            status=Order.Status.PENDING,
            quantity=quantity,
            trailing_stop_percent=trailing_percent,
            highest_price_seen=current_price if side == Order.Side.SELL else None,
            lowest_price_seen=current_price if side == Order.Side.BUY else None,
        )
    
    @classmethod
    def create_oco_order(cls, user, trading_pair, side, quantity, limit_price, stop_price, stop_limit_price=None):
        """Create OCO order pair"""
        with transaction.atomic():
            limit_order = Order.objects.create(
                user=user,
                trading_pair=trading_pair,
                order_type=Order.OrderType.LIMIT,
                side=side,
                status=Order.Status.OPEN,
                quantity=quantity,
                price=limit_price,
            )
            
            stop_type = Order.OrderType.STOP_LIMIT if stop_limit_price else Order.OrderType.STOP_LOSS
            stop_order = Order.objects.create(
                user=user,
                trading_pair=trading_pair,
                order_type=stop_type,
                side=side,
                status=Order.Status.PENDING,
                quantity=quantity,
                price=stop_limit_price,
                stop_price=stop_price,
                parent_order=limit_order,
            )
            
            limit_order.parent_order = stop_order
            limit_order.save(update_fields=['parent_order'])
            
            return limit_order, stop_order
    
    @classmethod
    def check_and_trigger_stops(cls, trading_pair, current_price):
        """Check and trigger stop orders"""
        triggered = []
        pending_stops = Order.objects.filter(
            trading_pair=trading_pair,
            status=Order.Status.PENDING,
            order_type__in=[
                Order.OrderType.STOP_LOSS,
                Order.OrderType.STOP_LIMIT,
                Order.OrderType.TAKE_PROFIT,
                Order.OrderType.TAKE_PROFIT_LIMIT,
                Order.OrderType.TRAILING_STOP,
            ]
        ).select_for_update()
        
        with transaction.atomic():
            for order in pending_stops:
                if order.should_trigger(current_price):
                    order.trigger()
                    triggered.append(order)
        
        return triggered
    
    @classmethod
    def cancel_stop_order(cls, order):
        """Cancel a stop order"""
        if order.status != Order.Status.PENDING:
            return False
        order.status = Order.Status.CANCELLED
        order.save(update_fields=['status'])
        return True
    
    @classmethod
    def get_user_stop_orders(cls, user, trading_pair=None):
        """Get user's pending stop orders"""
        queryset = Order.objects.filter(
            user=user,
            status=Order.Status.PENDING,
            order_type__in=[
                Order.OrderType.STOP_LOSS,
                Order.OrderType.STOP_LIMIT,
                Order.OrderType.TAKE_PROFIT,
                Order.OrderType.TAKE_PROFIT_LIMIT,
                Order.OrderType.TRAILING_STOP,
            ]
        )
        if trading_pair:
            queryset = queryset.filter(trading_pair=trading_pair)
        return list(queryset)
