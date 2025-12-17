# 📧 Email Notification System - Setup Guide

## Overview
Automated email notifications for subscription expiry reminders.

## Features
- ✅ 7 days before expiry: Warning email
- ✅ 3 days before expiry: Urgent reminder
- ✅ On expiry day: Expiration notification
- ✅ 3 days after expiry: Final reminder

## How It Works
1. Celery Beat runs daily at 9:00 AM
2. Checks all class subscriptions
3. Sends appropriate emails based on days remaining
4. Emails sent to Class Reps only

## Running the System

### Option 1: Worker + Beat Combined (Recommended for Development)
```bash
celery -A celery_worker.celery worker --beat --loglevel=info
```

### Option 2: Separate Processes (Recommended for Production)

**Terminal 1 - Start Celery Worker:**
```bash
celery -A celery_worker.celery worker --loglevel=info
```

**Terminal 2 - Start Celery Beat (Scheduler):**
```bash
celery -A celery_worker.celery beat --loglevel=info
```

## Manual Testing

You can manually trigger the subscription check:

```python
from app.tasks import check_subscription_expiry

# Run immediately
check_subscription_expiry.delay()
```

Or test individual email functions:

```python
from app.tasks import send_expiry_reminder_email

# Test 7-day reminder
send_expiry_reminder_email.delay(
    'rep@example.com',
    'John Doe',
    'Computer Science 2024',
    7,
    'December 25, 2025'
)
```

## Email Schedule

| Days Remaining | Email Type | Urgency |
|---------------|------------|---------|
| 7 days | Reminder | Normal |
| 3 days | Urgent Reminder | High |
| 0 days (today) | Expiration Notice | Critical |
| -3 days (3 days after) | Final Reminder | Last Chance |

## Email Content

### 7-Day Reminder
- Subject: "⏰ Reminder: Premium Expires in 7 Days"
- Content: Warning about upcoming expiry, features that will be locked, renewal options

### 3-Day Reminder
- Subject: "⚠️ URGENT: Premium Expires in 3 Days"
- Content: Urgent warning, locked features list, pricing, renewal link

### Expiry Day
- Subject: "🔴 Premium Subscription Expired"
- Content: Expiration notice, locked features, immediate renewal call-to-action

### 3 Days After Expiry
- Subject: "⚠️ Final Reminder: Renew Your Subscription"
- Content: Final reminder, status update, renewal options

## Configuration

### Change Email Schedule Time
Edit `celery_worker.py`:

```python
celery.conf.beat_schedule = {
    'check-subscription-expiry-daily': {
        'task': 'app.tasks.check_subscription_expiry',
        'schedule': crontab(hour=9, minute=0),  # Change hour/minute here
    },
}
```

### Change Reminder Days
Edit `app/tasks.py` in the `check_subscription_expiry` function:

```python
# Current: 7, 3, 0, -3 days
# Modify these conditions:
if days_remaining == 7:  # Change to 10 for 10-day reminder
if days_remaining == 3:  # Change to 5 for 5-day reminder
```

## Troubleshooting

### Emails Not Sending
1. Check Redis is running: `redis-cli ping` (should return PONG)
2. Check Celery worker is running
3. Check Celery beat is running
4. Check email configuration in `app/__init__.py`

### Check Celery Logs
```bash
# Worker logs show task execution
celery -A celery_worker.celery worker --loglevel=debug

# Beat logs show scheduling
celery -A celery_worker.celery beat --loglevel=debug
```

### Verify Task is Scheduled
```bash
celery -A celery_worker.celery inspect scheduled
```

## Production Deployment

For production, use a process manager like Supervisor or systemd:

### Supervisor Example (`/etc/supervisor/conf.d/celery.conf`):
```ini
[program:celery_worker]
command=celery -A celery_worker.celery worker --loglevel=info
directory=/path/to/uniportal
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/celery/worker.err.log
stdout_logfile=/var/log/celery/worker.out.log

[program:celery_beat]
command=celery -A celery_worker.celery beat --loglevel=info
directory=/path/to/uniportal
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/celery/beat.err.log
stdout_logfile=/var/log/celery/beat.out.log
```

## Testing Email Templates

To preview email templates, you can temporarily add a test route:

```python
@main.route('/test_email')
def test_email():
    from app.tasks import send_expiry_reminder_email
    send_expiry_reminder_email.delay(
        'your-email@example.com',
        'Test User',
        'Test Class',
        7,
        'December 31, 2025'
    )
    return 'Test email sent!'
```

## Notes
- Emails are sent to Class Reps only (not students)
- Reps are identified by `ClassGroup.created_by`
- All times are in UTC
- HTML and plain text versions included in all emails
- Beautiful responsive email templates with gradients and styling
