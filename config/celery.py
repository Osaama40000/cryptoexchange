"""
Celery Configuration for CryptoExchange Demo
"""

import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

app = Celery('cryptoexchange')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Periodic tasks schedule
app.conf.beat_schedule = {
    'monitor-deposits-every-30-seconds': {
        'task': 'apps.blockchain.tasks.monitor_deposits',
        'schedule': 30.0,
    },
    'update-trading-pair-stats-every-minute': {
        'task': 'apps.trading.tasks.update_trading_pair_stats',
        'schedule': 60.0,
    },
}