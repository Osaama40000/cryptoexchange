"""
Order Book Service
==================
Manages order book data and aggregation.
"""

import logging
from decimal import Decimal
from typing import List, Dict
from django.db.models import Sum, Count
from django.utils import timezone
from django.core.cache import cache

from apps.trading.models import TradingPair, Order

logger = logging.getLogger('apps.trading')


class OrderBookService:
    """
    Service for managing and querying order books.
    """

    CACHE_TTL = 5  # Cache order book for 5 seconds

    @staticmethod
    def get_order_book(trading_pair: TradingPair, depth: int = 50) -> Dict:
        """
        Get the current order book for a trading pair.

        Args:
            trading_pair: The trading pair
            depth: Number of price levels to return

        Returns:
            Dict with bids, asks, and metadata
        """
        cache_key = f"orderbook:{trading_pair.symbol}:{depth}"
        cached = cache.get(cache_key)

        if cached:
            return cached

        # Get aggregated bids (buy orders) - highest price first
        bids = Order.objects.filter(
            trading_pair=trading_pair,
            side='buy',
            status__in=['open', 'partial'],
            price__isnull=False
        ).values('price').annotate(
            quantity=Sum('quantity') - Sum('filled_quantity'),
            order_count=Count('id')
        ).order_by('-price')[:depth]

        # Get aggregated asks (sell orders) - lowest price first
        asks = Order.objects.filter(
            trading_pair=trading_pair,
            side='sell',
            status__in=['open', 'partial'],
            price__isnull=False
        ).values('price').annotate(
            quantity=Sum('quantity') - Sum('filled_quantity'),
            order_count=Count('id')
        ).order_by('price')[:depth]

        # Calculate running totals
        bid_list = []
        running_total = Decimal('0')
        for bid in bids:
            running_total += bid['quantity']
            bid_list.append({
                'price': str(bid['price']),
                'quantity': str(bid['quantity']),
                'total': str(running_total),
                'order_count': bid['order_count']
            })

        ask_list = []
        running_total = Decimal('0')
        for ask in asks:
            running_total += ask['quantity']
            ask_list.append({
                'price': str(ask['price']),
                'quantity': str(ask['quantity']),
                'total': str(running_total),
                'order_count': ask['order_count']
            })

        order_book = {
            'trading_pair': trading_pair.symbol,
            'bids': bid_list,
            'asks': ask_list,
            'last_price': str(trading_pair.last_price) if trading_pair.last_price else None,
            'timestamp': timezone.now().isoformat()
        }

        # Cache the result
        cache.set(cache_key, order_book, OrderBookService.CACHE_TTL)

        return order_book

    @staticmethod
    def get_best_bid(trading_pair: TradingPair) -> Order:
        """Get the highest buy order."""
        return Order.objects.filter(
            trading_pair=trading_pair,
            side='buy',
            status__in=['open', 'partial'],
            price__isnull=False
        ).order_by('-price', 'created_at').first()

    @staticmethod
    def get_best_ask(trading_pair: TradingPair) -> Order:
        """Get the lowest sell order."""
        return Order.objects.filter(
            trading_pair=trading_pair,
            side='sell',
            status__in=['open', 'partial'],
            price__isnull=False
        ).order_by('price', 'created_at').first()

    @staticmethod
    def get_spread(trading_pair: TradingPair) -> Dict:
        """Get bid-ask spread."""
        best_bid = OrderBookService.get_best_bid(trading_pair)
        best_ask = OrderBookService.get_best_ask(trading_pair)

        spread = None
        spread_percentage = None

        if best_bid and best_ask:
            spread = best_ask.price - best_bid.price
            mid_price = (best_ask.price + best_bid.price) / 2
            if mid_price > 0:
                spread_percentage = (spread / mid_price) * 100

        return {
            'best_bid': str(best_bid.price) if best_bid else None,
            'best_ask': str(best_ask.price) if best_ask else None,
            'spread': str(spread) if spread else None,
            'spread_percentage': str(spread_percentage) if spread_percentage else None
        }

    @staticmethod
    def get_matching_orders(
            trading_pair: TradingPair,
            side: str,
            price: Decimal = None,
            is_market_order: bool = False
    ) -> List[Order]:
        """
        Get orders that can match with a new order.

        Args:
            trading_pair: The trading pair
            side: Side of the NEW order (buy/sell)
            price: Price of the new order (for limit orders)
            is_market_order: Whether the new order is a market order

        Returns:
            List of matching orders, sorted by price-time priority
        """
        # Opposite side orders
        opposite_side = 'sell' if side == 'buy' else 'buy'

        queryset = Order.objects.filter(
            trading_pair=trading_pair,
            side=opposite_side,
            status__in=['open', 'partial'],
            price__isnull=False
        )

        if not is_market_order and price:
            if side == 'buy':
                # Buy order matches with sells at or below the buy price
                queryset = queryset.filter(price__lte=price)
            else:
                # Sell order matches with buys at or above the sell price
                queryset = queryset.filter(price__gte=price)

        # Order by price (best price first) then by time (oldest first)
        if opposite_side == 'sell':
            queryset = queryset.order_by('price', 'created_at')
        else:
            queryset = queryset.order_by('-price', 'created_at')

        return list(queryset)

    @staticmethod
    def invalidate_cache(trading_pair_symbol: str):
        """Invalidate order book cache for a trading pair."""
        for depth in [10, 20, 50, 100]:
            cache_key = f"orderbook:{trading_pair_symbol}:{depth}"
            cache.delete(cache_key)