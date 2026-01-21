"""
Email Middleware
================
Middleware for tracking logins and sending alerts
"""

import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


def get_client_ip(request):
    """Extract client IP from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', 'Unknown')
    return ip


def get_device_info(request):
    """Extract device info from user agent"""
    user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
    
    # Simple device detection
    if 'Mobile' in user_agent:
        device_type = 'Mobile'
    elif 'Tablet' in user_agent:
        device_type = 'Tablet'
    else:
        device_type = 'Desktop'
    
    # Simple browser detection
    if 'Chrome' in user_agent:
        browser = 'Chrome'
    elif 'Firefox' in user_agent:
        browser = 'Firefox'
    elif 'Safari' in user_agent:
        browser = 'Safari'
    elif 'Edge' in user_agent:
        browser = 'Edge'
    else:
        browser = 'Unknown'
    
    return f"{device_type} - {browser}"


def send_login_alert(user, request):
    """
    Send login alert email to user
    Call this from your login view after successful authentication
    """
    from emails.signals import login_detected
    
    ip_address = get_client_ip(request)
    device_info = get_device_info(request)
    
    login_detected.send(
        sender=user.__class__,
        user=user,
        ip_address=ip_address,
        device_info=device_info
    )
