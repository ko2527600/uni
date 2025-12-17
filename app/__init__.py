from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_socketio import SocketIO
from celery import Celery
import os

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
socketio = SocketIO()

def make_celery(app):
    """Create Celery instance and configure it with Flask app context"""
    celery = Celery(
        app.import_name,
        backend=app.config.get('result_backend', 'rpc://'),
        broker=app.config.get('broker_url', 'redis://localhost:6379/0')
    )
    
    # Update celery config with modern lowercase keys
    celery.conf.update(
        broker_url=app.config.get('broker_url'),
        result_backend=app.config.get('result_backend'),
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
    )
    
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///uniportal.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    
    # Flask-Mail Configuration
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 465
    app.config['MAIL_USE_TLS'] = False
    app.config['MAIL_USE_SSL'] = True
    app.config['MAIL_USERNAME'] = 'ko2527600@gmail.com'
    app.config['MAIL_PASSWORD'] = 'ymgnbniuurwicive'
    app.config['MAIL_DEFAULT_SENDER'] = 'ko2527600@gmail.com'
    app.config['MAIL_MAX_EMAILS'] = None
    app.config['MAIL_ASCII_ATTACHMENTS'] = False
    
    # Celery Configuration (Remote Redis Server) - Modern lowercase keys
    app.config['broker_url'] = 'redis://100.73.7.99:6379/0'
    app.config['result_backend'] = 'redis://100.73.7.99:6379/0'
    
    # Paystack Configuration
    app.config['PAYSTACK_SECRET_KEY'] = 'sk_live_9c4455eb5c73333b8897bc9d87e4d7af0f200d9e'
    app.config['PAYSTACK_PUBLIC_KEY'] = 'pk_live_f63cc192ec5f2867f5399bf64c67b78427f1ec19'
    
    # Create uploads folder if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'
    mail.init_app(app)
    
    # Initialize SocketIO
    socketio.init_app(app, cors_allowed_origins="*")
    
    # Initialize Celery
    celery = make_celery(app)
    app.extensions['celery'] = celery
    
    # Register blueprints
    from app.routes import main
    app.register_blueprint(main)
    
    # Register SocketIO events
    from app import events
    
    # Context processor for subscription status and device detection
    @app.context_processor
    def inject_global_context():
        from flask_login import current_user
        from datetime import datetime
        from app.utils.device_detection import device_detector
        
        # Device detection
        device_info = device_detector.get_device_info()
        
        # Subscription status
        subscription_data = {
            'is_premium': False,
            'days_remaining': 0,
            'premium_expiry': None
        }
        
        if current_user.is_authenticated and current_user.class_group:
            is_premium = current_user.class_group.is_active_premium
            
            # Calculate days remaining
            days_remaining = 0
            if current_user.class_group.premium_expiry:
                delta = current_user.class_group.premium_expiry - datetime.utcnow()
                days_remaining = max(0, delta.days)
            
            subscription_data = {
                'is_premium': is_premium,
                'days_remaining': days_remaining,
                'premium_expiry': current_user.class_group.premium_expiry
            }
        
        # Combine all context data
        return {
            **subscription_data,
            **device_info
        }
    
    return app

@login_manager.user_loader
def load_user(user_id):
    from app.models import User
    return User.query.get(int(user_id))
