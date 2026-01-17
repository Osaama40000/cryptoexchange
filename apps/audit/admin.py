"""
Audit Admin Configuration
"""

from django.contrib import admin
from .models import AuditLog, AdminBalanceAdjustment


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = [
        'created_at', 'user', 'action', 'resource_type',
        'status', 'ip_address'
    ]
    list_filter = ['action', 'status', 'resource_type', 'created_at']
    search_fields = ['user__email', 'ip_address', 'resource_id']
    ordering = ['-created_at']
    readonly_fields = [
        'id', 'user', 'action', 'resource_type', 'resource_id',
        'ip_address', 'user_agent', 'old_value', 'new_value',
        'metadata', 'status', 'error_message', 'created_at'
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AdminBalanceAdjustment)
class AdminBalanceAdjustmentAdmin(admin.ModelAdmin):
    list_display = [
        'created_at', 'admin', 'target_user', 'currency',
        'adjustment_type', 'amount', 'reason_short'
    ]
    list_filter = ['adjustment_type', 'currency', 'created_at']
    search_fields = ['admin__email', 'target_user__email', 'reason']
    ordering = ['-created_at']
    readonly_fields = [
        'id', 'admin', 'target_user', 'currency', 'adjustment_type',
        'amount', 'balance_before', 'balance_after', 'reason',
        'ledger_entry', 'created_at'
    ]

    def reason_short(self, obj):
        return obj.reason[:50] + '...' if len(obj.reason) > 50 else obj.reason

    reason_short.short_description = 'Reason'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False