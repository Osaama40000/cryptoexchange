"""
Audit Models
============
Models for comprehensive audit logging.
"""

import uuid
from django.db import models
from django.conf import settings


class AuditLog(models.Model):
    """
    Comprehensive audit log for all system actions.

    Records:
    - User actions (login, logout, etc.)
    - Trading actions (orders, trades)
    - Wallet actions (deposits, withdrawals)
    - Admin actions (balance adjustments)
    """

    ACTION_CHOICES = [
        # Authentication
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('login_failed', 'Login Failed'),
        ('register', 'Register'),
        ('password_change', 'Password Change'),
        ('password_reset', 'Password Reset'),

        # Wallet
        ('wallet_connect', 'Wallet Connect'),
        ('wallet_disconnect', 'Wallet Disconnect'),
        ('wallet_verify', 'Wallet Verify'),

        # Trading
        ('order_create', 'Order Create'),
        ('order_cancel', 'Order Cancel'),
        ('trade_execute', 'Trade Execute'),

        # Wallet Operations
        ('deposit_create', 'Deposit Create'),
        ('deposit_credit', 'Deposit Credit'),
        ('withdrawal_request', 'Withdrawal Request'),
        ('withdrawal_approve', 'Withdrawal Approve'),
        ('withdrawal_reject', 'Withdrawal Reject'),
        ('withdrawal_process', 'Withdrawal Process'),

        # Admin
        ('admin_balance_adjust', 'Admin Balance Adjust'),
        ('admin_user_update', 'Admin User Update'),
        ('admin_settings_change', 'Admin Settings Change'),

        # Other
        ('api_access', 'API Access'),
        ('error', 'Error'),
    ]

    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failure', 'Failure'),
        ('pending', 'Pending'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Who performed the action
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )

    # What action was performed
    action = models.CharField(max_length=50, choices=ACTION_CHOICES, db_index=True)

    # What resource was affected
    resource_type = models.CharField(max_length=50, db_index=True)
    resource_id = models.UUIDField(null=True, blank=True)

    # Request details
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)

    # Change tracking
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)

    # Additional context
    metadata = models.JSONField(null=True, blank=True)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='success')
    error_message = models.TextField(blank=True, null=True)

    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['action', '-created_at']),
            models.Index(fields=['resource_type', 'resource_id']),
        ]

    def __str__(self):
        user_str = self.user.email if self.user else 'Anonymous'
        return f"{user_str} - {self.action} - {self.created_at}"


class AdminBalanceAdjustment(models.Model):
    """
    Specific audit trail for admin balance adjustments.
    Provides extra detail for compliance and investigations.
    """

    ADJUSTMENT_TYPES = [
        ('credit', 'Credit'),
        ('debit', 'Debit'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Who made the adjustment
    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='admin_adjustments_made'
    )

    # Who was adjusted
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='balance_adjustments_received'
    )

    # What currency
    currency = models.ForeignKey(
        'wallets.Currency',
        on_delete=models.PROTECT
    )

    # Adjustment details
    adjustment_type = models.CharField(max_length=10, choices=ADJUSTMENT_TYPES)
    amount = models.DecimalField(max_digits=36, decimal_places=18)
    balance_before = models.DecimalField(max_digits=36, decimal_places=18)
    balance_after = models.DecimalField(max_digits=36, decimal_places=18)

    # Reason is mandatory
    reason = models.TextField()

    # Link to ledger entry
    ledger_entry = models.ForeignKey(
        'wallets.LedgerEntry',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Admin Balance Adjustment'
        verbose_name_plural = 'Admin Balance Adjustments'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.admin} {self.adjustment_type}ed {self.amount} to {self.target_user}"