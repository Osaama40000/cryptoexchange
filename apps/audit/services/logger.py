"""
Audit Logger Service
====================
Service for creating audit log entries.
"""

import logging
from typing import Any, Dict, Optional
from django.utils import timezone

from apps.audit.models import AuditLog, AdminBalanceAdjustment

logger = logging.getLogger('audit')


class AuditLogger:
    """
    Service for creating audit log entries.

    Usage:
        AuditLogger.log(
            user=request.user,
            action='order_create',
            resource_type='order',
            resource_id=order.id,
            request=request,
            new_value={'quantity': 100, 'price': 50}
        )
    """

    @staticmethod
    def log(
            action: str,
            resource_type: str,
            user=None,
            resource_id=None,
            request=None,
            old_value: Dict = None,
            new_value: Dict = None,
            metadata: Dict = None,
            status: str = 'success',
            error_message: str = None
    ) -> AuditLog:
        """
        Create an audit log entry.

        Args:
            action: Action being performed (from ACTION_CHOICES)
            resource_type: Type of resource affected
            user: User performing the action
            resource_id: ID of the affected resource
            request: HTTP request object (for IP and user agent)
            old_value: Previous state (for updates)
            new_value: New state
            metadata: Additional context
            status: success/failure/pending
            error_message: Error details if failed

        Returns:
            AuditLog instance
        """
        ip_address = None
        user_agent = None

        if request:
            ip_address = AuditLogger._get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]

        audit_log = AuditLog.objects.create(
            user=user,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            old_value=old_value,
            new_value=new_value,
            metadata=metadata,
            status=status,
            error_message=error_message
        )

        # Also log to file
        log_message = (
            f"AUDIT: {action} | User: {user.email if user else 'Anonymous'} | "
            f"Resource: {resource_type}/{resource_id} | Status: {status}"
        )

        if status == 'failure':
            logger.warning(log_message)
        else:
            logger.info(log_message)

        return audit_log

    @staticmethod
    def log_admin_balance_adjustment(
            admin,
            target_user,
            currency,
            adjustment_type: str,
            amount,
            balance_before,
            balance_after,
            reason: str,
            ledger_entry=None
    ) -> AdminBalanceAdjustment:
        """
        Create an admin balance adjustment audit record.

        Args:
            admin: Admin user making the adjustment
            target_user: User whose balance is being adjusted
            currency: Currency being adjusted
            adjustment_type: 'credit' or 'debit'
            amount: Amount of adjustment
            balance_before: Balance before adjustment
            balance_after: Balance after adjustment
            reason: Reason for adjustment
            ledger_entry: Associated ledger entry

        Returns:
            AdminBalanceAdjustment instance
        """
        adjustment = AdminBalanceAdjustment.objects.create(
            admin=admin,
            target_user=target_user,
            currency=currency,
            adjustment_type=adjustment_type,
            amount=amount,
            balance_before=balance_before,
            balance_after=balance_after,
            reason=reason,
            ledger_entry=ledger_entry
        )

        # Also create general audit log
        AuditLogger.log(
            user=admin,
            action='admin_balance_adjust',
            resource_type='balance',
            resource_id=target_user.id,
            old_value={'balance': str(balance_before)},
            new_value={'balance': str(balance_after)},
            metadata={
                'target_user_email': target_user.email,
                'currency': currency.symbol,
                'adjustment_type': adjustment_type,
                'amount': str(amount),
                'reason': reason
            }
        )

        logger.warning(
            f"ADMIN BALANCE ADJUSTMENT: {admin.email} {adjustment_type}ed "
            f"{amount} {currency.symbol} for {target_user.email}. Reason: {reason}"
        )

        return adjustment

    @staticmethod
    def _get_client_ip(request) -> Optional[str]:
        """Get client IP from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')