# Celery Setup for UniPortal

## Prerequisites

1. **Install Redis** (Celery message broker)
   ```bash
   # Windows (using Chocolatey)
   choco install redis-64
   
   # Or download from: https://github.com/microsoftarchive/redis/releases
   ```

2. **Install Celery**
   ```bash
   pip install celery redis
   ```

## Running Celery

### 1. Start Redis Server
```bash
redis-server
```

### 2. Start Celery Worker
```bash
celery -A celery_worker.celery worker --loglevel=info
```

### 3. Start Flask App (in another terminal)
```bash
python run.py
```

## Configuration

The Celery configuration is in `app/__init__.py`:
- **Broker URL**: `redis://localhost:6379/0`
- **Result Backend**: `redis://localhost:6379/0`

## Creating Celery Tasks

Example task in `app/tasks.py`:

```python
from app import create_app

app = create_app()
celery = app.extensions['celery']

@celery.task
def send_email_async(recipient, subject, body):
    """Send email asynchronously"""
    from flask_mail import Message
    from app import mail
    
    msg = Message(subject, recipients=[recipient])
    msg.body = body
    mail.send(msg)
    return f"Email sent to {recipient}"
```

## Using Tasks in Routes

```python
from app.tasks import send_email_async

@main.route('/send-notification')
def send_notification():
    # Queue the task
    send_email_async.delay('user@example.com', 'Hello', 'Test message')
    flash('Email queued for sending!', 'success')
    return redirect(url_for('main.dashboard'))
```

## Troubleshooting

### Error: "No module named 'celery'"
```bash
pip install celery redis
```

### Error: "Cannot connect to redis"
Make sure Redis server is running:
```bash
redis-server
```

### Error: "ModuleNotFoundError: No module named 'app'"
Make sure you're running from the project root directory where `celery_worker.py` is located.

## Windows-Specific Notes

On Windows, you may need to use:
```bash
celery -A celery_worker.celery worker --loglevel=info --pool=solo
```

The `--pool=solo` flag is required on Windows as it doesn't support the default pool.
