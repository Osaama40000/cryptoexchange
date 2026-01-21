"""
Email Signals
=============
Automatically trigger emails on certain events using Django signals
"""

from django.db.models.signals import post_save
from django.dispatch import receiver, Signal
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)

# Custom signals for events that need email notifications
order_filled = Signal()  # Triggered when an order is filled
withdrawal_requested = Signal()  # Triggered when withdrawal is requested
withdrawal_confirmed = Signal()  # Triggered when withdrawal is completed
deposit_confirmed = Signal()  # Triggered when deposit is confirmed
login_detected = Signal()  # Triggered on user login


@receiver(post_save, sender=get_user_model())
def send_welcome_email_on_registration(sender, instance, created, **kwargs):
    """
    Send welcome email when a new user is created
    """
    if created:
        from emails.services import EmailService
        try:
            EmailService.send_welcome_email(instance)
            logger.info(f"Welcome email sent to {instance.email}")
        except Exception as e:
            logger.error(f"Failed to send welcome email to {instance.email}: {e}")


@receiver(order_filled)
def send_order_filled_email(sender, user, order, **kwargs):
    """
    Send email when an order is filled
    """
    from emails.services import EmailService
    try:
        EmailService.send_order_filled(user, order)
        logger.info(f"Order filled email sent to {user.email}")
    except Exception as e:
        logger.error(f"Failed to send order filled email to {user.email}: {e}")


@receiver(withdrawal_requested)
def send_withdrawal_requested_email(sender, user, withdrawal, **kwargs):
    """
    Send email when withdrawal is requested
    """
    from emails.services import EmailService
    try:
        EmailService.send_withdrawal_requested(user, withdrawal)
        logger.info(f"Withdrawal requested email sent to {user.email}")
    except Exception as e:
        logger.error(f"Failed to send withdrawal requested email to {user.email}: {e}")


@receiver(withdrawal_confirmed)
def send_withdrawal_confirmed_email(sender, user, withdrawal, **kwargs):
    """
    Send email when withdrawal is confirmed
    """
    from emails.services import EmailService
    try:
        EmailService.send_withdrawal_confirmed(user, withdrawal)
        logger.info(f"Withdrawal confirmed email sent to {user.email}")
    except Exception as e:
        logger.error(f"Failed to send withdrawal confirmed email to {user.email}: {e}")


@receiver(deposit_confirmed)
def send_deposit_confirmed_email(sender, user, deposit, **kwargs):
    """
    Send email when deposit is confirmed
    """
    from emails.services import EmailService
    try:
        EmailService.send_deposit_confirmed(user, deposit)
        logger.info(f"Deposit confirmed email sent to {user.email}")
    except Exception as e:
        logger.error(f"Failed to send deposit confirmed email to {user.email}: {e}")


@receiver(login_detected)
def send_login_alert_email(sender, user, ip_address, device_info, **kwargs):
    """
    Send email when login is detected
    """
    from emails.services import EmailService
    try:
        EmailService.send_login_alert(user, ip_address, device_info)
        logger.info(f"Login alert email sent to {user.email}")
    except Exception as e:
        logger.error(f"Failed to send login alert email to {user.email}: {e}")
