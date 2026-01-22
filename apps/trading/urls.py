from django.urls import path
from .views import (
    TradingPairListView, TradingPairDetailView,
    OrderBookView,
    OrderListCreateView, OrderDetailView, OrderCancelView,
    TradeListView, TradeDetailView,
    StopLossOrderView, TakeProfitOrderView, TrailingStopOrderView,
    OCOOrderView, StopOrderListView, CancelStopOrderView,
)

app_name = 'trading'

urlpatterns = [
    # Trading pairs
    path('pairs/', TradingPairListView.as_view(), name='pair-list'),
    path('pairs/<str:symbol>/', TradingPairDetailView.as_view(), name='pair-detail'),
    
    # Order book
    path('orderbook/<str:symbol>/', OrderBookView.as_view(), name='orderbook'),
    
    # Orders
    path('orders/', OrderListCreateView.as_view(), name='order-list'),
    path('orders/<uuid:pk>/', OrderDetailView.as_view(), name='order-detail'),
    path('orders/<uuid:pk>/cancel/', OrderCancelView.as_view(), name='order-cancel'),
    
    # Stop Orders
    path('orders/stop-loss/', StopLossOrderView.as_view(), name='stop-loss'),
    path('orders/take-profit/', TakeProfitOrderView.as_view(), name='take-profit'),
    path('orders/trailing-stop/', TrailingStopOrderView.as_view(), name='trailing-stop'),
    path('orders/oco/', OCOOrderView.as_view(), name='oco'),
    path('orders/stops/', StopOrderListView.as_view(), name='stop-list'),
    path('orders/stops/<uuid:order_id>/cancel/', CancelStopOrderView.as_view(), name='cancel-stop'),
    
    # Trades
    path('trades/', TradeListView.as_view(), name='trade-list'),
    path('trades/<uuid:pk>/', TradeDetailView.as_view(), name='trade-detail'),
]
