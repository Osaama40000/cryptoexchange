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
# Add periodic task for stop order checking
app.conf.beat_schedule.update({
    'check-stop-orders': {
        'task': 'apps.trading.tasks.check_stop_orders',
        'schedule': 5.0,  # Every 5 seconds
    },
    'process-triggered-orders': {
        'task': 'apps.trading.tasks.process_triggered_orders',
        'schedule': 3.0,  # Every 3 seconds
    },
})

# Add periodic task for stop order checking
app.conf.beat_schedule.update({
    'check-stop-orders': {
        'task': 'apps.trading.tasks.check_stop_orders',
        'schedule': 5.0,  # Every 5 seconds
    },
    'process-triggered-orders': {
        'task': 'apps.trading.tasks.process_triggered_orders',
        'schedule': 3.0,  # Every 3 seconds
    },
})
