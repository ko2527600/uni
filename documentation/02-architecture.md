# 🏗️ UniPortal - System Architecture

## 1. Architecture Overview

### 1.1 High-Level Architecture
UniPortal follows a modern web application architecture with the following key components:

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENT LAYER                             │
├─────────────────────────────────────────────────────────────┤
│  Progressive Web App (PWA)                                  │
│  ├── HTML5/CSS3/JavaScript                                  │
│  ├── Service Worker (Offline Support)                       │
│  ├── Push Notifications                                     │
│  └── Responsive Design (Mobile-First)                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 APPLICATION LAYER                           │
├─────────────────────────────────────────────────────────────┤
│  Flask Web Framework                                        │
│  ├── Routes & Controllers (app/routes.py)                   │
│  ├── Business Logic                                         │
│  ├── Authentication & Authorization                         │
│  ├── Real-time Communication (Socket.IO)                    │
│  └── Background Tasks (Celery)                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   DATA LAYER                                │
├─────────────────────────────────────────────────────────────┤
│  Database (SQLite/PostgreSQL)                               │
│  ├── User Management                                        │
│  ├── Academic Data                                          │
│  ├── Communication Records                                  │
│  └── Subscription & Payment Data                            │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Technology Stack

#### Backend Technologies
- **Framework**: Flask 2.3+
- **Database**: SQLite (Development), PostgreSQL (Production)
- **ORM**: SQLAlchemy with Flask-SQLAlchemy
- **Authentication**: Flask-Login
- **Real-time**: Socket.IO with Flask-SocketIO
- **Background Tasks**: Celery with Redis
- **Email**: Flask-Mail with SMTP
- **File Handling**: Werkzeug utilities

#### Frontend Technologies
- **Core**: HTML5, CSS3, JavaScript (ES6+)
- **PWA**: Service Worker, Web App Manifest
- **UI Framework**: Custom CSS with responsive design
- **Icons**: FontAwesome (local)
- **Real-time**: Socket.IO client
- **Push Notifications**: Web Push API

#### Infrastructure
- **Caching**: Redis
- **Message Broker**: Redis
- **File Storage**: Local filesystem (Development), Cloud storage (Production)
- **Payment Gateway**: Paystack
- **Email Service**: Gmail SMTP
- **External APIs**: Google Books API

---

## 2. System Components

### 2.1 Application Structure

```
uniportal/
├── app/                          # Main application package
│   ├── __init__.py              # App factory and configuration
│   ├── models.py                # Database models
│   ├── routes.py                # URL routes and controllers
│   ├── events.py                # Socket.IO event handlers
│   ├── tasks.py                 # Celery background tasks
│   ├── utils/                   # Utility modules
│   │   ├── __init__.py
│   │   └── device_detection.py  # Device detection utilities
│   ├── static/                  # Static assets
│   │   ├── css/                 # Stylesheets
│   │   ├── js/                  # JavaScript files
│   │   ├── manifest.json        # PWA manifest
│   │   └── sw.js               # Service worker
│   ├── templates/               # Jinja2 templates
│   └── uploads/                 # User uploaded files
├── instance/                    # Instance-specific files
│   └── uniportal.db            # SQLite database
├── documentation/               # System documentation
├── run.py                      # Application entry point
└── requirements.txt            # Python dependencies
```

### 2.2 Database Architecture

#### 2.2.1 Core Entities

```sql
-- University Management
Universities
├── id (Primary Key)
├── name
├── domain
└── created_at

-- Class Organization
ClassGroups
├── id (Primary Key)
├── name
├── code
├── join_code (Unique)
├── lecturer_code (Unique)
├── university_id (Foreign Key)
├── subscription_plan
├── premium_expiry
└── storage_limits

-- User Management
Users
├── id (Primary Key)
├── username (Unique)
├── email (Unique)
├── password_hash
├── role (Student/Lecturer/Rep/Admin)
├── university_id (Foreign Key)
├── class_group_id (Foreign Key)
└── verification_status
```

#### 2.2.2 Academic Entities

```sql
-- Course Management
Courses
├── id (Primary Key)
├── name
├── lecturer_code
├── lecturer_id (Foreign Key)
├── class_group_id (Foreign Key)
└── created_at

-- Assignment System
Assignments
├── id (Primary Key)
├── filename
├── file_path
├── file_hash
├── grade
├── similarity_score
├── user_id (Foreign Key)
├── course_id (Foreign Key)
└── created_at

-- Resource Management
Resources
├── id (Primary Key)
├── title
├── file_path
├── category
├── is_approved
├── uploader_id (Foreign Key)
├── class_group_id (Foreign Key)
└── created_at
```

