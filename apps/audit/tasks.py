"""
Audit Celery Tasks
==================
"""

import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger('audit')


@shared_task(name='apps.audit.tasks.cleanup_old_audit_logs')
def cleanup_old_audit_logs(days_to_keep: int = 90):
    """
    Clean up old audit logs.
    Keeps logs for the specified number of days.
    Runs daily at 3 AM.
    """
    from apps.audit.models import AuditLog

    logger.info(f"Cleaning up audit logs older than {days_to_keep} days...")

    cutoff_date = timezone.now() - timedelta(days=days_to_keep)

    deleted_count, _ = AuditLog.objects.filter(
        created_at__lt=cutoff_date
    ).delete()

    logger.info(f"Deleted {deleted_count} old audit logs")

    return {'status': 'completed', 'deleted': deleted_count}