"""
Email Notifications Helper
==========================
Easy-to-use functions for sending email notifications from anywhere in the app
"""

from emails.signals import (
    order_filled,
    withdrawal_requested,
    withdrawal_confirmed,
    deposit_confirmed,
    login_detected,
)
import logging

logger = logging.getLogger(__name__)


def notify_order_filled(user, order):
    """
    Call this when an order is filled
    
    Usage:
        from emails.notifications import notify_order_filled
        notify_order_filled(user, order)
    """
    order_filled.send(sender=order.__class__, user=user, order=order)


def notify_withdrawal_requested(user, withdrawal):
    """
    Call this when a withdrawal is requested
    
    Usage:
        from emails.notifications import notify_withdrawal_requested
        notify_withdrawal_requested(user, withdrawal)
    """
    withdrawal_requested.send(sender=withdrawal.__class__, user=user, withdrawal=withdrawal)


def notify_withdrawal_confirmed(user, withdrawal):
    """
    Call this when a withdrawal is confirmed/completed
    
    Usage:
        from emails.notifications import notify_withdrawal_confirmed
        notify_withdrawal_confirmed(user, withdrawal)
    """
    withdrawal_confirmed.send(sender=withdrawal.__class__, user=user, withdrawal=withdrawal)


def notify_deposit_confirmed(user, deposit):
    """
    Call this when a deposit is confirmed
    
    Usage:
        from emails.notifications import notify_deposit_confirmed
        notify_deposit_confirmed(user, deposit)
    """
    deposit_confirmed.send(sender=deposit.__class__, user=user, deposit=deposit)


def notify_login(user, request):
    """
    Call this after successful login
    
    Usage:
        from emails.notifications import notify_login
        notify_login(user, request)
    """
    from emails.middleware import get_client_ip, get_device_info
    
    ip_address = get_client_ip(request)
    device_info = get_device_info(request)
    
    login_detected.send(
        sender=user.__class__,
        user=user,
        ip_address=ip_address,
        device_info=device_info
    )


def notify_2fa_enabled(user):
    """
    Call this when 2FA is enabled
    
    Usage:
        from emails.notifications import notify_2fa_enabled
        notify_2fa_enabled(user)
    """
    from emails.services import EmailService
    EmailService.send_2fa_enabled(user)


def notify_2fa_disabled(user):
    """
    Call this when 2FA is disabled
    
    Usage:
        from emails.notifications import notify_2fa_disabled
        notify_2fa_disabled(user)
    """
    from emails.services import EmailService
    EmailService.send_2fa_disabled(user)


def notify_password_changed(user):
    """
    Call this when password is changed
    
    Usage:
        from emails.notifications import notify_password_changed
        notify_password_changed(user)
    """
    from emails.services import EmailService
    EmailService.send_password_changed(user)


def notify_api_key_created(user, key_name):
    """
    Call this when an API key is created
    
    Usage:
        from emails.notifications import notify_api_key_created
        notify_api_key_created(user, "My Trading Bot")
    """
    from emails.services import EmailService
    EmailService.send_api_key_created(user, key_name)
