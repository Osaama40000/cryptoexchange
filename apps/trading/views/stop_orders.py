"""
Stop Order API Views
"""
from decimal import Decimal, InvalidOperation
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from apps.trading.models import Order, TradingPair
from apps.trading.services import StopOrderService
from apps.trading.serializers import OrderSerializer


class StopLossOrderView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            symbol = request.data.get('symbol')
            side = request.data.get('side')
            quantity = Decimal(str(request.data.get('quantity', 0)))
            stop_price = Decimal(str(request.data.get('stop_price', 0)))
            limit_price = request.data.get('limit_price')
            
            if limit_price:
                limit_price = Decimal(str(limit_price))
            
            if not symbol or not side or quantity <= 0 or stop_price <= 0:
                return Response({'error': 'Invalid parameters'}, status=status.HTTP_400_BAD_REQUEST)
            
            trading_pair = get_object_or_404(TradingPair, symbol=symbol.upper(), is_active=True)
            
            order = StopOrderService.create_stop_loss_order(
                user=request.user,
                trading_pair=trading_pair,
                side=side.lower(),
                quantity=quantity,
                stop_price=stop_price,
                limit_price=limit_price
            )
            
            return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
        except (InvalidOperation, ValueError) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class TakeProfitOrderView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            symbol = request.data.get('symbol')
            side = request.data.get('side')
            quantity = Decimal(str(request.data.get('quantity', 0)))
            take_profit_price = Decimal(str(request.data.get('take_profit_price', 0)))
            limit_price = request.data.get('limit_price')
            
            if limit_price:
                limit_price = Decimal(str(limit_price))
            
            if not symbol or not side or quantity <= 0 or take_profit_price <= 0:
                return Response({'error': 'Invalid parameters'}, status=status.HTTP_400_BAD_REQUEST)
            
            trading_pair = get_object_or_404(TradingPair, symbol=symbol.upper(), is_active=True)
            
            order = StopOrderService.create_take_profit_order(
                user=request.user,
                trading_pair=trading_pair,
                side=side.lower(),
                quantity=quantity,
                take_profit_price=take_profit_price,
                limit_price=limit_price
            )
            
            return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
        except (InvalidOperation, ValueError) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class TrailingStopOrderView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            symbol = request.data.get('symbol')
            side = request.data.get('side')
            quantity = Decimal(str(request.data.get('quantity', 0)))
            trailing_percent = Decimal(str(request.data.get('trailing_percent', 0)))
            
            if not symbol or not side or quantity <= 0 or trailing_percent <= 0:
                return Response({'error': 'Invalid parameters'}, status=status.HTTP_400_BAD_REQUEST)
            
            if trailing_percent > 50:
                return Response({'error': 'Trailing percent cannot exceed 50%'}, status=status.HTTP_400_BAD_REQUEST)
            
            trading_pair = get_object_or_404(TradingPair, symbol=symbol.upper(), is_active=True)
            current_price = trading_pair.last_price or Decimal('0')
            
            if current_price <= 0:
                return Response({'error': 'No market price available'}, status=status.HTTP_400_BAD_REQUEST)
            
            order = StopOrderService.create_trailing_stop_order(
                user=request.user,
                trading_pair=trading_pair,
                side=side.lower(),
                quantity=quantity,
                trailing_percent=trailing_percent,
                current_price=current_price
            )
            
            return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
        except (InvalidOperation, ValueError) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class OCOOrderView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            symbol = request.data.get('symbol')
            side = request.data.get('side')
            quantity = Decimal(str(request.data.get('quantity', 0)))
            limit_price = Decimal(str(request.data.get('limit_price', 0)))
            stop_price = Decimal(str(request.data.get('stop_price', 0)))
            stop_limit_price = request.data.get('stop_limit_price')
            
            if stop_limit_price:
                stop_limit_price = Decimal(str(stop_limit_price))
            
            if not symbol or not side or quantity <= 0 or limit_price <= 0 or stop_price <= 0:
                return Response({'error': 'Invalid parameters'}, status=status.HTTP_400_BAD_REQUEST)
            
            trading_pair = get_object_or_404(TradingPair, symbol=symbol.upper(), is_active=True)
            
            limit_order, stop_order = StopOrderService.create_oco_order(
                user=request.user,
                trading_pair=trading_pair,
                side=side.lower(),
                quantity=quantity,
                limit_price=limit_price,
                stop_price=stop_price,
                stop_limit_price=stop_limit_price
            )
            
            return Response({
                'limit_order': OrderSerializer(limit_order).data,
                'stop_order': OrderSerializer(stop_order).data
            }, status=status.HTTP_201_CREATED)
        except (InvalidOperation, ValueError) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class StopOrderListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        symbol = request.query_params.get('symbol')
        trading_pair = None
        
        if symbol:
            trading_pair = get_object_or_404(TradingPair, symbol=symbol.upper())
        
        orders = StopOrderService.get_user_stop_orders(user=request.user, trading_pair=trading_pair)
        return Response(OrderSerializer(orders, many=True).data)


class CancelStopOrderView(APIView):
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, order_id):
        order = get_object_or_404(Order, id=order_id, user=request.user)
        
        if not order.is_stop_order:
            return Response({'error': 'Not a stop order'}, status=status.HTTP_400_BAD_REQUEST)
        
        if StopOrderService.cancel_stop_order(order):
            return Response({'message': 'Order cancelled'})
        return Response({'error': 'Cannot cancel order'}, status=status.HTTP_400_BAD_REQUEST)
