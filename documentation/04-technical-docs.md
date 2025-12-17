# 🔧 UniPortal - Technical Documentation

## Table of Contents

1. [Development Environment Setup](#development-environment-setup)
2. [Database Management](#database-management)
3. [API Documentation](#api-documentation)
4. [Code Structure](#code-structure)
5. [Configuration Management](#configuration-management)
6. [Security Implementation](#security-implementation)
7. [Performance Optimization](#performance-optimization)
8. [Maintenance Procedures](#maintenance-procedures)

---

## Development Environment Setup

### Prerequisites

#### System Requirements
- **Python**: 3.8 or higher
- **Node.js**: 14+ (for PWA tools, optional)
- **Redis**: 6.0+ (for caching and Celery)
- **Git**: For version control

#### Python Dependencies
```bash
# Core Framework
Flask==2.3.3
Flask-SQLAlchemy==3.0.5
Flask-Login==0.6.3
Flask-Mail==0.9.1
Flask-SocketIO==5.3.6

# Database
SQLAlchemy==2.0.21
Alembic==1.12.0

# Background Tasks
Celery==5.3.2
Redis==4.6.0

# Security
Werkzeug==2.3.7
cryptography==41.0.4

# External Services
requests==2.31.0
pywebpush==1.14.0

# Development Tools
python-dotenv==1.0.0
```

### Installation Steps

#### 1. Clone Repository
```bash
git clone <repository-url>
cd uniportal
```

#### 2. Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 4. Environment Configuration
Create `.env` file in project root:
```env
# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///uniportal.db

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=465
MAIL_USE_SSL=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Paystack Configuration
PAYSTACK_SECRET_KEY=sk_test_your_secret_key
PAYSTACK_PUBLIC_KEY=pk_test_your_public_key

# VAPID Keys (for push notifications)
VAPID_PRIVATE_KEY=your-vapid-private-key
VAPID_PUBLIC_KEY=your-vapid-public-key
```

#### 5. Database Initialization
```bash
# Initialize database with default data
python run.py

# Or manually initialize
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
```

#### 6. Start Development Server
```bash
# HTTP (basic development)
python run.py

# HTTPS (for geolocation testing)
python run.py --https
```

### Development Tools

#### Code Quality Tools
```bash
# Install development dependencies
pip install flake8 black pytest pytest-cov

# Code formatting
black app/ *.py

# Linting
flake8 app/ --max-line-length=88

# Testing
pytest tests/ -v --cov=app
```

#### Database Tools
```bash
# Database migrations (if using Alembic)
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# Database inspection
python -c "from app import create_app, db; from app.models import *; app = create_app(); app.app_context().push(); print(db.engine.table_names())"
```

---

## Database Management

### Database Schema

#### Core Models Overview
```python
# University Management
class University(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    domain = db.Column(db.String(100), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Class Organization
class ClassGroup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    join_code = db.Column(db.String(10), unique=True, nullable=False)
    lecturer_code = db.Column(db.String(10), unique=True, nullable=False)
    subscription_plan = db.Column(db.String(20), default='free')
    premium_expiry = db.Column(db.DateTime, nullable=True)
    storage_used_mb = db.Column(db.Float, default=0.0)
    storage_limit_gb = db.Column(db.Float, default=0.05)

# User Management
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='Student')
    is_verified = db.Column(db.Boolean, default=False)
```

### Database Operations

#### Common Queries
```python
# User Management
def get_user_by_email(email):
    return User.query.filter_by(email=email).first()

def get_class_members(class_group_id):
    return User.query.filter_by(class_group_id=class_group_id).all()

# Class Management
def get_class_by_join_code(join_code):
    return ClassGroup.query.filter_by(join_code=join_code.upper()).first()

def get_premium_classes():
    return ClassGroup.query.filter(
        ClassGroup.premium_expiry > datetime.utcnow()
    ).all()

# Assignment Management
def get_ungraded_assignments():
    return Assignment.query.filter_by(grade=None).all()

def get_user_assignments(user_id):
    return Assignment.query.filter_by(user_id=user_id).order_by(
        Assignment.created_at.desc()
    ).all()
```

#### Database Maintenance
```python
# Cleanup old files
def cleanup_orphaned_files():
    """Remove files that no longer have database records"""
    import os
    from app.models import Assignment, Resource
    
    # Get all file paths from database
    db_files = set()
    for assignment in Assignment.query.all():
        db_files.add(assignment.file_path)
    for resource in Resource.query.all():
        db_files.add(resource.file_path)
    
    # Check filesystem for orphaned files
    upload_dir = 'app/uploads'
    for root, dirs, files in os.walk(upload_dir):
        for file in files:
            file_path = os.path.join(root, file)
            if file_path not in db_files:
                os.remove(file_path)
                print(f"Removed orphaned file: {file_path}")

# Update storage usage
def update_storage_usage(class_group_id):
    """Recalculate storage usage for a class group"""
    from app.models import ClassGroup, Assignment, Resource
    import os
    
    class_group = ClassGroup.query.get(class_group_id)
    if not class_group:
        return
    
    total_size = 0
    
    # Calculate assignment file sizes
    assignments = Assignment.query.join(User).filter(
        User.class_group_id == class_group_id
    ).all()
    
    for assignment in assignments:
        if os.path.exists(assignment.file_path):
            total_size += os.path.getsize(assignment.file_path)
    
    # Calculate resource file sizes
    resources = Resource.query.filter_by(class_group_id=class_group_id).all()
    for resource in resources:
        if os.path.exists(resource.file_path):
            total_size += os.path.getsize(resource.file_path)
    
    # Update database
    class_group.storage_used_mb = total_size / (1024 * 1024)  # Convert to MB
    db.session.commit()
```

### Migration Scripts

#### Adding New Columns
```python
# migrate_add_column.py
from app import create_app, db
from app.models import ClassGroup

def add_new_column():
    app = create_app()
    with app.app_context():
        # Add column using raw SQL if needed
        db.engine.execute(
            "ALTER TABLE class_groups ADD COLUMN new_column VARCHAR(50) DEFAULT 'default_value'"
        )
        db.session.commit()
        print("Column added successfully")

if __name__ == '__main__':
    add_new_column()
```

---

## API Documentation

### Authentication Endpoints

#### POST /register
Register a new user account.

**Request Body:**
```json
{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "password123",
    "full_name": "John Doe",
    "role": "Student",
    "join_code": "CS100"
}
```

**Response:**
```json
{
    "status": "success",
    "message": "Registration successful. Please check your email for verification.",
    "user_id": 123
}
```

#### POST /login
Authenticate user and create session.

**Request Body:**
```json
{
    "username": "john_doe",
    "password": "password123"
}
```

**Response:**
```json
{
    "status": "success",
    "message": "Login successful",
    "redirect_url": "/student_dashboard"
}
```

### File Upload Endpoints

#### POST /submit_assignment
Submit an assignment file.

**Headers:**
```
Content-Type: multipart/form-data
Authorization: Session-based (login required)
```

**Form Data:**
```
file: [binary file data]
course_id: 1
notes: "Assignment submission notes"
```

**Response:**
```json
{
    "status": "success",
    "message": "Assignment submitted successfully",
    "assignment_id": 456,
    "similarity_score": 15.2
}
```

### Real-time Communication

#### Socket.IO Events

**Client → Server Events:**
```javascript
// Join class chat room
socket.emit('join_class', {
    'class_group_id': 1
});

// Send chat message
socket.emit('send_message', {
    'message': 'Hello everyone!',
    'class_group_id': 1
});

// Mark user as typing
socket.emit('typing', {
    'class_group_id': 1,
    'is_typing': true
});
```

**Server → Client Events:**
```javascript
// Receive chat message
socket.on('receive_message', function(data) {
    console.log('New message:', data.message);
    console.log('From:', data.username);
    console.log('Time:', data.timestamp);
});

// User joined/left notifications
socket.on('user_joined', function(data) {
    console.log(data.username + ' joined the chat');
});

// Typing indicators
socket.on('user_typing', function(data) {
    console.log(data.username + ' is typing...');
});
```

### Payment Integration

#### POST /initiate_payment
Initialize Paystack payment for subscription.

**Request Body:**
```json
{
    "plan_name": "gold",
    "duration_semesters": 2
}
```

**Response:**
```json
{
    "status": "success",
    "authorization_url": "https://checkout.paystack.com/...",
    "reference": "UNIPORTAL_ABC123"
}
```

#### GET /payment/callback
Handle Paystack payment callback.

**Query Parameters:**
```
reference: UNIPORTAL_ABC123
```

**Response:**
```json
{
    "status": "success",
    "message": "Payment verified and subscription activated"
}
```

---

## Code Structure

### Application Factory Pattern

#### app/__init__.py
```python
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
socketio = SocketIO()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = 'your-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///uniportal.db'
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    socketio.init_app(app)
    
    # Register blueprints
    from app.routes import main
    app.register_blueprint(main)
    
    return app
```

### Route Organization

#### app/routes.py Structure
```python
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from functools import wraps

main = Blueprint('main', __name__)

# Decorators
def premium_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.class_group.is_active_premium:
            flash('Premium subscription required', 'warning')
            return redirect(url_for('main.subscription'))
        return f(*args, **kwargs)
    return decorated_function

# Authentication Routes
@main.route('/login', methods=['GET', 'POST'])
def login():
    # Login logic
    pass

@main.route('/register', methods=['GET', 'POST'])
def register():
    # Registration logic
    pass

# Dashboard Routes
@main.route('/student_dashboard')
@login_required
def student_dashboard():
    # Student dashboard logic
    pass

@main.route('/lecturer_dashboard')
@login_required
def lecturer_dashboard():
    # Lecturer dashboard logic
    pass

# Premium Features
@main.route('/library')
@login_required
@premium_required
def library():
    # Library access logic
    pass
```

### Model Relationships

#### app/models.py Relationships
```python
class University(db.Model):
    # One-to-many with ClassGroup
    class_groups = db.relationship('ClassGroup', backref='university', lazy=True)
    
    # One-to-many with User
    users = db.relationship('User', backref='university', lazy=True)

class ClassGroup(db.Model):
    # One-to-many with User
    users = db.relationship('User', backref='class_group', lazy=True)
    
    # One-to-many with Course
    courses = db.relationship('Course', backref='class_group', lazy=True)
    
    # Many-to-one with University
    university_id = db.Column(db.Integer, db.ForeignKey('universities.id'))

class User(UserMixin, db.Model):
    # Many-to-one with ClassGroup
    class_group_id = db.Column(db.Integer, db.ForeignKey('class_groups.id'))
    
    # Many-to-one with University
    university_id = db.Column(db.Integer, db.ForeignKey('universities.id'))
    
    # One-to-many with Assignment
    assignments = db.relationship('Assignment', backref='user', lazy=True)
```

### Background Tasks

#### app/tasks.py
```python
from celery import Celery
from app import create_app, db, mail
from flask_mail import Message

# Initialize Celery
celery = Celery('uniportal')

@celery.task
def send_email_async(subject, recipients, body):
    """Send email asynchronously"""
    app = create_app()
    with app.app_context():
        msg = Message(subject=subject, recipients=recipients, body=body)
        mail.send(msg)
    return f"Email sent to {recipients}"

@celery.task
def cleanup_old_files():
    """Clean up old uploaded files"""
    app = create_app()
    with app.app_context():
        # Cleanup logic here
        pass

@celery.task
def update_subscription_status():
    """Update expired subscriptions"""
    app = create_app()
    with app.app_context():
        from app.models import ClassGroup
        from datetime import datetime
        
        expired_classes = ClassGroup.query.filter(
            ClassGroup.premium_expiry < datetime.utcnow()
        ).all()
        
        for class_group in expired_classes:
            class_group.subscription_plan = 'free'
            class_group.storage_limit_gb = 0.1
            class_group.max_file_size_mb = 2
        
        db.session.commit()
        return f"Updated {len(expired_classes)} expired subscriptions"
```

---

## Configuration Management

### Environment-Specific Configuration

#### config.py
```python
import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Mail Configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 465)
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # Celery Configuration
    CELERY_BROKER_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    
    # File Upload Configuration
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'app', 'uploads')
    
    # Session Configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///uniportal.db'

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://user:pass@localhost/uniportal'
    
    # Security Headers
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
```

### Feature Flags

#### Feature Toggle System
```python
# app/utils/feature_flags.py
class FeatureFlags:
    # Core Features
    CHAT_ENABLED = True
    FORUM_ENABLED = True
    LIBRARY_ENABLED = True
    
    # Premium Features
    ADVANCED_ANALYTICS = True
    BULK_OPERATIONS = True
    CUSTOM_BRANDING = False
    
    # Experimental Features
    AI_PLAGIARISM_DETECTION = False
    VIDEO_CHAT = False
    MOBILE_APP_INTEGRATION = False
    
    @classmethod
    def is_enabled(cls, feature_name):
        return getattr(cls, feature_name, False)

# Usage in routes
from app.utils.feature_flags import FeatureFlags

@main.route('/advanced_analytics')
@login_required
def advanced_analytics():
    if not FeatureFlags.is_enabled('ADVANCED_ANALYTICS'):
        flash('Feature not available', 'info')
        return redirect(url_for('main.dashboard'))
    
    # Feature logic here
    pass
```

---

## Security Implementation

### Authentication Security

#### Password Hashing
```python
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    password_hash = db.Column(db.String(200), nullable=False)
    
    def set_password(self, password):
        """Hash and store password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password against hash"""
        return check_password_hash(self.password_hash, password)
```

#### Session Management
```python
from flask_login import LoginManager
from datetime import timedelta

login_manager = LoginManager()
login_manager.login_view = 'main.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.session_protection = 'strong'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Session timeout
app.permanent_session_lifetime = timedelta(hours=24)
```

### Input Validation

#### Form Validation
```python
from werkzeug.utils import secure_filename
import re

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_username(username):
    """Validate username format"""
    if len(username) < 3 or len(username) > 20:
        return False
    pattern = r'^[a-zA-Z0-9_]+$'
    return re.match(pattern, username) is not None

def validate_file_upload(file):
    """Validate uploaded file"""
    if not file or file.filename == '':
        return False, "No file selected"
    
    # Check file extension
    allowed_extensions = {'pdf', 'doc', 'docx', 'txt', 'ppt', 'pptx'}
    if not ('.' in file.filename and 
            file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
        return False, "File type not allowed"
    
    # Check file size (example: 50MB limit)
    file.seek(0, 2)  # Seek to end
    file_size = file.tell()
    file.seek(0)  # Reset to beginning
    
    if file_size > 50 * 1024 * 1024:  # 50MB
        return False, "File too large"
    
    return True, "Valid file"
```

### CSRF Protection

#### CSRF Implementation
```python
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    csrf.init_app(app)
    
    # CSRF error handler
    @app.errorhandler(400)
    def csrf_error(reason):
        return render_template('csrf_error.html', reason=reason), 400
    
    return app
```

### File Security

#### Secure File Handling
```python
import os
from werkzeug.utils import secure_filename

def save_uploaded_file(file, user_id, category='assignments'):
    """Securely save uploaded file"""
    if not file:
        return None
    
    # Secure filename
    filename = secure_filename(file.filename)
    
    # Create user-specific directory
    user_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    
    # Generate unique filename to prevent conflicts
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    name, ext = os.path.splitext(filename)
    unique_filename = f"{name}_{timestamp}{ext}"
    
    file_path = os.path.join(user_dir, unique_filename)
    file.save(file_path)
    
    return file_path

def serve_secure_file(file_path, user_id):
    """Serve file with access control"""
    # Verify user has access to this file
    if not os.path.exists(file_path):
        abort(404)
    
    # Check if user owns the file or has permission
    if str(user_id) not in file_path and not current_user.role in ['Admin', 'Lecturer']:
        abort(403)
    
    return send_file(file_path)
```

---

## Performance Optimization

### Database Optimization

#### Query Optimization
```python
# Efficient relationship loading
def get_class_with_users(class_id):
    """Load class with users in single query"""
    return ClassGroup.query.options(
        db.joinedload(ClassGroup.users)
    ).get(class_id)

# Pagination for large datasets
def get_assignments_paginated(page=1, per_page=20):
    """Get assignments with pagination"""
    return Assignment.query.order_by(
        Assignment.created_at.desc()
    ).paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )

# Bulk operations
def bulk_update_grades(assignment_grades):
    """Update multiple grades efficiently"""
    for assignment_id, grade in assignment_grades.items():
        db.session.execute(
            Assignment.__table__.update()
            .where(Assignment.id == assignment_id)
            .values(grade=grade)
        )
    db.session.commit()
```

#### Database Indexing
```sql
-- Add indexes for frequently queried columns
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_class_group_id ON users(class_group_id);
CREATE INDEX idx_assignments_user_id ON assignments(user_id);
CREATE INDEX idx_assignments_created_at ON assignments(created_at);
CREATE INDEX idx_class_groups_join_code ON class_groups(join_code);
```

### Caching Strategy

#### Redis Caching
```python
import redis
import json
from functools import wraps

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache_result(expiration=300):
    """Decorator to cache function results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            cached_result = redis_client.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            redis_client.setex(
                cache_key, 
                expiration, 
                json.dumps(result, default=str)
            )
            return result
        return wrapper
    return decorator

# Usage example
@cache_result(expiration=600)  # Cache for 10 minutes
def get_class_statistics(class_id):
    """Get class statistics with caching"""
    class_group = ClassGroup.query.get(class_id)
    return {
        'total_students': len(class_group.users),
        'total_assignments': len(class_group.assignments),
        'average_grade': calculate_average_grade(class_id)
    }
```

### File Handling Optimization

#### Efficient File Processing
```python
import hashlib
from werkzeug.datastructures import FileStorage

def calculate_file_hash(file_path):
    """Calculate file hash efficiently"""
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

def stream_file_upload(file: FileStorage, destination: str):
    """Stream large file uploads"""
    with open(destination, 'wb') as f:
        while True:
            chunk = file.stream.read(4096)
            if not chunk:
                break
            f.write(chunk)

def compress_uploaded_image(file_path, max_size=(800, 600)):
    """Compress uploaded images"""
    try:
        from PIL import Image
        
        with Image.open(file_path) as img:
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            img.save(file_path, optimize=True, quality=85)
    except ImportError:
        # PIL not available, skip compression
        pass
```

---

## Maintenance Procedures

### Regular Maintenance Tasks

#### Database Maintenance
```python
# cleanup_database.py
from app import create_app, db
from app.models import *
from datetime import datetime, timedelta
import os

def cleanup_old_records():
    """Remove old records and files"""
    app = create_app()
    with app.app_context():
        # Remove old verification codes (older than 24 hours)
        old_users = User.query.filter(
            User.is_verified == False,
            User.created_at < datetime.utcnow() - timedelta(hours=24)
        ).all()
        
        for user in old_users:
            db.session.delete(user)
        
        # Remove old password reset tokens
        expired_tokens = User.query.filter(
            User.password_reset_expires < datetime.utcnow()
        ).all()
        
        for user in expired_tokens:
            user.password_reset_token = None
            user.password_reset_expires = None
        
        db.session.commit()
        print(f"Cleaned up {len(old_users)} unverified users")

def update_storage_usage():
    """Update storage usage for all class groups"""
    app = create_app()
    with app.app_context():
        class_groups = ClassGroup.query.all()
        
        for class_group in class_groups:
            total_size = 0
            
            # Calculate total file size for this class
            for user in class_group.users:
                for assignment in user.assignments:
                    if os.path.exists(assignment.file_path):
                        total_size += os.path.getsize(assignment.file_path)
            
            for resource in class_group.resources:
                if os.path.exists(resource.file_path):
                    total_size += os.path.getsize(resource.file_path)
            
            class_group.storage_used_mb = total_size / (1024 * 1024)
        
        db.session.commit()
        print(f"Updated storage usage for {len(class_groups)} class groups")

if __name__ == '__main__':
    cleanup_old_records()
    update_storage_usage()
```

#### Log Rotation
```python
# log_management.py
import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logging(app):
    """Set up application logging"""
    if not app.debug:
        # Create logs directory
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        # Set up file handler with rotation
        file_handler = RotatingFileHandler(
            'logs/uniportal.log', 
            maxBytes=10240000,  # 10MB
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

### Backup Procedures

#### Database Backup
```bash
#!/bin/bash
# backup_database.sh

# Configuration
DB_PATH="instance/uniportal.db"
BACKUP_DIR="backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/uniportal_backup_$DATE.db"

# Create backup directory
mkdir -p $BACKUP_DIR

# Create database backup
cp $DB_PATH $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

# Remove backups older than 30 days
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete

echo "Database backup completed: $BACKUP_FILE.gz"
```

#### File System Backup
```bash
#!/bin/bash
# backup_files.sh

# Configuration
UPLOAD_DIR="app/uploads"
BACKUP_DIR="backups/files"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/uploads_backup_$DATE.tar.gz"

# Create backup directory
mkdir -p $BACKUP_DIR

# Create compressed archive
tar -czf $BACKUP_FILE $UPLOAD_DIR

# Remove backups older than 7 days
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "File backup completed: $BACKUP_FILE"
```

### Monitoring and Health Checks

#### Health Check Endpoint
```python
@main.route('/health')
def health_check():
    """System health check endpoint"""
    try:
        # Check database connection
        db.session.execute('SELECT 1')
        
        # Check Redis connection
        redis_client.ping()
        
        # Check disk space
        import shutil
        total, used, free = shutil.disk_usage('/')
        disk_usage_percent = (used / total) * 100
        
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'database': 'connected',
            'redis': 'connected',
            'disk_usage_percent': round(disk_usage_percent, 2),
            'version': '1.0.0'
        }
        
        if disk_usage_percent > 90:
            health_status['status'] = 'warning'
            health_status['warnings'] = ['High disk usage']
        
        return jsonify(health_status)
    
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500
```

#### Performance Monitoring
```python
import time
from functools import wraps

def monitor_performance(func):
    """Decorator to monitor function performance"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Log slow operations
        if execution_time > 1.0:  # Log operations taking more than 1 second
            current_app.logger.warning(
                f"Slow operation: {func.__name__} took {execution_time:.2f} seconds"
            )
        
        return result
    return wrapper

# Usage
@main.route('/slow_operation')
@monitor_performance
def slow_operation():
    # Operation logic here
    pass
```

---

*Document Version: 1.0*  
*Last Updated: December 16, 2024*  
*Status: Final*