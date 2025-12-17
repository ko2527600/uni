"""
Celery worker entry point for UniPortal
Run with: 
  Worker: celery -A celery_worker.celery worker --loglevel=info
  Beat (Scheduler): celery -A celery_worker.celery beat --loglevel=info
  Combined: celery -A celery_worker.celery worker --beat --loglevel=info
"""
from app import create_app
from celery.schedules import crontab

# Create Flask app instance
app = create_app()

# Expose celery instance for worker
celery = app.extensions['celery']

# Configure Celery Beat schedule for periodic tasks
celery.conf.beat_schedule = {
    'check-subscription-expiry-daily': {
        'task': 'app.tasks.check_subscription_expiry',
        'schedule': crontab(hour=9, minute=0),  # Run daily at 9:00 AM
    },
}

celery.conf.timezone = 'UTC'
