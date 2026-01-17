"""
Trading WebSocket Routing
=========================
"""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/orderbook/(?P<symbol>\w+)/$', consumers.OrderBookConsumer.as_asgi()),
    re_path(r'ws/trades/(?P<symbol>\w+)/$', consumers.TradeConsumer.as_asgi()),
    re_path(r'ws/user/$', consumers.UserConsumer.as_asgi()),
]