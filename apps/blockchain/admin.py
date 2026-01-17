"""
Blockchain Admin Configuration
"""

from django.contrib import admin
from .models import Network, MonitoredAddress


@admin.register(Network)
class NetworkAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'chain_id', 'native_currency', 'is_active',
        'is_testnet', 'last_synced_block'
    ]
    list_filter = ['is_active', 'is_testnet']
    search_fields = ['name', 'chain_id']
    ordering = ['chain_id']


@admin.register(MonitoredAddress)
class MonitoredAddressAdmin(admin.ModelAdmin):
    list_display = ['address_short', 'network', 'user', 'is_active', 'created_at']
    list_filter = ['network', 'is_active']
    search_fields = ['address', 'user__email']
    ordering = ['-created_at']

    def address_short(self, obj):
        return f"{obj.address[:10]}...{obj.address[-8:]}"

    address_short.short_description = 'Address'