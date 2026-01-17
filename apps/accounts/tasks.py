"""
Accounts Celery Tasks
=====================
"""

import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger('apps.accounts')


@shared_task(name='apps.accounts.tasks.cleanup_expired_nonces')
def cleanup_expired_nonces():
    """
    Clean up expired authentication nonces.
    Runs every hour.
    """
    from apps.accounts.models import AuthNonce

    logger.info("Cleaning up expired nonces...")

    deleted_count, _ = AuthNonce.objects.filter(
        expires_at__lt=timezone.now()
    ).delete()

    logger.info(f"Deleted {deleted_count} expired nonces")

    return {'status': 'completed', 'deleted': deleted_count}