"""
Trading Views
=============
API endpoints for order management and market data.
"""

import logging
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Q

from .models import TradingPair, Order, Trade
from .serializers import (
    TradingPairSerializer,
    OrderSerializer,
    CreateOrderSerializer,
    TradeSerializer,
    UserTradeSerializer,
)
from .services.matching_engine import MatchingEngine
from .services.order_book import OrderBookService

logger = logging.getLogger(__name__)


# =============================================================================
# MARKET DATA ENDPOINTS (Public)
# =============================================================================

class TradingPairListView(generics.ListAPIView):
    """
    GET /api/v1/trading/pairs/

    List all active trading pairs.
    """
    serializer_class = TradingPairSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return TradingPair.objects.filter(is_active=True)


class TradingPairDetailView(generics.RetrieveAPIView):
    """
    GET /api/v1/trading/pairs/<symbol>/

    Get details of a specific trading pair.
    """
    serializer_class = TradingPairSerializer
    permission_classes = [AllowAny]
    lookup_field = 'symbol'

    def get_queryset(self):
        return TradingPair.objects.filter(is_active=True)


class OrderBookView(APIView):
    """
    GET /api/v1/trading/orderbook/<symbol>/

    Get order book for a trading pair.
    """
    permission_classes = [AllowAny]

    def get(self, request, symbol):
        try:
            trading_pair = TradingPair.objects.get(symbol=symbol.upper(), is_active=True)
        except TradingPair.DoesNotExist:
            return Response(
                {'error': 'Trading pair not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        depth = int(request.query_params.get('depth', 50))
        depth = min(depth, 100)

        order_book = OrderBookService.get_order_book(trading_pair, depth)

        return Response(order_book)


class RecentTradesView(generics.ListAPIView):
    """
    GET /api/v1/trading/trades/<symbol>/

    Get recent trades for a trading pair.
    """
    serializer_class = TradeSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        symbol = self.kwargs.get('symbol', '').upper()
        return Trade.objects.filter(
            trading_pair__symbol=symbol
        ).order_by('-created_at')[:100]


class TickerView(APIView):
    """
    GET /api/v1/trading/ticker/
    GET /api/v1/trading/ticker/<symbol>/

    Get 24h ticker data.
    """
    permission_classes = [AllowAny]

    def get(self, request, symbol=None):
        if symbol:
            try:
                pair = TradingPair.objects.get(symbol=symbol.upper(), is_active=True)
                return Response(self._get_ticker_data(pair))
            except TradingPair.DoesNotExist:
                return Response(
                    {'error': 'Trading pair not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            pairs = TradingPair.objects.filter(is_active=True)
            return Response([self._get_ticker_data(p) for p in pairs])

    def _get_ticker_data(self, pair):
        spread = OrderBookService.get_spread(pair)
        return {
            'symbol': pair.symbol,
            'last_price': str(pair.last_price) if pair.last_price else None,
            'price_change_24h': str(pair.price_change_24h) if pair.price_change_24h else None,
            'high_24h': str(pair.high_24h) if pair.high_24h else None,
            'low_24h': str(pair.low_24h) if pair.low_24h else None,
            'volume_24h': str(pair.volume_24h) if pair.volume_24h else None,
            'best_bid': spread['best_bid'],
            'best_ask': spread['best_ask'],
            'spread': spread['spread'],
        }


# =============================================================================
# ORDER MANAGEMENT ENDPOINTS (Authenticated)
# =============================================================================

class CreateOrderView(APIView):
    """
    POST /api/v1/trading/orders/create/

    Create a new order.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreateOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            order, trades = MatchingEngine.create_order(
                user=request.user,
                trading_pair=serializer.validated_data['trading_pair'],
                order_type=serializer.validated_data['order_type'],
                side=serializer.validated_data['side'],
                quantity=serializer.validated_data['quantity'],
                price=serializer.validated_data.get('price'),
                time_in_force=serializer.validated_data['time_in_force'],
                client_order_id=serializer.validated_data.get('client_order_id')
            )

            # Send email notification if order was filled (has trades)
            if trades and len(trades) > 0:
                try:
                    from emails.notifications import notify_order_filled
                    notify_order_filled(request.user, order)
                    logger.info(f"Order filled email sent to {request.user.email}")
                except Exception as e:
                    logger.error(f"Failed to send order filled email: {e}")

            return Response({
                'message': 'Order created successfully',
                'order': OrderSerializer(order).data,
                'trades': TradeSerializer(trades, many=True).data,
                'trades_count': len(trades)
            }, status=status.HTTP_201_CREATED)

        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class CancelOrderView(APIView):
    """
    POST /api/v1/trading/orders/<order_id>/cancel/

    Cancel an open order.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response(
                {'error': 'Order not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            order = MatchingEngine.cancel_order(order)
            return Response({
                'message': 'Order cancelled successfully',
                'order': OrderSerializer(order).data
            })
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class UserOrdersView(generics.ListAPIView):
    """
    GET /api/v1/trading/orders/

    Get all orders for the current user.
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Order.objects.filter(user=self.request.user)

        # Filter by status
        order_status = self.request.query_params.get('status')
        if order_status:
            queryset = queryset.filter(status=order_status)

        # Filter by symbol
        symbol = self.request.query_params.get('symbol')
        if symbol:
            queryset = queryset.filter(trading_pair__symbol=symbol.upper())

        # Filter by side
        side = self.request.query_params.get('side')
        if side:
            queryset = queryset.filter(side=side)

        return queryset.order_by('-created_at')


class UserOpenOrdersView(generics.ListAPIView):
    """
    GET /api/v1/trading/orders/open/

    Get open orders for the current user.
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(
            user=self.request.user,
            status__in=['pending', 'partially_filled']
        ).order_by('-created_at')


class UserTradesView(generics.ListAPIView):
    """
    GET /api/v1/trading/user-trades/

    Get trade history for the current user.
    """
    serializer_class = UserTradeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Trade.objects.filter(
            Q(maker_order__user=self.request.user) |
            Q(taker_order__user=self.request.user)
        ).order_by('-created_at')
