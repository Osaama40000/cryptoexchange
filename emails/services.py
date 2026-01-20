cat > emails / services.py << 'EOF'
"""
Email Service
=============
Centralized email sending service with templates
"""

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """
    Service class for sending all email notifications
    """

    FROM_EMAIL = settings.DEFAULT_FROM_EMAIL

    @classmethod
    def send_email(cls, to_email, subject, template_name, context=None):
        """
        Send an email using a template

        Args:
            to_email: Recipient email address
            subject: Email subject line
            template_name: Name of the template (without extension)
            context: Dictionary of template variables
        """
        if context is None:
            context = {}

        # Add common context variables
        context.update({
            'site_name': 'CryptoExchange',
            'site_url': settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else 'https://cryptoexchange.com',
            'support_email': 'support@cryptoexchange.com',
            'current_year': timezone.now().year,
        })

        try:
            # Render HTML template
            html_content = render_to_string(f'emails/{template_name}.html', context)

            # Render plain text template (fallback)
            try:
                text_content = render_to_string(f'emails/{template_name}.txt', context)
            except:
                # Strip HTML tags for plain text fallback
                import re
                text_content = re.sub('<[^<]+?>', '', html_content)

            # Create email message
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=cls.FROM_EMAIL,
                to=[to_email]
            )
            email.attach_alternative(html_content, "text/html")

            # Send email
            email.send(fail_silently=False)

            logger.info(f"Email sent successfully: {template_name} to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email {template_name} to {to_email}: {str(e)}")
            return False

    # ==================== User Authentication Emails ====================

    @classmethod
    def send_welcome_email(cls, user):
        """Send welcome email to new users"""
        return cls.send_email(
            to_email=user.email,
            subject="Welcome to CryptoExchange! 🎉",
            template_name="welcome",
            context={
                'user': user,
                'username': user.email.split('@')[0],
            }
        )

    @classmethod
    def send_login_alert(cls, user, ip_address, user_agent, location=None):
        """Send alert when user logs in from new device/location"""
        return cls.send_email(
            to_email=user.email,
            subject="🔔 New Login to Your CryptoExchange Account",
            template_name="login_alert",
            context={
                'user': user,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'location': location or 'Unknown',
                'login_time': timezone.now(),
            }
        )

    @classmethod
    def send_password_changed(cls, user):
        """Send confirmation when password is changed"""
        return cls.send_email(
            to_email=user.email,
            subject="🔐 Your Password Has Been Changed",
            template_name="password_changed",
            context={
                'user': user,
                'changed_at': timezone.now(),
            }
        )

    @classmethod
    def send_password_reset(cls, user, reset_url):
        """Send password reset link"""
        return cls.send_email(
            to_email=user.email,
            subject="Reset Your CryptoExchange Password",
            template_name="password_reset",
            context={
                'user': user,
                'reset_url': reset_url,
            }
        )

    # ==================== Security Emails ====================

    @classmethod
    def send_2fa_enabled(cls, user):
        """Send confirmation when 2FA is enabled"""
        return cls.send_email(
            to_email=user.email,
            subject="✅ Two-Factor Authentication Enabled",
            template_name="2fa_enabled",
            context={
                'user': user,
                'enabled_at': timezone.now(),
            }
        )

    @classmethod
    def send_2fa_disabled(cls, user):
        """Send alert when 2FA is disabled"""
        return cls.send_email(
            to_email=user.email,
            subject="⚠️ Two-Factor Authentication Disabled",
            template_name="2fa_disabled",
            context={
                'user': user,
                'disabled_at': timezone.now(),
            }
        )

    @classmethod
    def send_api_key_created(cls, user, key_name):
        """Send alert when new API key is created"""
        return cls.send_email(
            to_email=user.email,
            subject="🔑 New API Key Created",
            template_name="api_key_created",
            context={
                'user': user,
                'key_name': key_name,
                'created_at': timezone.now(),
            }
        )

    # ==================== Trading Emails ====================

    @classmethod
    def send_order_filled(cls, user, order):
        """Send notification when order is filled"""
        return cls.send_email(
            to_email=user.email,
            subject=f"✅ Order Filled: {order.side.upper()} {order.symbol}",
            template_name="order_filled",
            context={
                'user': user,
                'order': order,
                'symbol': order.symbol,
                'side': order.side,
                'quantity': order.quantity,
                'price': order.price,
                'total': float(order.quantity) * float(order.price),
                'filled_at': timezone.now(),
            }
        )

    @classmethod
    def send_order_cancelled(cls, user, order):
        """Send notification when order is cancelled"""
        return cls.send_email(
            to_email=user.email,
            subject=f"❌ Order Cancelled: {order.side.upper()} {order.symbol}",
            template_name="order_cancelled",
            context={
                'user': user,
                'order': order,
                'cancelled_at': timezone.now(),
            }
        )

    # ==================== Withdrawal Emails ====================

    @classmethod
    def send_withdrawal_requested(cls, user, withdrawal):
        """Send confirmation when withdrawal is requested"""
        return cls.send_email(
            to_email=user.email,
            subject=f"📤 Withdrawal Request: {withdrawal.amount} {withdrawal.currency}",
            template_name="withdrawal_requested",
            context={
                'user': user,
                'withdrawal': withdrawal,
                'amount': withdrawal.amount,
                'currency': withdrawal.currency,
                'address': withdrawal.address,
                'requested_at': timezone.now(),
            }
        )

    @classmethod
    def send_withdrawal_confirmed(cls, user, withdrawal):
        """Send confirmation when withdrawal is completed"""
        return cls.send_email(
            to_email=user.email,
            subject=f"✅ Withdrawal Completed: {withdrawal.amount} {withdrawal.currency}",
            template_name="withdrawal_confirmed",
            context={
                'user': user,
                'withdrawal': withdrawal,
                'amount': withdrawal.amount,
                'currency': withdrawal.currency,
                'tx_hash': withdrawal.tx_hash,
                'confirmed_at': timezone.now(),
            }
        )

    # ==================== Deposit Emails ====================

    @classmethod
    def send_deposit_confirmed(cls, user, deposit):
        """Send confirmation when deposit is received"""
        return cls.send_email(
            to_email=user.email,
            subject=f"💰 Deposit Received: {deposit.amount} {deposit.currency}",
            template_name="deposit_confirmed",
            context={
                'user': user,
                'deposit': deposit,
                'amount': deposit.amount,
                'currency': deposit.currency,
                'confirmed_at': timezone.now(),
            }
        )


