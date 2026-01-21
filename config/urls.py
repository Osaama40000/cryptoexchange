"""
URL Configuration
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # Keep 'auth' path for frontend compatibility
    path('api/v1/auth/', include('apps.accounts.urls')),
    path('api/v1/wallets/', include('apps.wallets.urls')),
    path('api/v1/email/', include('emails.urls')),
    path('api/v1/trading/', include('apps.trading.urls')),
    path('api/v1/security/', include('security.urls')),
]
