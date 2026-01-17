"""
Trading Celery Tasks
====================
"""

import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Min, Max

logger = logging.getLogger('apps.trading')


@shared_task(name='apps.trading.tasks.update_trading_pair_stats')
def update_trading_pair_stats():
    """
    Update 24h statistics for all trading pairs.
    Runs every minute.
    """
    from apps.trading.models import TradingPair, Trade

    logger.info("Updating trading pair statistics...")

    now = timezone.now()
    yesterday = now - timedelta(hours=24)

    pairs = TradingPair.objects.filter(is_active=True)

    for pair in pairs:
        try:
            # Get 24h trades
            trades_24h = Trade.objects.filter(
                trading_pair=pair,
                created_at__gte=yesterday
            )

            if trades_24h.exists():
                stats = trades_24h.aggregate(
                    volume=Sum('quantity'),
                    high=Max('price'),
                    low=Min('price')
                )

                pair.volume_24h = stats['volume']
                pair.high_24h = stats['high']
                pair.low_24h = stats['low']

                # Calculate price change
                first_trade = trades_24h.order_by('created_at').first()
                if first_trade and pair.last_price:
                    old_price = first_trade.price
                    new_price = pair.last_price
                    if old_price > 0:
                        pair.price_change_24h = ((new_price - old_price) / old_price) * 100

                pair.save(update_fields=[
                    'volume_24h', 'high_24h', 'low_24h',
                    'price_change_24h', 'updated_at'
                ])

        except Exception as e:
            logger.error(f"Error updating stats for {pair.symbol}: {e}")

    logger.info(f"Updated statistics for {pairs.count()} trading pairs")

    return {'status': 'completed', 'pairs_updated': pairs.count()}