"""
Trading WebSocket Consumers
===========================
Real-time data streaming for order book, trades, and user updates.
"""

import json
import logging
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async

logger = logging.getLogger('apps.trading')


class OrderBookConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for real-time order book updates.

    Connect: ws://localhost:8000/ws/orderbook/ETH_USDT/
    """

    async def connect(self):
        self.symbol = self.scope['url_route']['kwargs']['symbol'].upper()
        self.room_group_name = f'orderbook_{self.symbol}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # Send initial order book
        order_book = await self.get_order_book()
        await self.send_json({
            'type': 'orderbook_snapshot',
            'data': order_book
        })

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive_json(self, content):
        """Handle incoming messages (e.g., subscription changes)."""
        message_type = content.get('type')

        if message_type == 'ping':
            await self.send_json({'type': 'pong'})

    async def orderbook_update(self, event):
        """Send order book update to WebSocket."""
        await self.send_json({
            'type': 'orderbook_update',
            'data': event['data']
        })

    @database_sync_to_async
    def get_order_book(self):
        from apps.trading.models import TradingPair
        from apps.trading.services.order_book import OrderBookService

        try:
            trading_pair = TradingPair.objects.get(symbol=self.symbol, is_active=True)
            return OrderBookService.get_order_book(trading_pair)
        except TradingPair.DoesNotExist:
            return {'error': 'Trading pair not found'}


class TradeConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for real-time trade updates.

    Connect: ws://localhost:8000/ws/trades/ETH_USDT/
    """

    async def connect(self):
        self.symbol = self.scope['url_route']['kwargs']['symbol'].upper()
        self.room_group_name = f'trades_{self.symbol}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # Send recent trades
        trades = await self.get_recent_trades()
        await self.send_json({
            'type': 'trades_snapshot',
            'data': trades
        })

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive_json(self, content):
        message_type = content.get('type')

        if message_type == 'ping':
            await self.send_json({'type': 'pong'})

    async def trade_update(self, event):
        """Send new trade to WebSocket."""
        await self.send_json({
            'type': 'new_trade',
            'data': event['data']
        })

    @database_sync_to_async
    def get_recent_trades(self):
        from apps.trading.models import Trade

        trades = Trade.objects.filter(
            trading_pair__symbol=self.symbol
        ).order_by('-created_at')[:50]

        return [
            {
                'id': str(t.id),
                'price': str(t.price),
                'quantity': str(t.quantity),
                'side': 'buy' if t.buyer_is_maker else 'sell',
                'timestamp': t.created_at.isoformat()
            }
            for t in trades
        ]


class UserConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for user-specific updates.

    Connect: ws://localhost:8000/ws/user/

    Sends:
    - Order updates (created, filled, cancelled)
    - Balance updates
    - Trade notifications
    """

    async def connect(self):
        user = self.scope.get('user')

        if not user or not user.is_authenticated:
            await self.close()
            return

        self.user_id = str(user.id)
        self.room_group_name = f'user_{self.user_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        await self.send_json({
            'type': 'connected',
            'message': 'Connected to user updates'
        })

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive_json(self, content):
        message_type = content.get('type')

        if message_type == 'ping':
            await self.send_json({'type': 'pong'})

    async def order_update(self, event):
        """Send order update to user."""
        await self.send_json({
            'type': 'order_update',
            'data': event['data']
        })

    async def balance_update(self, event):
        """Send balance update to user."""
        await self.send_json({
            'type': 'balance_update',
            'data': event['data']
        })

    async def trade_notification(self, event):
        """Send trade notification to user."""
        await self.send_json({
            'type': 'trade_notification',
            'data': event['data']
        })