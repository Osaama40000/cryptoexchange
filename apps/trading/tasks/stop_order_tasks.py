"""
Celery tasks for stop order processing
"""
from celery import shared_task
from decimal import Decimal
from django.utils import timezone

from apps.trading.models import Order, TradingPair
from apps.trading.services import StopOrderService


@shared_task
def check_stop_orders():
    """
    Periodic task to check and trigger stop orders
    
    This should run frequently (e.g., every few seconds) to ensure
    stop orders are triggered promptly when price conditions are met.
    """
    active_pairs = TradingPair.objects.filter(is_active=True, last_price__gt=0)
    
    triggered_count = 0
    for pair in active_pairs:
        triggered = StopOrderService.check_and_trigger_stops(
            trading_pair=pair,
            current_price=pair.last_price
        )
        triggered_count += len(triggered)
    
    return f"Checked {active_pairs.count()} pairs, triggered {triggered_count} orders"


@shared_task
def process_triggered_orders():
    """
    Process orders that have been triggered and are now ready to execute
    """
    from apps.trading.services import MatchingEngine
    
    triggered_orders = Order.objects.filter(
        status=Order.Status.OPEN,
        triggered_at__isnull=False
    ).order_by('triggered_at')
    
    processed = 0
    for order in triggered_orders:
        try:
            MatchingEngine.match_order(order)
            processed += 1
        except Exception as e:
            # Log error but continue processing other orders
            print(f"Error processing triggered order {order.id}: {e}")
    
    return f"Processed {processed} triggered orders"


@shared_task
def update_trailing_stops(symbol: str, current_price: str):
    """
    Update trailing stop orders when price changes
    
    This should be called whenever a trade occurs
    """
    try:
        trading_pair = TradingPair.objects.get(symbol=symbol)
        price = Decimal(current_price)
        
        triggered = StopOrderService.check_and_trigger_stops(
            trading_pair=trading_pair,
            current_price=price
        )
        
        return f"Updated trailing stops for {symbol}, triggered {len(triggered)} orders"
    except TradingPair.DoesNotExist:
        return f"Trading pair {symbol} not found"