#### 2.2.3 Communication Entities

```sql
-- Forum System
ForumPosts
├── id (Primary Key)
├── title
├── content
├── user_id (Foreign Key)
├── class_group_id (Foreign Key)
└── timestamp

ForumReplies
├── id (Primary Key)
├── content
├── user_id (Foreign Key)
├── post_id (Foreign Key)
└── timestamp

-- Broadcast System
Broadcasts
├── id (Primary Key)
├── message
├── user_id (Foreign Key)
├── class_group_id (Foreign Key)
└── timestamp
```

#### 2.2.4 Subscription & Payment Entities

```sql
-- Payment Management
Payments
├── id (Primary Key)
├── class_group_id (Foreign Key)
├── user_id (Foreign Key)
├── amount
├── plan_type
├── reference (Unique)
├── status
└── created_at

-- Push Notifications
PushSubscriptions
├── id (Primary Key)
├── user_id (Foreign Key)
├── endpoint
├── p256dh_key
├── auth_key
└── created_at
```

### 2.3 Authentication & Authorization

#### 2.3.1 Authentication Flow
```
1. User Registration
   ├── Email validation
   ├── Role selection
   ├── Join code verification (Students/Reps)
   └── Email verification (6-digit code)

2. Login Process
   ├── Credential validation
   ├── Session creation
   ├── Role-based redirection
   └── Device detection

3. Password Reset
   ├── Email-based token generation
   ├── Secure token validation
   └── Password update
```

#### 2.3.2 Authorization Matrix

| Role | Dashboard | Upload | Grade | Manage Class | Admin Panel |
|------|-----------|--------|-------|--------------|-------------|
| Student | ✅ | ✅ | ❌ | ❌ | ❌ |
| Lecturer | ✅ | ✅ | ✅ | ❌ | ❌ |
| Rep | ✅ | ✅ | ❌ | ✅ | ❌ |
| Admin | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## 3. Data Flow Architecture

### 3.1 Request Processing Flow

```
Client Request
      │
      ▼
┌─────────────┐
│   Routes    │ ← URL routing and request handling
│ (routes.py) │
└─────────────┘
      │
      ▼
┌─────────────┐
│ Controllers │ ← Business logic and validation
│             │
└─────────────┘
      │
      ▼
┌─────────────┐
│   Models    │ ← Database operations
│ (models.py) │
└─────────────┘
      │
      ▼
┌─────────────┐
│  Database   │ ← Data persistence
│             │
└─────────────┘
```

### 3.2 Real-time Communication Flow

```
Client Event
      │
      ▼
┌─────────────┐
│ Socket.IO   │ ← WebSocket connection
│   Client    │
└─────────────┘
      │
      ▼
┌─────────────┐
│ Socket.IO   │ ← Event handling
│   Server    │
│ (events.py) │
└─────────────┘
      │
      ▼
┌─────────────┐
│ Broadcast   │ ← Message distribution
│  to Room    │
└─────────────┘
```

### 3.3 Background Task Flow

```
Task Trigger
      │
      ▼
┌─────────────┐
│   Celery    │ ← Task queuing
│   Producer  │
└─────────────┘
      │
      ▼
┌─────────────┐
│    Redis    │ ← Message broker
│   Queue     │
└─────────────┘
      │
      ▼
┌─────────────┐
│   Celery    │ ← Task execution
│   Worker    │
│ (tasks.py)  │
└─────────────┘
```

---

## 4. Security Architecture

### 4.1 Security Layers

#### 4.1.1 Transport Security
- **HTTPS Enforcement**: All communications encrypted
- **HSTS Headers**: HTTP Strict Transport Security
- **Secure Cookies**: HTTPOnly and Secure flags
- **CSRF Protection**: Token-based validation

#### 4.1.2 Authentication Security
- **Password Hashing**: Werkzeug PBKDF2 with salt
- **Session Management**: Flask-Login with secure sessions
- **Token-based Reset**: Time-limited password reset tokens
- **Rate Limiting**: Login attempt restrictions

#### 4.1.3 Authorization Security
- **Role-based Access**: Decorator-based permission checks
- **Resource Ownership**: User-specific data access
- **Premium Features**: Subscription-based feature gates
- **File Access Control**: Secure file serving

