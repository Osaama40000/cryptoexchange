"""
Accounts URL Configuration
==========================
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    WalletNonceView,
    WalletVerifyView,
    WalletConnectView,
    WalletDisconnectView,
    UserProfileView,
    UserWalletsView,
    ChangePasswordView,
    SetPasswordView,
)

app_name = 'accounts'

urlpatterns = [
    # Email/Password Authentication
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Wallet Authentication
    path('wallet/nonce/', WalletNonceView.as_view(), name='wallet_nonce'),
    path('wallet/verify/', WalletVerifyView.as_view(), name='wallet_verify'),
    path('wallet/connect/', WalletConnectView.as_view(), name='wallet_connect'),
    path('wallet/<uuid:wallet_id>/disconnect/', WalletDisconnectView.as_view(), name='wallet_disconnect'),

    # User Profile
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('wallets/', UserWalletsView.as_view(), name='user_wallets'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('set-password/', SetPasswordView.as_view(), name='set_password'),
]