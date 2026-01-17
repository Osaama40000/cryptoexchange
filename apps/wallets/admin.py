"""
Wallets Admin Configuration
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Currency, Balance, LedgerEntry, Deposit, Withdrawal


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = [
        'symbol', 'name', 'currency_type', 'is_active',
        'is_deposit_enabled', 'is_withdrawal_enabled'
    ]
    list_filter = ['currency_type', 'is_active', 'chain_id']
    search_fields = ['symbol', 'name', 'contract_address']
    ordering = ['symbol']


@admin.register(Balance)
class BalanceAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'currency', 'available', 'locked', 'total_display', 'updated_at'
    ]
    list_filter = ['currency']
    search_fields = ['user__email', 'currency__symbol']
    readonly_fields = ['version', 'created_at', 'updated_at']
    ordering = ['-updated_at']

    def total_display(self, obj):
        return obj.total

    total_display.short_description = 'Total'


@admin.register(LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):
    list_display = [
        'created_at', 'user', 'currency', 'entry_type',
        'amount', 'balance_after'
    ]
    list_filter = ['entry_type', 'currency', 'created_at']
    search_fields = ['user__email', 'description']
    readonly_fields = [
        'id', 'user', 'currency', 'entry_type', 'amount',
        'balance_before', 'balance_after', 'reference_type',
        'reference_id', 'created_by', 'created_at'
    ]
    ordering = ['-created_at']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    list_display = [
        'created_at', 'user', 'currency', 'amount',
        'status', 'confirmations_display', 'tx_hash_short'
    ]
    list_filter = ['status', 'currency', 'created_at']
    search_fields = ['user__email', 'tx_hash', 'from_address']
    readonly_fields = ['created_at', 'updated_at', 'credited_at']
    ordering = ['-created_at']

    def confirmations_display(self, obj):
        return f"{obj.confirmations}/{obj.required_confirmations}"

    confirmations_display.short_description = 'Confirmations'

    def tx_hash_short(self, obj):
        return f"{obj.tx_hash[:10]}...{obj.tx_hash[-8:]}"

    tx_hash_short.short_description = 'Tx Hash'


@admin.register(Withdrawal)
class WithdrawalAdmin(admin.ModelAdmin):
    list_display = [
        'created_at', 'user', 'currency', 'amount',
        'fee', 'status', 'to_address_short'
    ]
    list_filter = ['status', 'currency', 'created_at']
    search_fields = ['user__email', 'tx_hash', 'to_address']
    readonly_fields = ['created_at', 'updated_at', 'approved_at', 'processed_at']
    ordering = ['-created_at']

    actions = ['approve_withdrawals', 'reject_withdrawals']

    def to_address_short(self, obj):
        return f"{obj.to_address[:10]}...{obj.to_address[-8:]}"

    to_address_short.short_description = 'To Address'

    @admin.action(description='Approve selected withdrawals')
    def approve_withdrawals(self, request, queryset):
        queryset.filter(status='pending').update(
            status='approved',
            approved_by=request.user
        )

    @admin.action(description='Reject selected withdrawals')
    def reject_withdrawals(self, request, queryset):
        queryset.filter(status='pending').update(
            status='rejected',
            rejection_reason='Rejected by admin'
        )