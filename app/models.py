from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class University(db.Model):
    __tablename__ = 'universities'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    domain = db.Column(db.String(100), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    users = db.relationship('User', backref='university', lazy=True)
    class_groups = db.relationship('ClassGroup', backref='university', lazy=True)
    
    def __repr__(self):
        return f'<University {self.name}>'

class ClassGroup(db.Model):
    __tablename__ = 'class_groups'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    code = db.Column(db.String(50), nullable=False)
    join_code = db.Column(db.String(10), unique=True, nullable=False)
    lecturer_code = db.Column(db.String(10), unique=True, nullable=False)
    lecturer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    university_id = db.Column(db.Integer, db.ForeignKey('universities.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    premium_expiry = db.Column(db.DateTime, nullable=True)
    trial_used = db.Column(db.Boolean, default=False)
    
    # New subscription fields
    subscription_plan = db.Column(db.String(20), default='free')  # 'free', 'gold', 'platinum'
    storage_used_mb = db.Column(db.Float, default=0.0)
    storage_limit_gb = db.Column(db.Float, default=0.05)  # 50MB for free tier
    max_file_size_mb = db.Column(db.Integer, default=0)  # No uploads for free tier
    subscription_expiry = db.Column(db.DateTime, nullable=True)
    
    users = db.relationship('User', backref='class_group', lazy=True, foreign_keys='User.class_group_id')
    lecturer = db.relationship('User', foreign_keys=[lecturer_id], backref='teaching_class')
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_classes')
    
    @property
    def is_active_premium(self):
        """Check if premium subscription is active"""
        if self.premium_expiry is None:
            return False
        return self.premium_expiry > datetime.utcnow()
    
    @staticmethod
    def get_pricing_tiers():
        """Get available subscription pricing tiers"""
        return {
            'gold': {
                'base_price': 250,
                'name': 'Gold Plan'
            },
            'platinum': {
                'base_price': 450,
                'name': 'Platinum Plan'
            }
        }
    
    @staticmethod
    def get_duration_discounts():
        """Get available duration options with discounts"""
        return {
            1: {
                'label': '1 Semester',
                'multiplier': 1.0
            },
            2: {
                'label': '2 Semesters (1 Year)',
                'multiplier': 0.9
            },
            4: {
                'label': '4 Semesters (2 Years)',
                'multiplier': 0.8
            }
        }
    
    def upgrade_subscription(self, plan_name, duration_semesters=1):
        """Upgrade subscription plan with multi-semester duration support"""
        # Calculate expiry (4 months per semester)
        self.subscription_expiry = datetime.utcnow() + relativedelta(months=4 * duration_semesters)
        
        # Set tier-specific limits
        if plan_name == 'gold':
            self.storage_limit_gb = 8.0
            self.max_file_size_mb = 15
        elif plan_name == 'platinum':
            self.storage_limit_gb = 30.0
            self.max_file_size_mb = 50
        elif plan_name == 'free':
            self.storage_limit_gb = 0.1  # 100MB
            self.max_file_size_mb = 2
        
        # Update subscription plan
        self.subscription_plan = plan_name
        
        # Commit changes
        db.session.commit()
    
    @staticmethod
    def calculate_subscription_price(base_price, duration_semesters):
        """Calculate subscription price with multi-semester discounts"""
        duration_discounts = ClassGroup.get_duration_discounts()
        
        # Get multiplier (default to 1.0 if duration not in predefined options)
        multiplier = duration_discounts.get(duration_semesters, {}).get('multiplier', 1.0)
        
        # Calculate total price
        total_price = base_price * duration_semesters * multiplier
        
        return total_price
    
    def check_upload_permission(self, file_size_mb):
        """Check if file upload is allowed based on subscription limits"""
        # Check 1: File size limit
        if file_size_mb > self.max_file_size_mb:
            return False
        
        # Check 2: Subscription expiry (allow if free plan OR subscription is active)
        if self.subscription_plan != 'free':
            if not self.subscription_expiry or self.subscription_expiry < datetime.utcnow():
                return False
        
        # Check 3: Storage space limit
        storage_limit_mb = self.storage_limit_gb * 1024
        if (self.storage_used_mb + file_size_mb) > storage_limit_mb:
            return False
        
        return True
    
    def __repr__(self):
        return f'<ClassGroup {self.name}>'

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password_hash = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(100), nullable=True)
    receive_emails = db.Column(db.Boolean, default=True)
    role = db.Column(db.String(20), nullable=False, default='Student')  # Student, Admin, Rep, Lecturer
    is_verified = db.Column(db.Boolean, default=False)
    verification_code = db.Column(db.String(6))
    password_reset_token = db.Column(db.String(100), nullable=True)
    password_reset_expires = db.Column(db.DateTime, nullable=True)
    university_id = db.Column(db.Integer, db.ForeignKey('universities.id'), nullable=True)
    class_group_id = db.Column(db.Integer, db.ForeignKey('class_groups.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    assignments = db.relationship('Assignment', backref='user', lazy=True)
    resources = db.relationship('Resource', backref='uploader', lazy=True)
    
    @property
    def avatar_initials(self):
        """Generate initials for avatar from full_name or username"""
        if self.full_name and self.full_name.strip():
            # Get first letter of each word
            words = self.full_name.strip().split()
            if len(words) >= 2:
                return (words[0][0] + words[-1][0]).upper()
            elif len(words) == 1:
                return words[0][:2].upper()
        # Fallback to username
        return self.username[:2].upper()
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def generate_password_reset_token(self):
        """Generate a secure password reset token"""
        import secrets
        self.password_reset_token = secrets.token_urlsafe(32)
        self.password_reset_expires = datetime.utcnow() + timedelta(hours=1)  # Token expires in 1 hour
        return self.password_reset_token
    
    def verify_password_reset_token(self, token):
        """Verify if the password reset token is valid and not expired"""
        if not self.password_reset_token or not self.password_reset_expires:
            return False
        if self.password_reset_token != token:
            return False
        if datetime.utcnow() > self.password_reset_expires:
            return False
        return True
    
    def reset_password(self, new_password):
        """Reset password and clear reset token"""
        self.set_password(new_password)
        self.password_reset_token = None
        self.password_reset_expires = None
    
    def __repr__(self):
        return f'<User {self.username}>'

class Course(db.Model):
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    lecturer_code = db.Column(db.String(10), unique=True, nullable=False)
    lecturer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    class_group_id = db.Column(db.Integer, db.ForeignKey('class_groups.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    class_group = db.relationship('ClassGroup', backref='courses', lazy=True)
    lecturer = db.relationship('User', foreign_keys=[lecturer_id], backref='teaching_courses')
    assignments = db.relationship('Assignment', backref='course', lazy=True)
    resources = db.relationship('Resource', backref='course', lazy=True)
    
    def __repr__(self):
        return f'<Course {self.name}>'

class Assignment(db.Model):
    __tablename__ = 'assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_hash = db.Column(db.String(64), nullable=True)
    grade = db.Column(db.String(10), nullable=True)
    feedback = db.Column(db.Text, nullable=True)
    similarity_score = db.Column(db.Float, nullable=True)
    matched_assignment_id = db.Column(db.Integer, db.ForeignKey('assignments.id'), nullable=True)
    archive_link = db.Column(db.String(500), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    matched_assignment = db.relationship('Assignment', remote_side=[id], backref='matched_by', uselist=False)
    
    def __repr__(self):
        return f'<Assignment {self.filename}>'

class Resource(db.Model):
    __tablename__ = 'resources'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    author = db.Column(db.String(200), nullable=True)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(100), nullable=True)
    cover_image = db.Column(db.String(500), nullable=True)
    external_link = db.Column(db.String(500), nullable=True)
    is_approved = db.Column(db.Boolean, default=False)
    uploader_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=True)
    class_group_id = db.Column(db.Integer, db.ForeignKey('class_groups.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Resource {self.title}>'

class ClassWallet(db.Model):
    __tablename__ = 'class_wallets'
    
    id = db.Column(db.Integer, primary_key=True)
    current_balance = db.Column(db.Float, default=0.0)
    target = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ClassWallet Balance: {self.current_balance}>'

class Broadcast(db.Model):
    __tablename__ = 'broadcasts'
    
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    class_group_id = db.Column(db.Integer, db.ForeignKey('class_groups.id'), nullable=True)
    
    user = db.relationship('User', backref='broadcasts', lazy=True)
    
    def __repr__(self):
        return f'<Broadcast {self.id}: {self.message[:30]}...>'

class Slide(db.Model):
    __tablename__ = 'slides'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text, nullable=True)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    class_group_id = db.Column(db.Integer, db.ForeignKey('class_groups.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    uploader = db.relationship('User', backref='slides', lazy=True)
    
    def __repr__(self):
        return f'<Slide {self.title}>'

class ForumPost(db.Model):
    __tablename__ = 'forum_posts'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    class_group_id = db.Column(db.Integer, db.ForeignKey('class_groups.id'), nullable=False)
    
    author = db.relationship('User', backref='forum_posts', lazy=True)
    class_group = db.relationship('ClassGroup', backref='forum_posts', lazy=True)
    replies = db.relationship('ForumReply', backref='post', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ForumPost {self.title}>'

class ForumReply(db.Model):
    __tablename__ = 'forum_replies'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('forum_posts.id'), nullable=False)
    
    author = db.relationship('User', backref='forum_replies', lazy=True)
    
    def __repr__(self):
        return f'<ForumReply {self.id}>'

class TimetableEvent(db.Model):
    __tablename__ = 'timetable_events'
    
    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.String(20), nullable=False)  # Monday, Tuesday, etc.
    start_time = db.Column(db.String(10), nullable=False)  # e.g., "09:00"
    end_time = db.Column(db.String(10), nullable=False)  # e.g., "11:00"
    course_name = db.Column(db.String(200), nullable=False)
    venue = db.Column(db.String(200), nullable=False)
    class_group_id = db.Column(db.Integer, db.ForeignKey('class_groups.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    class_group = db.relationship('ClassGroup', backref='timetable_events', lazy=True)
    
    def __repr__(self):
        return f'<TimetableEvent {self.course_name} on {self.day}>'

class AttendanceSession(db.Model):
    __tablename__ = 'attendance_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    course = db.relationship('Course', backref='attendance_sessions', lazy=True)
    creator = db.relationship('User', backref='created_sessions', lazy=True)
    records = db.relationship('AttendanceRecord', backref='session', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<AttendanceSession {self.id} for Course {self.course_id}>'

class AttendanceRecord(db.Model):
    __tablename__ = 'attendance_records'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('attendance_sessions.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    student_name = db.Column(db.String(200), nullable=True)
    index_number = db.Column(db.String(50), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Present')
    
    student = db.relationship('User', backref='attendance_records', lazy=True)
    
    def __repr__(self):
        return f'<AttendanceRecord Student {self.student_id} - {self.status}>'

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    class_group_id = db.Column(db.Integer, db.ForeignKey('class_groups.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    plan_type = db.Column(db.String(20), nullable=False)  # semester, yearly, 4year
    reference = db.Column(db.String(100), unique=True, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, success, failed
    paystack_response = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    class_group = db.relationship('ClassGroup', backref='payments', lazy=True)
    user = db.relationship('User', backref='payments', lazy=True)
    
    def __repr__(self):
        return f'<Payment {self.reference} - {self.status}>'

class PushSubscription(db.Model):
    __tablename__ = 'push_subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    endpoint = db.Column(db.Text, nullable=False)
    p256dh_key = db.Column(db.Text, nullable=False)
    auth_key = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='push_subscriptions', lazy=True)
    
    def __repr__(self):
        return f'<PushSubscription {self.id} for User {self.user_id}>'
