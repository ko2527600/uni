# 🚀 UniPortal - Deployment Guide

## Table of Contents

1. [Deployment Overview](#deployment-overview)
2. [Development Deployment](#development-deployment)
3. [Production Deployment](#production-deployment)
4. [Cloud Deployment](#cloud-deployment)
5. [Configuration Management](#configuration-management)
6. [Monitoring & Operations](#monitoring--operations)
7. [Backup & Recovery](#backup--recovery)
8. [Troubleshooting](#troubleshooting)

---

## Deployment Overview

### Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PRODUCTION STACK                         │
├─────────────────────────────────────────────────────────────┤
│  Load Balancer (Nginx)                                     │
│  ├── SSL Termination                                        │
│  ├── Static File Serving                                    │
│  └── Request Routing                                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 APPLICATION SERVERS                         │
├─────────────────────────────────────────────────────────────┤
│  Gunicorn (WSGI Server)                                     │
│  ├── Multiple Worker Processes                              │
│  ├── Flask Application Instances                            │
│  └── Socket.IO Support                                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   DATA SERVICES                             │
├─────────────────────────────────────────────────────────────┤
│  PostgreSQL Database                                        │
│  Redis Cache & Message Broker                               │
│  File Storage (Local/Cloud)                                 │
└─────────────────────────────────────────────────────────────┘
```

### Deployment Environments

| Environment | Purpose | Database | Caching | SSL | Monitoring |
|-------------|---------|----------|---------|-----|------------|
| Development | Local development | SQLite | Optional Redis | Self-signed | Basic logging |
| Staging | Testing & QA | PostgreSQL | Redis | Let's Encrypt | Full monitoring |
| Production | Live system | PostgreSQL | Redis Cluster | Let's Encrypt | Full monitoring |

---

## Development Deployment

### Quick Start (Local Development)

#### Prerequisites
```bash
# System requirements
Python 3.8+
Git
Redis (optional for full features)
```

#### Installation Steps
```bash
# 1. Clone repository
git clone <repository-url>
cd uniportal

# 2. Create virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Initialize database
python run.py
```

#### Development Configuration
Create `.env` file:
```env
# Flask Configuration
FLASK_ENV=development
SECRET_KEY=dev-secret-key-change-in-production
DATABASE_URL=sqlite:///uniportal.db

# Email Configuration (for testing)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=465
MAIL_USE_SSL=True
MAIL_USERNAME=your-test-email@gmail.com
MAIL_PASSWORD=your-app-password

# Redis (optional)
REDIS_URL=redis://localhost:6379/0

# Paystack (test keys)
PAYSTACK_SECRET_KEY=sk_test_your_test_secret_key
PAYSTACK_PUBLIC_KEY=pk_test_your_test_public_key
```

#### Running Development Server
```bash
# HTTP server (basic development)
python run.py

# HTTPS server (for geolocation testing)
python run.py --https

# With Celery (background tasks)
# Terminal 1: Start Redis
redis-server

# Terminal 2: Start Celery worker
celery -A app.celery worker --loglevel=info

# Terminal 3: Start Flask app
python run.py
```

### Development Tools Setup

#### Code Quality Tools
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Code formatting
black app/ *.py

# Linting
flake8 app/ --max-line-length=88

# Type checking
mypy app/

# Testing
pytest tests/ -v --cov=app
```

#### Database Tools
```bash
# Database inspection
python -c "
from app import create_app, db
from app.models import *
app = create_app()
with app.app_context():
    print('Tables:', db.engine.table_names())
    print('Users:', User.query.count())
    print('Classes:', ClassGroup.query.count())
"

# Reset database
rm instance/uniportal.db
python run.py
```

---

## Production Deployment

### Server Requirements

#### Minimum System Requirements
- **CPU**: 2 cores
- **RAM**: 4GB
- **Storage**: 50GB SSD
- **OS**: Ubuntu 20.04 LTS or CentOS 8
- **Network**: 100 Mbps connection

#### Recommended System Requirements
- **CPU**: 4+ cores
- **RAM**: 8GB+
- **Storage**: 100GB+ SSD
- **OS**: Ubuntu 22.04 LTS
- **Network**: 1 Gbps connection

### Production Setup

#### 1. System Preparation
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install system dependencies
sudo apt install -y python3 python3-pip python3-venv nginx postgresql postgresql-contrib redis-server supervisor git

# Create application user
sudo useradd -m -s /bin/bash uniportal
sudo usermod -aG sudo uniportal
```

#### 2. Database Setup
```bash
# Configure PostgreSQL
sudo -u postgres psql

-- Create database and user
CREATE DATABASE uniportal;
CREATE USER uniportal_user WITH PASSWORD 'secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE uniportal TO uniportal_user;
\q

# Configure PostgreSQL for production
sudo nano /etc/postgresql/14/main/postgresql.conf
# Uncomment and modify:
# listen_addresses = 'localhost'
# max_connections = 100
# shared_buffers = 256MB

sudo systemctl restart postgresql
```

#### 3. Redis Configuration
```bash
# Configure Redis
sudo nano /etc/redis/redis.conf

# Modify these settings:
# bind 127.0.0.1
# maxmemory 256mb
# maxmemory-policy allkeys-lru

sudo systemctl restart redis-server
sudo systemctl enable redis-server
```

#### 4. Application Deployment
```bash
# Switch to application user
sudo su - uniportal

# Clone repository
git clone <repository-url> /home/uniportal/uniportal
cd /home/uniportal/uniportal

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn psycopg2-binary

# Create production configuration
nano .env
```

#### Production Environment Configuration
```env
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your-super-secure-secret-key-here
DATABASE_URL=postgresql://uniportal_user:secure_password_here@localhost/uniportal

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=465
MAIL_USE_SSL=True
MAIL_USERNAME=your-production-email@gmail.com
MAIL_PASSWORD=your-app-password

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Paystack Configuration (live keys)
PAYSTACK_SECRET_KEY=sk_live_your_live_secret_key
PAYSTACK_PUBLIC_KEY=pk_live_your_live_public_key

# Security Settings
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax
```

#### 5. Database Migration
```bash
# Initialize production database
source venv/bin/activate
python -c "
from app import create_app, db
app = create_app()
with app.app_context():
    db.create_all()
    print('Database initialized')
"

# Run setup script
python run.py --setup-only
```

### Web Server Configuration

#### Gunicorn Configuration
Create `/home/uniportal/uniportal/gunicorn.conf.py`:
```python
# Gunicorn configuration
bind = "127.0.0.1:8000"
workers = 4
worker_class = "eventlet"
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
preload_app = True
```

#### Nginx Configuration
Create `/etc/nginx/sites-available/uniportal`:
```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Security Headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";

    # File Upload Limits
    client_max_body_size 50M;

    # Static Files
    location /static {
        alias /home/uniportal/uniportal/app/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Uploads (protected)
    location /uploads {
        internal;
        alias /home/uniportal/uniportal/app/uploads;
    }

    # Socket.IO
    location /socket.io {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/uniportal /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### SSL Certificate Setup

#### Using Let's Encrypt
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Test automatic renewal
sudo certbot renew --dry-run

# Set up automatic renewal
sudo crontab -e
# Add line:
0 12 * * * /usr/bin/certbot renew --quiet
```

### Process Management

#### Supervisor Configuration
Create `/etc/supervisor/conf.d/uniportal.conf`:
```ini
[program:uniportal]
command=/home/uniportal/uniportal/venv/bin/gunicorn -c gunicorn.conf.py "app:create_app()"
directory=/home/uniportal/uniportal
user=uniportal
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/uniportal/app.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10

[program:uniportal-celery]
command=/home/uniportal/uniportal/venv/bin/celery -A app.celery worker --loglevel=info
directory=/home/uniportal/uniportal
user=uniportal
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/uniportal/celery.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
```

Start services:
```bash
# Create log directory
sudo mkdir -p /var/log/uniportal
sudo chown uniportal:uniportal /var/log/uniportal

# Update supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start uniportal:*
```

---

## Cloud Deployment

### AWS Deployment

#### EC2 Instance Setup
```bash
# Launch EC2 instance (Ubuntu 22.04 LTS)
# Instance type: t3.medium or larger
# Security groups: HTTP (80), HTTPS (443), SSH (22)

# Connect to instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# Follow production setup steps above
```

#### RDS Database Setup
```bash
# Create RDS PostgreSQL instance
# Instance class: db.t3.micro or larger
# Storage: 20GB GP2 minimum

# Update DATABASE_URL in .env
DATABASE_URL=postgresql://username:password@your-rds-endpoint:5432/uniportal
```

#### ElastiCache Redis Setup
```bash
# Create ElastiCache Redis cluster
# Node type: cache.t3.micro or larger

# Update REDIS_URL in .env
REDIS_URL=redis://your-elasticache-endpoint:6379/0
```

#### S3 File Storage (Optional)
```python
# Install boto3
pip install boto3

# Configure S3 storage
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=us-east-1

# Update file handling code to use S3
```

### DigitalOcean Deployment

#### Droplet Setup
```bash
# Create Droplet (Ubuntu 22.04)
# Size: 2GB RAM, 1 vCPU minimum

# Follow production setup steps
```

#### Managed Database
```bash
# Create managed PostgreSQL database
# Update connection string in .env
```

### Heroku Deployment

#### Heroku Configuration
Create `Procfile`:
```
web: gunicorn -c gunicorn.conf.py "app:create_app()"
worker: celery -A app.celery worker --loglevel=info
```

Create `runtime.txt`:
```
python-3.11.0
```

Deploy:
```bash
# Install Heroku CLI
# Login to Heroku
heroku login

# Create app
heroku create your-app-name

# Add PostgreSQL
heroku addons:create heroku-postgresql:hobby-dev

# Add Redis
heroku addons:create heroku-redis:hobby-dev

# Set environment variables
heroku config:set FLASK_ENV=production
heroku config:set SECRET_KEY=your-secret-key

# Deploy
git push heroku main

# Run database setup
heroku run python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
```

---

## Configuration Management

### Environment Variables

#### Production Environment Variables
```bash
# Create /home/uniportal/uniportal/.env
FLASK_ENV=production
SECRET_KEY=your-super-secure-secret-key
DATABASE_URL=postgresql://user:pass@localhost/uniportal
REDIS_URL=redis://localhost:6379/0

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=465
MAIL_USE_SSL=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Payment Gateway
PAYSTACK_SECRET_KEY=sk_live_your_live_key
PAYSTACK_PUBLIC_KEY=pk_live_your_public_key

# Security
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
WTF_CSRF_ENABLED=True

# File Upload
MAX_CONTENT_LENGTH=52428800  # 50MB
UPLOAD_FOLDER=/home/uniportal/uniportal/app/uploads

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/uniportal/app.log
```

### Configuration Validation

#### Environment Validation Script
Create `validate_config.py`:
```python
#!/usr/bin/env python3
import os
import sys
from urllib.parse import urlparse

def validate_config():
    """Validate production configuration"""
    errors = []
    warnings = []
    
    # Required variables
    required_vars = [
        'SECRET_KEY',
        'DATABASE_URL',
        'MAIL_USERNAME',
        'MAIL_PASSWORD',
        'PAYSTACK_SECRET_KEY',
        'PAYSTACK_PUBLIC_KEY'
    ]
    
    for var in required_vars:
        if not os.environ.get(var):
            errors.append(f"Missing required environment variable: {var}")
    
    # Validate SECRET_KEY strength
    secret_key = os.environ.get('SECRET_KEY', '')
    if len(secret_key) < 32:
        errors.append("SECRET_KEY should be at least 32 characters long")
    
    # Validate DATABASE_URL
    db_url = os.environ.get('DATABASE_URL', '')
    if db_url.startswith('sqlite://') and os.environ.get('FLASK_ENV') == 'production':
        warnings.append("Using SQLite in production is not recommended")
    
    # Validate Paystack keys
    paystack_secret = os.environ.get('PAYSTACK_SECRET_KEY', '')
    if paystack_secret.startswith('sk_test_') and os.environ.get('FLASK_ENV') == 'production':
        warnings.append("Using Paystack test keys in production")
    
    # Print results
    if errors:
        print("❌ Configuration Errors:")
        for error in errors:
            print(f"  - {error}")
    
    if warnings:
        print("⚠️  Configuration Warnings:")
        for warning in warnings:
            print(f"  - {warning}")
    
    if not errors and not warnings:
        print("✅ Configuration validation passed")
    
    return len(errors) == 0

if __name__ == '__main__':
    if not validate_config():
        sys.exit(1)
```

---

## Monitoring & Operations

### Application Monitoring

#### Health Check Endpoint
```python
# Add to app/routes.py
@main.route('/health')
def health_check():
    """System health check"""
    try:
        # Check database
        db.session.execute('SELECT 1')
        
        # Check Redis
        from app import redis_client
        redis_client.ping()
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0'
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500
```

#### Logging Configuration
```python
# Add to app/__init__.py
import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logging(app):
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = RotatingFileHandler(
            'logs/uniportal.log',
            maxBytes=10240000,
            backupCount=10
        )
        
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('UniPortal startup')
```

### System Monitoring

#### Nginx Monitoring
```bash
# Check Nginx status
sudo systemctl status nginx

# View Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Test Nginx configuration
sudo nginx -t
```

#### Application Monitoring
```bash
# Check application status
sudo supervisorctl status uniportal:*

# View application logs
sudo tail -f /var/log/uniportal/app.log
sudo tail -f /var/log/uniportal/celery.log

# Restart application
sudo supervisorctl restart uniportal:*
```

#### Database Monitoring
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Monitor database connections
sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity;"

# Check database size
sudo -u postgres psql -d uniportal -c "SELECT pg_size_pretty(pg_database_size('uniportal'));"
```

### Performance Monitoring

#### System Resource Monitoring
```bash
# Install monitoring tools
sudo apt install htop iotop nethogs

# Monitor system resources
htop
iotop
nethogs

# Check disk usage
df -h
du -sh /home/uniportal/uniportal/app/uploads/
```

#### Application Performance
```python
# Add performance monitoring to routes
import time
from functools import wraps

def monitor_performance(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        result = f(*args, **kwargs)
        end_time = time.time()
        
        execution_time = end_time - start_time
        if execution_time > 1.0:  # Log slow requests
            current_app.logger.warning(
                f"Slow request: {request.endpoint} took {execution_time:.2f}s"
            )
        
        return result
    return decorated_function
```

---

## Backup & Recovery

### Database Backup

#### Automated Backup Script
Create `/home/uniportal/scripts/backup_database.sh`:
```bash
#!/bin/bash

# Configuration
DB_NAME="uniportal"
DB_USER="uniportal_user"
BACKUP_DIR="/home/uniportal/backups/database"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/uniportal_backup_$DATE.sql"

# Create backup directory
mkdir -p $BACKUP_DIR

# Create database backup
pg_dump -h localhost -U $DB_USER -d $DB_NAME > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

# Remove backups older than 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "Database backup completed: $BACKUP_FILE.gz"
```

#### Database Restore
```bash
# Restore from backup
gunzip backup_file.sql.gz
sudo -u postgres psql -d uniportal < backup_file.sql
```

### File System Backup

#### File Backup Script
Create `/home/uniportal/scripts/backup_files.sh`:
```bash
#!/bin/bash

# Configuration
SOURCE_DIR="/home/uniportal/uniportal/app/uploads"
BACKUP_DIR="/home/uniportal/backups/files"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/uploads_backup_$DATE.tar.gz"

# Create backup directory
mkdir -p $BACKUP_DIR

# Create compressed archive
tar -czf $BACKUP_FILE -C $(dirname $SOURCE_DIR) $(basename $SOURCE_DIR)

# Remove backups older than 7 days
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "File backup completed: $BACKUP_FILE"
```

### Automated Backup Schedule

#### Cron Jobs
```bash
# Edit crontab
crontab -e

# Add backup jobs
# Database backup daily at 2 AM
0 2 * * * /home/uniportal/scripts/backup_database.sh

# File backup daily at 3 AM
0 3 * * * /home/uniportal/scripts/backup_files.sh

# Log cleanup weekly
0 4 * * 0 find /var/log/uniportal -name "*.log.*" -mtime +7 -delete
```

---

## Troubleshooting

### Common Issues

#### Application Won't Start
```bash
# Check logs
sudo tail -f /var/log/uniportal/app.log

# Check supervisor status
sudo supervisorctl status uniportal:*

# Restart application
sudo supervisorctl restart uniportal:*

# Check configuration
cd /home/uniportal/uniportal
source venv/bin/activate
python validate_config.py
```

#### Database Connection Issues
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test database connection
sudo -u postgres psql -d uniportal -c "SELECT version();"

# Check connection string
echo $DATABASE_URL
```

#### High Memory Usage
```bash
# Check memory usage
free -h
ps aux --sort=-%mem | head

# Restart services if needed
sudo supervisorctl restart uniportal:*
sudo systemctl restart redis-server
```

#### SSL Certificate Issues
```bash
# Check certificate status
sudo certbot certificates

# Renew certificate
sudo certbot renew

# Test SSL configuration
openssl s_client -connect your-domain.com:443
```

### Performance Issues

#### Slow Database Queries
```sql
-- Enable query logging in PostgreSQL
ALTER SYSTEM SET log_statement = 'all';
ALTER SYSTEM SET log_min_duration_statement = 1000;
SELECT pg_reload_conf();

-- Check slow queries
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
```

#### High CPU Usage
```bash
# Identify CPU-intensive processes
top -o %CPU

# Check application performance
sudo tail -f /var/log/uniportal/app.log | grep "Slow request"

# Adjust Gunicorn workers if needed
sudo nano /home/uniportal/uniportal/gunicorn.conf.py
sudo supervisorctl restart uniportal
```

### Emergency Procedures

#### Service Recovery
```bash
# Full service restart
sudo supervisorctl stop uniportal:*
sudo systemctl restart postgresql
sudo systemctl restart redis-server
sudo systemctl restart nginx
sudo supervisorctl start uniportal:*
```

#### Database Recovery
```bash
# If database is corrupted
sudo systemctl stop postgresql
sudo -u postgres pg_resetwal /var/lib/postgresql/14/main
sudo systemctl start postgresql

# Restore from backup if needed
```

#### Rollback Deployment
```bash
# Switch to previous version
cd /home/uniportal/uniportal
git log --oneline -10
git checkout <previous-commit-hash>
sudo supervisorctl restart uniportal:*
```

---

*Document Version: 1.0*  
*Last Updated: December 16, 2024*  
*Status: Final*