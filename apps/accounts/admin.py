"""
Accounts Admin Configuration
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, WalletConnection, AuthNonce


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User Admin."""

    list_display = [
        'email', 'username', 'is_email_verified',
        'is_active', 'is_staff', 'created_at'
    ]
    list_filter = ['is_active', 'is_staff', 'is_email_verified', 'created_at']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering = ['-created_at']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('username', 'first_name', 'last_name')}),
        ('Verification', {'fields': ('is_email_verified', 'is_2fa_enabled')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Timestamps', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )

    readonly_fields = ['created_at', 'updated_at', 'last_login']

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )


@admin.register(WalletConnection)
class WalletConnectionAdmin(admin.ModelAdmin):
    """Wallet Connection Admin."""

    list_display = [
        'wallet_address_short', 'user', 'wallet_type',
        'is_verified', 'is_primary', 'created_at'
    ]
    list_filter = ['wallet_type', 'is_verified', 'is_primary', 'chain_id']
    search_fields = ['wallet_address', 'user__email']
    ordering = ['-created_at']

    readonly_fields = ['nonce', 'created_at', 'updated_at', 'last_used_at']

    def wallet_address_short(self, obj):
        return f"{obj.wallet_address[:8]}...{obj.wallet_address[-6:]}"

    wallet_address_short.short_description = 'Wallet'


@admin.register(AuthNonce)
class AuthNonceAdmin(admin.ModelAdmin):
    """Auth Nonce Admin."""

    list_display = [
        'wallet_address_short', 'is_used',
        'is_expired', 'expires_at', 'created_at'
    ]
    list_filter = ['is_used', 'created_at']
    search_fields = ['wallet_address']
    ordering = ['-created_at']

    readonly_fields = ['nonce', 'message', 'created_at']

    def wallet_address_short(self, obj):
        return f"{obj.wallet_address[:8]}...{obj.wallet_address[-6:]}"

    wallet_address_short.short_description = 'Wallet'

    def is_expired(self, obj):
        return obj.is_expired

    is_expired.boolean = True
    is_expired.short_description = 'Expired'