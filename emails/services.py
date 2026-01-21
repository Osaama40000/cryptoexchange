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
        """
        if context is None:
            context = {}
        
        context.update({
            'site_name': 'CryptoExchange',
            'site_url': getattr(settings, 'FRONTEND_URL', 'https://cryptoexchange.com'),
            'support_email': 'support@cryptoexchange.com',
            'current_year': timezone.now().year,
        })
        
        try:
            # Render HTML template
            html_content = render_to_string(f'emails/{template_name}.html', context)
            
            # Try to render text template, fallback to stripping HTML
            try:
                text_content = render_to_string(f'emails/{template_name}.txt', context)
            except Exception:
                # If no .txt template, create plain text from subject
                text_content = f"{subject}\n\nPlease view this email in an HTML-compatible email client."
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=cls.FROM_EMAIL,
                to=[to_email],
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
            
            logger.info(f"Email sent: {template_name} to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email {template_name} to {to_email}: {e}")
            return False
    
    @classmethod
    def send_welcome_email(cls, user):
        """Send welcome email to new user"""
        return cls.send_email(
            to_email=user.email,
            subject="Welcome to CryptoExchange!",
            template_name="welcome",
            context={'user': user}
        )
    
    @classmethod
    def send_login_alert(cls, user, ip_address, device_info):
        """Send login alert email"""
        return cls.send_email(
            to_email=user.email,
            subject="New Login Detected - CryptoExchange",
            template_name="login_alert",
            context={
                'user': user,
                'ip_address': ip_address,
                'device_info': device_info,
                'login_time': timezone.now(),
            }
        )
    
    @classmethod
    def send_order_filled(cls, user, order):
        """Send order filled notification"""
        return cls.send_email(
            to_email=user.email,
            subject=f"Order Filled - {order.side.upper()} {order.symbol}",
            template_name="order_filled",
            context={'user': user, 'order': order}
        )
    
    @classmethod
    def send_withdrawal_requested(cls, user, withdrawal):
        """Send withdrawal request confirmation"""
        return cls.send_email(
            to_email=user.email,
            subject="Withdrawal Request Received - CryptoExchange",
            template_name="withdrawal_requested",
            context={'user': user, 'withdrawal': withdrawal}
        )
    
    @classmethod
    def send_withdrawal_confirmed(cls, user, withdrawal):
        """Send withdrawal completion notification"""
        return cls.send_email(
            to_email=user.email,
            subject="Withdrawal Complete - CryptoExchange",
            template_name="withdrawal_confirmed",
            context={'user': user, 'withdrawal': withdrawal}
        )
    
    @classmethod
    def send_deposit_confirmed(cls, user, deposit):
        """Send deposit confirmation"""
        return cls.send_email(
            to_email=user.email,
            subject="Deposit Confirmed - CryptoExchange",
            template_name="deposit_confirmed",
            context={'user': user, 'deposit': deposit}
        )
    
    @classmethod
    def send_2fa_enabled(cls, user):
        """Send 2FA enabled notification"""
        return cls.send_email(
            to_email=user.email,
            subject="2FA Enabled - CryptoExchange",
            template_name="2fa_enabled",
            context={'user': user}
        )
    
    @classmethod
    def send_2fa_disabled(cls, user):
        """Send 2FA disabled notification"""
        return cls.send_email(
            to_email=user.email,
            subject="2FA Disabled - CryptoExchange",
            template_name="2fa_disabled",
            context={'user': user}
        )
    
    @classmethod
    def send_password_changed(cls, user):
        """Send password changed notification"""
        return cls.send_email(
            to_email=user.email,
            subject="Password Changed - CryptoExchange",
            template_name="password_changed",
            context={'user': user}
        )
    
    @classmethod
    def send_api_key_created(cls, user, key_name):
        """Send API key created notification"""
        return cls.send_email(
            to_email=user.email,
            subject="New API Key Created - CryptoExchange",
            template_name="api_key_created",
            context={'user': user, 'key_name': key_name}
        )


    @classmethod
    def send_verification_email(cls, user, token):
        """Send email verification link"""
        from django.conf import settings
        
        verification_url = f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/verify-email?token={token.token}"
        
        return cls.send_email(
            to_email=user.email,
            subject="Verify Your Email - CryptoExchange",
            template_name="verify_email",
            context={
                'user': user,
                'verification_url': verification_url,
                'token': token,
            }
        )
