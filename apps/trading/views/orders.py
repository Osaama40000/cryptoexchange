"""
Trading Views
"""
import logging
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Q

from apps.trading.models import TradingPair, Order, Trade
from apps.trading.serializers import (
    TradingPairSerializer,
    OrderSerializer,
    OrderCreateSerializer,
    TradeSerializer,
    UserTradeSerializer,
)
from apps.trading.services import MatchingEngine, OrderBookService

logger = logging.getLogger(__name__)


class TradingPairListView(generics.ListAPIView):
    serializer_class = TradingPairSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        return TradingPair.objects.filter(is_active=True)


class TradingPairDetailView(generics.RetrieveAPIView):
    serializer_class = TradingPairSerializer
    permission_classes = [AllowAny]
    lookup_field = 'symbol'
    
    def get_queryset(self):
        return TradingPair.objects.filter(is_active=True)


class OrderBookView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request, symbol):
        try:
            trading_pair = TradingPair.objects.get(symbol=symbol.upper(), is_active=True)
        except TradingPair.DoesNotExist:
            return Response({'error': 'Trading pair not found'}, status=status.HTTP_404_NOT_FOUND)
        
        depth = min(int(request.query_params.get('depth', 50)), 100)
        order_book = OrderBookService.get_order_book(trading_pair, depth)
        return Response(order_book)


class OrderListCreateView(generics.ListCreateAPIView):
    """List and create orders"""
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return OrderCreateSerializer
        return OrderSerializer
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')
    
    def create(self, request, *args, **kwargs):
        serializer = OrderCreateSerializer(data=request.data)
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
            
            return Response({
                'order': OrderSerializer(order).data,
                'trades': TradeSerializer(trades, many=True).data,
            }, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)


class OrderCancelView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        try:
            order = Order.objects.get(id=pk, user=request.user)
            order = MatchingEngine.cancel_order(order)
            return Response({'message': 'Order cancelled', 'order': OrderSerializer(order).data})
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class TradeListView(generics.ListAPIView):
    serializer_class = TradeSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        symbol = self.request.query_params.get('symbol')
        queryset = Trade.objects.all().order_by('-created_at')[:100]
        if symbol:
            queryset = queryset.filter(trading_pair__symbol=symbol.upper())
        return queryset


class TradeDetailView(generics.RetrieveAPIView):
    serializer_class = TradeSerializer
    permission_classes = [AllowAny]
    queryset = Trade.objects.all()
