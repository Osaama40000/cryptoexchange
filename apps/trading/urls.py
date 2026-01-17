"""
Trading URL Configuration
=========================
"""

from django.urls import path

from .views import (
    TradingPairListView,
    TradingPairDetailView,
    OrderBookView,
    RecentTradesView,
    TickerView,
    CreateOrderView,
    CancelOrderView,
    UserOrdersView,
    UserOpenOrdersView,
    UserTradesView,
)

app_name = 'trading'

urlpatterns = [
    # Market Data (Public)
    path('pairs/', TradingPairListView.as_view(), name='pair_list'),
    path('pairs/<str:symbol>/', TradingPairDetailView.as_view(), name='pair_detail'),
    path('orderbook/<str:symbol>/', OrderBookView.as_view(), name='orderbook'),
    path('trades/<str:symbol>/', RecentTradesView.as_view(), name='recent_trades'),
    path('ticker/', TickerView.as_view(), name='ticker_all'),
    path('ticker/<str:symbol>/', TickerView.as_view(), name='ticker'),

    # Order Management (Authenticated)
    path('orders/', UserOrdersView.as_view(), name='user_orders'),
    path('orders/create/', CreateOrderView.as_view(), name='create_order'),
    path('orders/open/', UserOpenOrdersView.as_view(), name='user_open_orders'),
    path('orders/<uuid:order_id>/cancel/', CancelOrderView.as_view(), name='cancel_order'),

    # User Trades
    path('user/trades/', UserTradesView.as_view(), name='user_trades'),
]