#### 4.1.4 Data Security
- **Input Validation**: Form data sanitization
- **SQL Injection Prevention**: SQLAlchemy ORM protection
- **XSS Protection**: Template auto-escaping
- **File Upload Security**: Type and size validation

### 4.2 Security Implementation

```python
# Authentication Decorator
@login_required
def protected_route():
    # Route logic here
    pass

# Role-based Authorization
@premium_required
def premium_feature():
    # Premium feature logic
    pass

# File Security
def secure_filename_validation(filename):
    # Validate file type and name
    return allowed_file(filename)
```

---

## 5. Performance Architecture

### 5.1 Caching Strategy

#### 5.1.1 Application-Level Caching
- **Session Storage**: Redis-based session management
- **Database Query Caching**: SQLAlchemy query optimization
- **Template Caching**: Jinja2 template compilation caching

#### 5.1.2 Client-Side Caching
- **Service Worker**: PWA offline caching
- **Browser Caching**: Static asset caching headers
- **Local Storage**: User preferences and temporary data

### 5.2 Database Optimization

#### 5.2.1 Query Optimization
- **Eager Loading**: Relationship loading optimization
- **Index Strategy**: Primary and foreign key indexing
- **Query Batching**: Bulk operations for efficiency

#### 5.2.2 Connection Management
- **Connection Pooling**: SQLAlchemy connection pool
- **Transaction Management**: Proper commit/rollback handling
- **Database Migrations**: Alembic for schema changes

### 5.3 File Handling Optimization

```python
# Efficient File Processing
def process_file_upload(file):
    # Stream processing for large files
    # Hash calculation for duplicate detection
    # Secure storage with access controls
    pass
```

---

## 6. Scalability Architecture

### 6.1 Horizontal Scaling

#### 6.1.1 Application Scaling
- **Load Balancer**: Multiple Flask instances
- **Session Sharing**: Redis-based session store
- **Static Asset CDN**: Content delivery network

#### 6.1.2 Database Scaling
- **Read Replicas**: Database read scaling
- **Connection Pooling**: Efficient connection management
- **Query Optimization**: Performance monitoring

### 6.2 Vertical Scaling

#### 6.2.1 Resource Optimization
- **Memory Management**: Efficient object lifecycle
- **CPU Optimization**: Async task processing
- **Storage Optimization**: File compression and cleanup

---

## 7. Integration Architecture

### 7.1 External Service Integration

#### 7.1.1 Payment Gateway (Paystack)
```python
# Payment Processing Flow
def initiate_payment(amount, user_email):
    # Create payment record
    # Initialize Paystack transaction
    # Handle callback verification
    # Update subscription status
    pass
```

#### 7.1.2 Email Service Integration
```python
# Email Notification System
def send_notification_email(user, subject, template):
    # Template rendering
    # SMTP delivery
    # Delivery tracking
    pass
```

#### 7.1.3 External APIs
- **Google Books API**: Library resource integration
- **Geolocation Services**: Attendance tracking
- **Push Notification Services**: Web push delivery

### 7.2 Internal Service Communication

#### 7.2.1 Real-time Communication
- **Socket.IO Rooms**: Class-based chat rooms
- **Event Broadcasting**: Multi-user notifications
- **Connection Management**: User presence tracking

#### 7.2.2 Background Processing
- **Email Queue**: Asynchronous email delivery
- **File Processing**: Background file operations
- **Cleanup Tasks**: Maintenance operations

---

## 8. Deployment Architecture

### 8.1 Development Environment
```
Local Development
├── SQLite Database
├── Flask Development Server
├── Redis (Local)
├── File Storage (Local)
└── HTTPS (Self-signed)
```

### 8.2 Production Environment
```
Production Deployment
├── PostgreSQL Database
├── WSGI Server (Gunicorn)
├── Reverse Proxy (Nginx)
├── Redis Cluster
├── Cloud File Storage
├── SSL Certificate (Let's Encrypt)
└── Process Management (Supervisor)
```

### 8.3 Monitoring & Logging
- **Application Logs**: Structured logging with rotation
- **Error Tracking**: Exception monitoring and alerting
- **Performance Metrics**: Response time and throughput
- **Health Checks**: Service availability monitoring

---

*Document Version: 1.0*  
*Last Updated: December 16, 2024*  
*Status: Final*