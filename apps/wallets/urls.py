"""
Wallets URL Configuration
"""
from django.urls import path
from .views import (
    CurrencyListView,
    BalanceListView,
    BalanceDetailView,
    LedgerHistoryView,
    DepositAddressView,
    DepositHistoryView,
    WithdrawalListView,
    WithdrawalCreateView,
    WithdrawalCancelView,
    AdminBalanceAdjustmentView,
)
from .admin_views import (
    AdminBalanceAdjustmentView as AdminBalanceAdjustView,
    AdminWithdrawalListView,
    AdminWithdrawalApproveView,
    AdminWithdrawalRejectView,
)
from . import views_transfer

app_name = 'wallets'

urlpatterns = [
    # Currencies
    path('currencies/', CurrencyListView.as_view(), name='currency_list'),
    
    # Balances
    path('balances/', BalanceListView.as_view(), name='balance_list'),
    path('balances/<str:currency_symbol>/', BalanceDetailView.as_view(), name='balance_detail'),
    
    # Ledger
    path('ledger/', LedgerHistoryView.as_view(), name='ledger_history'),
    
    # Deposits
    path('deposit-address/<str:currency_symbol>/', DepositAddressView.as_view(), name='deposit_address'),
    path('deposits/', DepositHistoryView.as_view(), name='deposit_list'),
    
    # Withdrawals
    path('withdrawals/', WithdrawalListView.as_view(), name='withdrawal_list'),
    path('withdrawals/create/', WithdrawalCreateView.as_view(), name='withdrawal_create'),
    path('withdrawals/<uuid:withdrawal_id>/cancel/', WithdrawalCancelView.as_view(), name='withdrawal_cancel'),
    
    # P2P Transfers
    path('transfer/', views_transfer.transfer_crypto, name='transfer-crypto'),
    path('transfer/qr/', views_transfer.get_transfer_qr_data, name='transfer-qr'),
    path('transfer/search/', views_transfer.search_users, name='transfer-search'),
    
    # Admin endpoints
    path('admin/adjust-balance/', AdminBalanceAdjustView.as_view(), name='admin_adjust_balance'),
    path('admin/withdrawals/', AdminWithdrawalListView.as_view(), name='admin_withdrawal_list'),
    path('admin/withdrawals/<uuid:withdrawal_id>/approve/', AdminWithdrawalApproveView.as_view(), name='admin_withdrawal_approve'),
    path('admin/withdrawals/<uuid:withdrawal_id>/reject/', AdminWithdrawalRejectView.as_view(), name='admin_withdrawal_reject'),
]
