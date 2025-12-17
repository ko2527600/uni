from flask import Blueprint, render_template, redirect, url_for, request, flash, send_file, current_app, session, Response, jsonify, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
from werkzeug.utils import secure_filename
from functools import wraps
from app import db, mail
from app.models import User, Assignment, Resource, University, Course, TimetableEvent, AttendanceSession, AttendanceRecord, Payment, PushSubscription
from datetime import datetime, timedelta
import os
import hashlib
import random
import math
import csv
from io import StringIO
import requests

main = Blueprint('main', __name__)

@main.route('/device-info')
def device_info():
    """Test route to display device detection information"""
    from app.utils.device_detection import device_detector
    device_data = device_detector.get_device_info()
    return jsonify(device_data)

@main.route('/mobile-test')
def mobile_test():
    """Test page for mobile layout verification"""
    return render_template('mobile_test.html')

@main.route('/scroll-test')
def scroll_test():
    """Simple scroll test page without complex CSS"""
    return render_template('scroll_test.html')

@main.route('/scroll-test-simple')
def scroll_test_simple():
    """Simple scroll test page for mobile debugging"""
    return render_template('scroll_test_simple.html')

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'ppt', 'pptx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def premium_required(f):
    """
    Decorator to enforce premium subscription for specific features.
    Checks if user's class has an active premium subscription.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user has a class
        if not current_user.class_group:
            flash('🔒 You must join a class to access this feature.', 'warning')
            return redirect(url_for('main.dashboard'))
        
        # Check if class has active premium
        if not current_user.class_group.is_active_premium:
            flash('🔒 This feature requires an active premium subscription. Please contact your Class Rep to renew.', 'warning')
            return redirect(url_for('main.subscription'))
        
        return f(*args, **kwargs)
    return decorated_function

def calculate_file_hash(file_path):
    """Calculate SHA256 hash of a file"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def extract_text_from_file(file_path):
    """Extract text content from various file types"""
    try:
        if file_path.endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        elif file_path.endswith('.pdf'):
            try:
                import PyPDF2
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    text = ''
                    for page in reader.pages:
                        text += page.extract_text()
                    return text
            except:
                return ''
        elif file_path.endswith(('.doc', '.docx')):
            try:
                import docx
                doc = docx.Document(file_path)
                return '\n'.join([para.text for para in doc.paragraphs])
            except:
                return ''
        else:
            return ''
    except:
        return ''

def check_plagiarism(new_file_path, new_file_hash):
    """
    Check for plagiarism by comparing with existing assignments
    Returns: (similarity_score, matched_assignment_id)
    """
    from difflib import SequenceMatcher
    
    # Get all existing assignments except the current one
    existing_assignments = Assignment.query.filter(Assignment.file_hash != new_file_hash).all()
    
    if not existing_assignments:
        return 0.0, None
    
    # Extract text from new file
    new_text = extract_text_from_file(new_file_path)
    if not new_text:
        return 0.0, None
    
    max_similarity = 0.0
    matched_id = None
    
    # Compare with each existing assignment
    for assignment in existing_assignments:
        if os.path.exists(assignment.file_path):
            existing_text = extract_text_from_file(assignment.file_path)
            if existing_text:
                # Calculate similarity ratio
                similarity = SequenceMatcher(None, new_text, existing_text).ratio()
                similarity_percentage = similarity * 100
                
                if similarity_percentage > max_similarity:
                    max_similarity = similarity_percentage
                    matched_id = assignment.id
    
    return max_similarity, matched_id

@main.route('/')
def index():
    return redirect(url_for('main.login'))

@main.route('/subscription')
@login_required
def subscription():
    """Subscription plans page"""
    return render_template('subscription.html', 
                         current_user=current_user, 
                         class_group=current_user.class_group)

@main.route('/payment_history')
@login_required
def payment_history():
    """View payment history for current user's class"""
    if current_user.role != 'Rep':
        flash('Access denied. Rep privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    if not current_user.class_group_id:
        flash('You must create a class first.', 'error')
        return redirect(url_for('main.subscription'))
    
    # Get all payments for this class
    payments = Payment.query.filter_by(
        class_group_id=current_user.class_group_id
    ).order_by(Payment.created_at.desc()).all()
    
    # Calculate statistics
    total_spent = sum(p.amount for p in payments if p.status == 'success')
    successful_payments = len([p for p in payments if p.status == 'success'])
    failed_payments = len([p for p in payments if p.status == 'failed'])
    
    return render_template('payment_history.html',
                         payments=payments,
                         total_spent=total_spent,
                         successful_payments=successful_payments,
                         failed_payments=failed_payments)

@main.route('/analytics')
@login_required
def analytics():
    """Analytics dashboard for Reps and Admins"""
    if current_user.role == 'Student':
        flash('Access denied.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Admin Analytics (Platform-wide)
    if current_user.role == 'Admin':
        from app.models import ClassGroup
        from sqlalchemy import func
        
        # Platform statistics
        total_classes = ClassGroup.query.count()
        active_premium = ClassGroup.query.filter(
            ClassGroup.premium_expiry > datetime.utcnow()
        ).count()
        expired_classes = total_classes - active_premium
        
        total_students = User.query.filter_by(role='Student').count()
        total_lecturers = User.query.filter_by(role='Lecturer').count()
        total_reps = User.query.filter_by(role='Rep').count()
        
        # Revenue statistics
        all_payments = Payment.query.filter_by(status='success').all()
        total_revenue = sum(p.amount for p in all_payments)
        
        # Plan distribution
        semester_count = len([p for p in all_payments if p.plan_type == 'semester'])
        yearly_count = len([p for p in all_payments if p.plan_type == 'yearly'])
        
        # Recent payments
        recent_payments = Payment.query.order_by(Payment.created_at.desc()).limit(10).all()
        
        return render_template('analytics.html',
                             role='Admin',
                             total_classes=total_classes,
                             active_premium=active_premium,
                             expired_classes=expired_classes,
                             total_students=total_students,
                             total_lecturers=total_lecturers,
                             total_reps=total_reps,
                             total_revenue=total_revenue,
                             semester_count=semester_count,
                             yearly_count=yearly_count,
                             recent_payments=recent_payments)
    
    # Rep Analytics (Class-specific)
    elif current_user.role == 'Rep':
        if not current_user.class_group_id:
            flash('You must create a class first.', 'error')
            return redirect(url_for('main.rep_dashboard'))
        
        from app.models import ForumPost, ForumReply
        
        # Class statistics
        class_students = User.query.filter_by(
            class_group_id=current_user.class_group_id,
            role='Student'
        ).count()
        
        # Assignment statistics
        class_assignments = Assignment.query.join(User).filter(
            User.class_group_id == current_user.class_group_id
        ).all()
        total_assignments = len(class_assignments)
        graded_assignments = len([a for a in class_assignments if a.grade])
        pending_assignments = total_assignments - graded_assignments
        
        # Resource statistics
        class_resources = Resource.query.filter_by(
            class_group_id=current_user.class_group_id,
            category='Lecture Slides'
        ).count()
        
        # Forum statistics
        forum_posts = ForumPost.query.filter_by(
            class_group_id=current_user.class_group_id
        ).count()
        
        forum_replies = ForumReply.query.join(ForumPost).filter(
            ForumPost.class_group_id == current_user.class_group_id
        ).count()
        
        # Payment statistics
        class_payments = Payment.query.filter_by(
            class_group_id=current_user.class_group_id,
            status='success'
        ).all()
        total_spent = sum(p.amount for p in class_payments)
        
        # Subscription status
        subscription_active = current_user.class_group.is_active_premium
        days_remaining = 0
        if current_user.class_group.premium_expiry:
            delta = current_user.class_group.premium_expiry - datetime.utcnow()
            days_remaining = max(0, delta.days)
        
        return render_template('analytics.html',
                             role='Rep',
                             class_students=class_students,
                             total_assignments=total_assignments,
                             graded_assignments=graded_assignments,
                             pending_assignments=pending_assignments,
                             class_resources=class_resources,
                             forum_posts=forum_posts,
                             forum_replies=forum_replies,
                             total_spent=total_spent,
                             subscription_active=subscription_active,
                             days_remaining=days_remaining)
    
    # Lecturer Analytics
    else:
        # Get courses taught by this lecturer
        lecturer_courses = Course.query.filter_by(lecturer_id=current_user.id).all()
        
        # Assignment statistics
        total_assignments = 0
        graded_assignments = 0
        for course in lecturer_courses:
            course_assignments = Assignment.query.filter_by(course_id=course.id).all()
            total_assignments += len(course_assignments)
            graded_assignments += len([a for a in course_assignments if a.grade])
        
        pending_assignments = total_assignments - graded_assignments
        
        # Attendance statistics
        attendance_sessions = AttendanceSession.query.filter_by(
            created_by_id=current_user.id
        ).count()
        
        return render_template('analytics.html',
                             role='Lecturer',
                             total_courses=len(lecturer_courses),
                             total_assignments=total_assignments,
                             graded_assignments=graded_assignments,
                             pending_assignments=pending_assignments,
                             attendance_sessions=attendance_sessions)

@main.route('/initiate_payment', methods=['POST'])
@login_required
def initiate_payment():
    """Initiate Paystack payment with new subscription model"""
    if current_user.role != 'Rep':
        flash('Only Class Reps can purchase subscriptions.', 'error')
        return redirect(url_for('main.subscription'))
    
    if not current_user.class_group_id:
        flash('You must create a class first.', 'error')
        return redirect(url_for('main.subscription'))
    
    # Get form data
    plan_name = request.form.get('plan_name')  # 'gold' or 'platinum'
    duration_semesters = int(request.form.get('duration_semesters', 1))  # 1, 2, or 4
    
    # Import ClassGroup for pricing calculation
    from app.models import ClassGroup
    
    # Get pricing tiers and duration discounts
    pricing_tiers = ClassGroup.get_pricing_tiers()
    duration_discounts = ClassGroup.get_duration_discounts()
    
    # Validate inputs
    if plan_name not in pricing_tiers:
        flash('Invalid plan selected.', 'error')
        return redirect(url_for('main.subscription'))
    
    if duration_semesters not in duration_discounts:
        flash('Invalid duration selected.', 'error')
        return redirect(url_for('main.subscription'))
    
    # Calculate pricing
    base_price = pricing_tiers[plan_name]['base_price']
    total_amount_ghs = ClassGroup.calculate_subscription_price(base_price, duration_semesters)
    amount_pesewas = int(total_amount_ghs * 100)  # Convert to pesewas for Paystack
    
    plan = {
        'amount': amount_pesewas,
        'name': f"{pricing_tiers[plan_name]['name']} - {duration_discounts[duration_semesters]['label']}",
        'plan_name': plan_name,
        'duration_semesters': duration_semesters
    }
    
    # Generate unique reference
    import secrets
    reference = f'UNIPORTAL_{secrets.token_hex(8).upper()}'
    
    # Create payment record
    from app.models import Payment
    payment = Payment(
        class_group_id=current_user.class_group_id,
        user_id=current_user.id,
        amount=total_amount_ghs,  # Amount in GHS
        plan_type=f"{plan_name}_{duration_semesters}sem",  # e.g., "gold_2sem"
        reference=reference,
        status='pending'
    )
    db.session.add(payment)
    db.session.commit()
    
    # Initialize Paystack payment
    import requests
    
    paystack_url = 'https://api.paystack.co/transaction/initialize'
    headers = {
        'Authorization': f'Bearer {current_app.config["PAYSTACK_SECRET_KEY"]}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'email': current_user.email,
        'amount': plan['amount'],  # Amount in pesewas
        'reference': reference,
        'callback_url': url_for('main.payment_callback', _external=True),
        'metadata': {
            'class_group_id': current_user.class_group_id,
            'user_id': current_user.id,
            'plan_name': plan_name,
            'duration_semesters': duration_semesters,
            'plan_display_name': plan['name']
        }
    }
    
    try:
        response = requests.post(paystack_url, json=data, headers=headers)
        response_data = response.json()
        
        if response_data.get('status'):
            # Redirect to Paystack checkout
            authorization_url = response_data['data']['authorization_url']
            return redirect(authorization_url)
        else:
            flash(f'Payment initialization failed: {response_data.get("message")}', 'error')
            payment.status = 'failed'
            db.session.commit()
            return redirect(url_for('main.subscription'))
    
    except Exception as e:
        flash(f'Payment error: {str(e)}', 'error')
        payment.status = 'failed'
        db.session.commit()
        return redirect(url_for('main.subscription'))

@main.route('/payment/callback')
@login_required
def payment_callback():
    """Handle Paystack payment callback"""
    reference = request.args.get('reference')
    
    if not reference:
        flash('Invalid payment reference.', 'error')
        return redirect(url_for('main.subscription'))
    
    # Verify payment with Paystack
    import requests
    
    verify_url = f'https://api.paystack.co/transaction/verify/{reference}'
    headers = {
        'Authorization': f'Bearer {current_app.config["PAYSTACK_SECRET_KEY"]}'
    }
    
    try:
        response = requests.get(verify_url, headers=headers)
        response_data = response.json()
        
        if response_data.get('status') and response_data['data']['status'] == 'success':
            # Payment successful
            from app.models import Payment, ClassGroup
            payment = Payment.query.filter_by(reference=reference).first()
            
            if not payment:
                flash('Payment record not found.', 'error')
                return redirect(url_for('main.subscription'))
            
            # Update payment status
            payment.status = 'success'
            payment.paystack_response = str(response_data)
            
            # Upgrade subscription using new model
            class_group = ClassGroup.query.get(payment.class_group_id)
            
            if class_group:
                # Parse plan details from plan_type (e.g., "gold_2sem")
                plan_parts = payment.plan_type.split('_')
                plan_name = plan_parts[0]  # 'gold' or 'platinum'
                duration_semesters = int(plan_parts[1].replace('sem', ''))  # 2
                
                # Upgrade subscription using the new model
                class_group.upgrade_subscription(plan_name, duration_semesters)
                
                # Send confirmation email
                try:
                    msg = Message(
                        'Payment Successful - UniPortal Subscription Activated!',
                        sender=('UniPortal', 'ko2527600@gmail.com'),
                        recipients=[current_user.email]
                    )
                    msg.body = f'''Hello {current_user.username},

Your payment was successful! 🎉

Subscription Details:
- Plan: {plan_name.title()} Plan
- Duration: {duration_semesters} Semester(s)
- Amount: GH₵{payment.amount:.2f}
- Reference: {reference}
- Expires: {class_group.subscription_expiry.strftime('%B %d, %Y') if class_group.subscription_expiry else 'N/A'}

Your class now has full access to all premium features!

Thank you for choosing UniPortal.

Best regards,
UniPortal Team'''
                    mail.send(msg)
                except Exception as e:
                    print(f"Email sending failed: {str(e)}")
                
                expiry_date = class_group.subscription_expiry.strftime("%B %d, %Y") if class_group.subscription_expiry else "N/A"
                flash(f'✅ Payment successful! {plan_name.title()} subscription activated until {expiry_date}', 'success')
            else:
                flash('Class group not found.', 'error')
            
            return redirect(url_for('main.subscription'))
        else:
            # Payment failed
            from app.models import Payment
            payment = Payment.query.filter_by(reference=reference).first()
            if payment:
                payment.status = 'failed'
                payment.paystack_response = str(response_data)
                db.session.commit()
            
            flash('Payment verification failed. Please try again.', 'error')
            return redirect(url_for('main.subscription'))
    
    except Exception as e:
        flash(f'Payment verification error: {str(e)}', 'error')
        return redirect(url_for('main.subscription'))

@main.route('/payment/webhook', methods=['POST'])
def payment_webhook():
    """Handle Paystack webhook notifications"""
    # Verify webhook signature
    paystack_signature = request.headers.get('x-paystack-signature')
    
    if not paystack_signature:
        return jsonify({'status': 'error', 'message': 'No signature'}), 400
    
    # Verify signature
    import hmac
    import hashlib
    
    body = request.get_data()
    computed_signature = hmac.new(
        current_app.config['PAYSTACK_SECRET_KEY'].encode('utf-8'),
        body,
        hashlib.sha512
    ).hexdigest()
    
    if computed_signature != paystack_signature:
        return jsonify({'status': 'error', 'message': 'Invalid signature'}), 400
    
    # Process webhook
    data = request.get_json()
    event = data.get('event')
    
    if event == 'charge.success':
        reference = data['data']['reference']
        
        from app.models import Payment, ClassGroup
        payment = Payment.query.filter_by(reference=reference).first()
        
        if payment and payment.status == 'pending':
            payment.status = 'success'
            payment.paystack_response = str(data)
            
            # Extend premium
            class_group = ClassGroup.query.get(payment.class_group_id)
            if class_group:
                from datetime import datetime, timedelta
                
                pricing = {
                    'semester': 150,
                    'yearly': 365,
                    '4year': 1460
                }
                
                duration_days = pricing.get(payment.plan_type, 150)
                
                if class_group.premium_expiry and class_group.premium_expiry > datetime.utcnow():
                    new_expiry = class_group.premium_expiry + timedelta(days=duration_days)
                else:
                    new_expiry = datetime.utcnow() + timedelta(days=duration_days)
                
                class_group.premium_expiry = new_expiry
            
            db.session.commit()
    
    return jsonify({'status': 'success'}), 200

@main.route('/attendance_dashboard')
@login_required
def attendance_dashboard():
    """Professional attendance dashboard for lecturers and reps"""
    if current_user.role not in ['Admin', 'Lecturer', 'Rep']:
        flash('Access denied. Lecturer or Rep privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Get courses based on role
    if current_user.role == 'Rep':
        # Get all courses in the rep's class
        if current_user.class_group:
            lecturer_courses = current_user.class_group.courses
        else:
            lecturer_courses = []
    else:
        # Get courses taught by this lecturer
        lecturer_courses = Course.query.filter_by(lecturer_id=current_user.id).all()
    
    # Get attendance data for each course
    attendance_data = []
    for course in lecturer_courses:
        sessions = AttendanceSession.query.filter_by(course_id=course.id).order_by(AttendanceSession.timestamp.desc()).all()
        
        for session in sessions:
            records = AttendanceRecord.query.filter_by(session_id=session.id).all()
            attendance_data.append({
                'course': course,
                'session': session,
                'records': records,
                'count': len(records)
            })
    
    return render_template('attendance_dashboard.html', attendance_data=attendance_data, lecturer_courses=lecturer_courses)

@main.route('/library')
@login_required
@premium_required
def library():
    """Universal Online Library with Google Books API"""
    # Get search query, default to science books
    search_query = request.args.get('q', '').strip()
    if not search_query:
        search_query = 'subject:science'
    
    # Common search suggestions for autocomplete
    suggestions = [
        'Computer Science',
        'Calculus',
        'Biology',
        'History of Ghana',
        'Physics',
        'Economics',
        'Accounting',
        'Chemistry',
        'Mathematics',
        'Engineering',
        'Psychology',
        'Business Management',
        'Data Science',
        'Artificial Intelligence',
        'Statistics',
        'Literature',
        'Philosophy',
        'Political Science',
        'Sociology',
        'Medicine'
    ]
    
    # Fetch local resources from database (filtered by user's class)
    local_resources = []
    if current_user.class_group_id:
        # Fetch resources that belong to the user's class
        local_resources = Resource.query.filter_by(
            is_approved=True,
            class_group_id=current_user.class_group_id
        ).order_by(Resource.created_at.desc()).all()
    else:
        # If user has no class, show no local resources (only Google Books)
        local_resources = []
    
    # Search Google Books API
    api_books = []
    try:
        response = requests.get(f'https://www.googleapis.com/books/v1/volumes?q={search_query}&maxResults=12')
        if response.status_code == 200:
            data = response.json()
            items = data.get('items', [])
            
            # Parse Google Books data
            for item in items:
                volume_info = item.get('volumeInfo', {})
                book_data = {
                    'title': volume_info.get('title', 'Unknown Title'),
                    'authors': ', '.join(volume_info.get('authors', [])) if volume_info.get('authors') else 'Unknown Author',
                    'thumbnail': volume_info.get('imageLinks', {}).get('thumbnail', ''),
                    'link': volume_info.get('previewLink', ''),
                    'rating': volume_info.get('averageRating'),
                    'publisher': volume_info.get('publisher', ''),
                    'publishedDate': volume_info.get('publishedDate', ''),
                    'description': volume_info.get('description', '')[:200] + '...' if volume_info.get('description') else ''
                }
                api_books.append(book_data)
    except Exception as e:
        print(f"Error fetching from Google Books API: {str(e)}")
        flash('Could not fetch external books at this time.', 'warning')
    
    return render_template('library.html', 
                         local_resources=local_resources, 
                         api_books=api_books,
                         search_query=search_query if search_query != 'subject:science' else '',
                         suggestions=suggestions)

@main.route('/grading_room/<int:assignment_id>')
@login_required
@premium_required
def grading_room(assignment_id):
    """Speed grading interface for lecturers"""
    if current_user.role not in ['Admin', 'Lecturer']:
        flash('Access denied. Lecturer privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Get the current assignment
    assignment = Assignment.query.get_or_404(assignment_id)
    
    # Get the next ungraded assignment in the queue
    next_assignment = Assignment.query.filter(
        Assignment.id > assignment_id,
        Assignment.grade == None
    ).order_by(Assignment.id.asc()).first()
    
    # Get total ungraded count
    ungraded_count = Assignment.query.filter(Assignment.grade == None).count()
    
    return render_template('grading_room.html', 
                         assignment=assignment, 
                         next_assignment=next_assignment,
                         ungraded_count=ungraded_count)

@main.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Settings page with role-specific features"""
    if request.method == 'POST':
        action = request.form.get('action')
        
        # Update Profile (Password & Email Preferences)
        if action == 'update_profile':
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            receive_emails = request.form.get('receive_emails') == 'on'
            
            # Update email preference
            current_user.receive_emails = receive_emails
            
            # Update password if provided
            if current_password and new_password:
                if not current_user.check_password(current_password):
                    flash('Current password is incorrect.', 'error')
                    return redirect(url_for('main.settings'))
                
                if new_password != confirm_password:
                    flash('New passwords do not match.', 'error')
                    return redirect(url_for('main.settings'))
                
                if len(new_password) < 6:
                    flash('Password must be at least 6 characters.', 'error')
                    return redirect(url_for('main.settings'))
                
                current_user.set_password(new_password)
                flash('✅ Password updated successfully!', 'success')
            
            db.session.commit()
            flash('✅ Settings updated successfully!', 'success')
            return redirect(url_for('main.settings'))
        
        # Leave Class (Students Only)
        elif action == 'leave_class':
            if current_user.role not in ['Student', 'Rep']:
                flash('Access denied.', 'error')
                return redirect(url_for('main.settings'))
            
            if not current_user.class_group_id:
                flash('You are not in any class.', 'info')
                return redirect(url_for('main.settings'))
            
            current_user.class_group_id = None
            db.session.commit()
            flash('✅ You have left the class.', 'success')
            return redirect(url_for('main.settings'))
        
        # Update Class (Reps Only)
        elif action == 'update_class':
            if current_user.role != 'Rep':
                flash('Access denied. Rep privileges required.', 'error')
                return redirect(url_for('main.settings'))
            
            class_id = request.form.get('class_id')
            class_name = request.form.get('class_name')
            regenerate_codes = request.form.get('regenerate_codes') == 'on'
            
            from app.models import ClassGroup
            class_group = ClassGroup.query.get(class_id)
            
            if not class_group or class_group.created_by != current_user.id:
                flash('Invalid class or access denied.', 'error')
                return redirect(url_for('main.settings'))
            
            # Update class name
            if class_name and class_name.strip():
                class_group.name = class_name.strip()
            
            # Regenerate codes if requested
            if regenerate_codes:
                import string
                import random
                
                # Generate new join code
                while True:
                    join_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                    if not ClassGroup.query.filter_by(join_code=join_code).first():
                        break
                
                # Generate new lecturer code
                while True:
                    lecturer_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                    if not ClassGroup.query.filter_by(lecturer_code=lecturer_code).first():
                        break
                
                class_group.join_code = join_code
                class_group.lecturer_code = lecturer_code
                flash(f'✅ New codes generated! Student: {join_code} | Lecturer: {lecturer_code}', 'success')
            
            db.session.commit()
            flash('✅ Class settings updated!', 'success')
            return redirect(url_for('main.settings'))
        
        # Update System (Admins Only)
        elif action == 'update_system':
            if current_user.role != 'Admin':
                flash('Access denied. Admin privileges required.', 'error')
                return redirect(url_for('main.settings'))
            
            drive_folder_id = request.form.get('drive_folder_id', '').strip()
            
            # In a real app, you'd store this in a SystemConfig model
            # For now, we'll just flash a success message
            flash(f'✅ System configuration updated! Drive Folder ID: {drive_folder_id}', 'success')
            return redirect(url_for('main.settings'))
    
    # GET request - fetch user's classes if Rep
    my_classes = []
    if current_user.role == 'Rep':
        from app.models import ClassGroup
        my_classes = ClassGroup.query.filter_by(created_by=current_user.id).all()
    
    return render_template('settings.html', my_classes=my_classes)

@main.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile page for viewing and editing user details"""
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        
        # Validation
        if not username or not email:
            flash('Username and email are required.', 'error')
            return redirect(url_for('main.profile'))
        
        # Check if username is taken by another user
        if username != current_user.username:
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash('Username already taken. Please choose another.', 'error')
                return redirect(url_for('main.profile'))
        
        # Check if email is taken by another user
        if email != current_user.email:
            existing_email = User.query.filter_by(email=email).first()
            if existing_email:
                flash('Email already in use. Please use another.', 'error')
                return redirect(url_for('main.profile'))
        
        # Update user details
        current_user.full_name = full_name if full_name else None
        current_user.username = username
        current_user.email = email
        
        db.session.commit()
        
        flash('✅ Profile updated successfully!', 'success')
        return redirect(url_for('main.profile'))
    
    return render_template('profile.html')

@main.route('/terms')
def terms():
    """Display Terms of Service page"""
    return render_template('terms.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            # Check if user is verified
            if not user.is_verified:
                session['unverified_user_id'] = user.id
                flash('Please verify your account first.', 'error')
                return redirect(url_for('main.verify'))
            
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@main.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')  # Student/Lecturer/Rep
        join_code = request.form.get('join_code')  # For Students
        lecturer_code = request.form.get('lecturer_code')  # For Lecturers
        rep_code = request.form.get('rep_code')  # For Reps (optional)
        
        # Check if user exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists! Try another.', 'error')
            return redirect(url_for('main.register'))
        
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            flash('Email already exists! Try another.', 'error')
            return redirect(url_for('main.register'))
        
        # Validate join code logic
        class_group_id = None
        university_id = None
        actual_role = role
        
        from app.models import ClassGroup
        
        # STUDENT REGISTRATION
        if role == 'Student':
            if not join_code or join_code.strip() == '':
                flash('❌ Students must enter a Student Class Code. Get it from your Class Rep.', 'error')
                return redirect(url_for('main.register'))
            
            # Validate student join_code
            group = ClassGroup.query.filter_by(join_code=join_code.strip().upper()).first()
            if not group:
                flash('❌ Invalid Student Class Code. Please check and try again.', 'error')
                return redirect(url_for('main.register'))
            
            class_group_id = group.id
            university_id = group.university_id
            actual_role = 'Student'
        
        # LECTURER REGISTRATION
        elif role == 'Lecturer':
            if not lecturer_code or lecturer_code.strip() == '':
                flash('❌ Lecturers must enter a Lecturer Code. Get it from your Class Rep.', 'error')
                return redirect(url_for('main.register'))
            
            # Try to validate as Class Lecturer Code first
            group = ClassGroup.query.filter_by(lecturer_code=lecturer_code.strip().upper()).first()
            
            # If not found, try as Course Lecturer Code
            if not group:
                course = Course.query.filter_by(lecturer_code=lecturer_code.strip().upper()).first()
                if course:
                    # Found a course code - join the class and assign to this course
                    group = ClassGroup.query.get(course.class_group_id)
                    if group:
                        class_group_id = group.id
                        university_id = group.university_id
                        actual_role = 'Lecturer'
                        
                        # Note: We'll assign the lecturer to this course after user creation
                        # Store course_id temporarily in session
                        session['pending_course_assignment'] = course.id
                    else:
                        flash('❌ Invalid Lecturer Code. Course class not found.', 'error')
                        return redirect(url_for('main.register'))
                else:
                    flash('❌ Invalid Lecturer Code. Please check and try again.', 'error')
                    return redirect(url_for('main.register'))
            else:
                # Found class lecturer code - join entire class
                class_group_id = group.id
                university_id = group.university_id
                actual_role = 'Lecturer'
        
        # REP REGISTRATION
        elif role == 'Rep':
            # If Rep provides a code, they join existing class as Student
            if rep_code and rep_code.strip() != '':
                group = ClassGroup.query.filter_by(join_code=rep_code.strip().upper()).first()
                if not group:
                    flash('❌ Invalid Class Code. Please check and try again.', 'error')
                    return redirect(url_for('main.register'))
                
                class_group_id = group.id
                university_id = group.university_id
                actual_role = 'Student'  # Rep joining existing class becomes Student
            else:
                # Founder Rep - no class yet, they will create one
                actual_role = 'Rep'
                class_group_id = None
                university_id = None
        
        # Generate 6-digit verification code
        verification_code = str(random.randint(100000, 999999))
        
        # Create new user
        new_user = User(
            username=username,
            email=email,
            role=actual_role,
            verification_code=verification_code,
            class_group_id=class_group_id,
            university_id=university_id
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        # If lecturer used a course code, assign them to that course
        if actual_role == 'Lecturer' and 'pending_course_assignment' in session:
            course_id = session.pop('pending_course_assignment')
            course = Course.query.get(course_id)
            if course:
                course.lecturer_id = new_user.id
                db.session.commit()
                flash(f'✅ You have been assigned to teach {course.name}', 'success')
        
        # Send verification email
        try:
            msg = Message('UniPortal Verification Code',
                        sender=('UniPortal', 'ko2527600@gmail.com'),
                        recipients=[email])
            msg.body = f'Welcome to UniPortal!\n\nYour verification code is: {verification_code}\n\nPlease enter this code to verify your account.\n\nThank you,\nUniPortal Team'
            mail.send(msg)
            flash(f'✅ A verification code has been sent to {email}', 'success')
        except Exception as e:
            # If email fails, log the error but don't show code
            print(f"Email sending failed: {str(e)}")
            flash(f'⚠️ Email service temporarily unavailable. Please contact support.', 'error')
        
        # Store user ID in session for verification
        session['unverified_user_id'] = new_user.id
        
        return redirect(url_for('main.verify'))
    
    return render_template('register.html')

@main.route('/verify', methods=['GET', 'POST'])
def verify():
    # Check if there's a user to verify
    user_id = session.get('unverified_user_id')
    if not user_id:
        flash('No pending verification. Please register or login.', 'error')
        return redirect(url_for('main.register'))
    
    user = User.query.get(user_id)
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('main.register'))
    
    # If already verified, redirect to login
    if user.is_verified:
        session.pop('unverified_user_id', None)
        flash('Account already verified. Please login.', 'success')
        return redirect(url_for('main.login'))
    
    if request.method == 'POST':
        code = request.form.get('code')
        
        if code == user.verification_code:
            # Verify the user
            user.is_verified = True
            user.verification_code = None  # Clear the code
            db.session.commit()
            
            # Clear session
            session.pop('unverified_user_id', None)
            
            # Log them in
            login_user(user)
            flash('Account verified successfully! Welcome to UniPortal.', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid verification code. Please try again.', 'error')
    
    return render_template('verify.html', email=user.email)

@main.route('/resend_verification', methods=['POST'])
def resend_verification():
    """Resend verification code to user's email"""
    user_id = session.get('unverified_user_id')
    if not user_id:
        flash('No pending verification. Please register first.', 'error')
        return redirect(url_for('main.register'))
    
    user = User.query.get(user_id)
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('main.register'))
    
    if user.is_verified:
        flash('Account already verified. Please login.', 'success')
        return redirect(url_for('main.login'))
    
    # Generate new verification code
    verification_code = str(random.randint(100000, 999999))
    user.verification_code = verification_code
    db.session.commit()
    
    # Send verification email
    try:
        msg = Message('UniPortal Verification Code',
                    sender=('UniPortal', 'ko2527600@gmail.com'),
                    recipients=[user.email])
        msg.body = f'Welcome to UniPortal!\n\nYour NEW verification code is: {verification_code}\n\nPlease enter this code to verify your account.\n\nThank you,\nUniPortal Team'
        mail.send(msg)
        flash(f'✅ New verification code sent to {user.email}', 'success')
    except Exception as e:
        print(f"Email sending failed: {str(e)}")
        flash(f'⚠️ Could not send email. Please try again later.', 'error')
    
    return redirect(url_for('main.verify'))

@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.login'))

@main.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'Admin':
        return redirect(url_for('main.admin_dashboard'))
    elif current_user.role == 'Lecturer':
        # Check if lecturer has assigned course
        course = Course.query.filter_by(lecturer_id=current_user.id).first()
        if course:
            return redirect(url_for('main.lecturer_dashboard'))
        else:
            # Lecturer without assigned course goes to admin dashboard
            return redirect(url_for('main.admin_dashboard'))
    elif current_user.role == 'Rep':
        return redirect(url_for('main.rep_dashboard'))
    else:
        return redirect(url_for('main.student_dashboard'))

@main.route('/student/dashboard')
@login_required
def student_dashboard():
    if current_user.role not in ['Student', 'Rep']:
        flash('Access denied', 'error')
        return redirect(url_for('main.dashboard'))
    
    assignments = Assignment.query.filter_by(user_id=current_user.id).order_by(Assignment.created_at.desc()).all()
    
    # Get the latest broadcast
    from app.models import Broadcast
    broadcast = Broadcast.query.order_by(Broadcast.timestamp.desc()).first()
    
    # Get available courses for the student's class (with their resources)
    courses = []
    if current_user.class_group_id:
        courses = Course.query.filter_by(class_group_id=current_user.class_group_id).all()
    
    # Get slides (Resources with category 'Lecture Slides') for student's class
    # Keep this for backward compatibility with other parts of the dashboard
    slides = []
    if current_user.class_group_id:
        slides = Resource.query.filter_by(
            class_group_id=current_user.class_group_id,
            category='Lecture Slides',
            is_approved=True
        ).order_by(Resource.created_at.desc()).all()
    
    # Calculate current average score for GPA Forecaster
    current_average = 0.0
    graded_assignments = [a for a in assignments if a.grade and a.grade.replace('.', '').replace('%', '').isdigit()]
    if graded_assignments:
        total_score = sum(float(a.grade.replace('%', '')) for a in graded_assignments)
        current_average = round(total_score / len(graded_assignments), 2)
    
    # Get timetable events for the student's class
    timetable_events = []
    if current_user.class_group_id:
        # Define day order for sorting
        day_order = {'Monday': 1, 'Tuesday': 2, 'Wednesday': 3, 'Thursday': 4, 'Friday': 5, 'Saturday': 6, 'Sunday': 7}
        events = TimetableEvent.query.filter_by(class_group_id=current_user.class_group_id).all()
        # Sort by day and then by start_time
        timetable_events = sorted(events, key=lambda e: (day_order.get(e.day, 8), e.start_time))
    
    # Calculate subscription status for banner (same logic as rep dashboard)
    is_premium = False
    days_remaining = 0
    
    if current_user.class_group:
        # Check subscription_expiry first (new field)
        if current_user.class_group.subscription_expiry:
            delta = current_user.class_group.subscription_expiry - datetime.utcnow()
            days_remaining = max(0, delta.days)
            is_premium = days_remaining > 0
        
        # Check old premium_expiry for backward compatibility
        elif current_user.class_group.premium_expiry:
            delta = current_user.class_group.premium_expiry - datetime.utcnow()
            days_remaining = max(0, delta.days)
            is_premium = days_remaining > 0
        
        # If no expiry dates are set, treat as free plan (no banner)
        else:
            # Check if subscription_plan is set to something other than 'free'
            if hasattr(current_user.class_group, 'subscription_plan') and current_user.class_group.subscription_plan != 'free':
                is_premium = True  # Active subscription without expiry
            else:
                is_premium = True  # Don't show expired banner for free users
    
    return render_template('student_dashboard.html', 
                         assignments=assignments, 
                         broadcast=broadcast, 
                         slides=slides, 
                         courses=courses,
                         current_average=current_average,
                         timetable_events=timetable_events,
                         is_premium=is_premium,
                         days_remaining=days_remaining)

@main.route('/lecturer/dashboard')
@login_required
def lecturer_dashboard():
    """Course-specific lecturer dashboard - only shows assigned course data"""
    if current_user.role != 'Lecturer':
        flash('Access denied. Lecturer privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Get lecturer's assigned courses
    lecturer_courses = Course.query.filter_by(lecturer_id=current_user.id).all()
    
    if not lecturer_courses:
        flash('No courses assigned. Contact your Class Rep.', 'warning')
        return redirect(url_for('main.dashboard'))
    
    # For now, handle single course assignment (most common case)
    course = lecturer_courses[0]
    class_group = course.class_group
    
    # Get assignments for this course only
    assignments = Assignment.query.join(User).filter(
        User.class_group_id == class_group.id,
        Assignment.course_id == course.id
    ).order_by(Assignment.created_at.desc()).all()
    
    # Get resources for this course only
    resources = Resource.query.filter_by(
        class_group_id=class_group.id,
        course_id=course.id
    ).order_by(Resource.created_at.desc()).all()
    
    # Get students in this class
    students = User.query.filter_by(
        class_group_id=class_group.id,
        role='Student'
    ).all()
    
    # Calculate course-specific stats
    total_assignments = len(assignments)
    graded_assignments = len([a for a in assignments if a.grade])
    pending_assignments = total_assignments - graded_assignments
    
    # Get attendance sessions for this course
    attendance_sessions = AttendanceSession.query.filter_by(course_id=course.id).all()
    
    # Calculate subscription status
    is_premium = False
    days_remaining = 0
    
    if class_group:
        if class_group.subscription_expiry:
            delta = class_group.subscription_expiry - datetime.utcnow()
            days_remaining = max(0, delta.days)
            is_premium = days_remaining > 0
        elif class_group.premium_expiry:
            delta = class_group.premium_expiry - datetime.utcnow()
            days_remaining = max(0, delta.days)
            is_premium = days_remaining > 0
        else:
            if hasattr(class_group, 'subscription_plan') and class_group.subscription_plan != 'free':
                is_premium = True
            else:
                is_premium = True
    
    # Calculate analytics data
    analytics = {
        'avg_grade': 0,
        'submission_rate': 0,
        'total_students': len(students)
    }
    
    # Calculate average grade
    if graded_assignments > 0:
        grade_values = []
        grade_mapping = {
            'A': 90, 'B+': 85, 'B': 80, 'C+': 75, 'C': 70, 
            'D+': 65, 'D': 60, 'F': 50
        }
        
        for assignment in assignments:
            if assignment.grade and assignment.grade in grade_mapping:
                grade_values.append(grade_mapping[assignment.grade])
        
        if grade_values:
            analytics['avg_grade'] = round(sum(grade_values) / len(grade_values), 1)
    
    # Calculate submission rate
    if len(students) > 0:
        # Count unique students who have submitted assignments
        submitted_students = set()
        for assignment in assignments:
            submitted_students.add(assignment.user_id)
        
        analytics['submission_rate'] = round((len(submitted_students) / len(students)) * 100, 1)
    
    return render_template('lecturer_dashboard.html',
                         course=course,
                         class_group=class_group,
                         assignments=assignments,
                         resources=resources,
                         students=students,
                         total_assignments=total_assignments,
                         graded_assignments=graded_assignments,
                         pending_assignments=pending_assignments,
                         attendance_sessions=attendance_sessions,
                         lecturer_courses=lecturer_courses,
                         is_premium=is_premium,
                         days_remaining=days_remaining,
                         analytics=analytics)

@main.route('/rep/dashboard')
@login_required
def rep_dashboard():
    if current_user.role != 'Rep':
        flash('Access denied. Rep privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Get rep's own assignments
    my_assignments = Assignment.query.filter_by(user_id=current_user.id).order_by(Assignment.created_at.desc()).all()
    
    # Get ALL class assignments (for compilation)
    all_assignments = Assignment.query.order_by(Assignment.created_at.desc()).all()
    
    # Get class wallet balance (get the first wallet or create default)
    from app.models import ClassWallet
    wallet = ClassWallet.query.first()
    if not wallet:
        wallet = ClassWallet(current_balance=0.0, target=1000.0)
        db.session.add(wallet)
        db.session.commit()
    
    # Get latest broadcast
    from app.models import Broadcast
    broadcast = Broadcast.query.order_by(Broadcast.timestamp.desc()).first()
    
    # Get all broadcasts for this rep's class
    my_broadcasts = []
    if current_user.class_group_id:
        my_broadcasts = Broadcast.query.filter_by(class_group_id=current_user.class_group_id).order_by(Broadcast.timestamp.desc()).all()
    
    # Get courses for the rep's class (with their resources)
    courses = []
    if current_user.class_group_id:
        courses = Course.query.filter_by(class_group_id=current_user.class_group_id).all()
    
    # Get slides (Resources with category 'Lecture Slides') for rep's class
    # Keep this for backward compatibility with other parts of the dashboard
    slides = []
    if current_user.class_group_id:
        slides = Resource.query.filter_by(
            class_group_id=current_user.class_group_id,
            category='Lecture Slides',
            is_approved=True
        ).order_by(Resource.created_at.desc()).all()
    
    # Calculate stats for dashboard
    from app.models import User
    total_students = User.query.filter_by(role='Student').count()
    files_uploaded = len(all_assignments)
    broadcasts_count = Broadcast.query.count()
    
    # Get classes created by this rep
    from app.models import ClassGroup
    my_classes = ClassGroup.query.filter_by(created_by=current_user.id).all()
    
    # Get available courses for the rep's class (for upload dropdown)
    courses = []
    if current_user.class_group_id:
        class_group = ClassGroup.query.get(current_user.class_group_id)
        if class_group:
            courses = class_group.courses
    
    # Get timetable events for the rep's class
    timetable_events = []
    if current_user.class_group_id:
        # Define day order for sorting
        day_order = {'Monday': 1, 'Tuesday': 2, 'Wednesday': 3, 'Thursday': 4, 'Friday': 5, 'Saturday': 6, 'Sunday': 7}
        events = TimetableEvent.query.filter_by(class_group_id=current_user.class_group_id).all()
        # Sort by day and then by start_time
        timetable_events = sorted(events, key=lambda e: (day_order.get(e.day, 8), e.start_time))
    
    # Calculate subscription status for banner
    is_premium = False
    days_remaining = 0
    
    if current_user.class_group:
        # Check new subscription model first
        if current_user.class_group.subscription_expiry:
            delta = current_user.class_group.subscription_expiry - datetime.utcnow()
            days_remaining = max(0, delta.days)
            is_premium = days_remaining > 0
        # Check old premium_expiry for backward compatibility
        elif current_user.class_group.premium_expiry:
            delta = current_user.class_group.premium_expiry - datetime.utcnow()
            days_remaining = max(0, delta.days)
            is_premium = days_remaining > 0
        # If no expiry dates are set, treat as free plan (no banner)
        else:
            # Check if subscription_plan is set to something other than 'free'
            if hasattr(current_user.class_group, 'subscription_plan') and current_user.class_group.subscription_plan != 'free':
                is_premium = True  # Active subscription without expiry
            else:
                is_premium = True  # Don't show expired banner for free users
    
    return render_template('rep_dashboard.html', 
                         my_assignments=my_assignments, 
                         all_assignments=all_assignments,
                         wallet=wallet,
                         my_broadcasts=my_broadcasts,
                         broadcast=broadcast,
                         slides=slides,
                         total_students=total_students,
                         files_uploaded=files_uploaded,
                         broadcasts_count=broadcasts_count,
                         my_classes=my_classes,
                         courses=courses,
                         timetable_events=timetable_events,
                         is_premium=is_premium,
                         days_remaining=days_remaining)

@main.route('/create_class', methods=['POST'])
@login_required
def create_class():
    from app.models import ClassGroup, University
    
    if current_user.role != 'Rep':
        flash('Access denied. Rep privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # CHECK: Rep can only create ONE class group
    existing_class = ClassGroup.query.filter_by(created_by=current_user.id).first()
    if existing_class:
        flash('❌ You already have a class group. ONE Rep = ONE Class. To help another class, use their join code.', 'error')
        return redirect(url_for('main.rep_dashboard'))
    
    class_name = request.form.get('class_name')
    class_code = request.form.get('class_code')
    
    if not class_name or not class_code:
        flash('Class name and code are required.', 'error')
        return redirect(url_for('main.rep_dashboard'))
    
    # Generate unique join_code (6 characters)
    import string
    while True:
        join_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if not ClassGroup.query.filter_by(join_code=join_code).first():
            break
    
    # Generate unique lecturer_code (8 characters) - DEPRECATED, now per-course
    while True:
        lecturer_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        if not ClassGroup.query.filter_by(lecturer_code=lecturer_code).first():
            break
    
    # Create the class
    # If Rep doesn't have a university yet, create a default one or use existing default
    university_id = current_user.university_id
    if not university_id:
        # Get or create a default university
        default_university = University.query.filter_by(name='Default University').first()
        if not default_university:
            default_university = University(name='Default University', domain='default.edu')
            db.session.add(default_university)
            db.session.commit()
        university_id = default_university.id
        # Update the Rep's university
        current_user.university_id = university_id
        db.session.commit()
    
    new_class = ClassGroup(
        name=class_name.strip(),
        code=class_code.strip(),
        join_code=join_code,
        lecturer_code=lecturer_code,
        created_by=current_user.id,
        university_id=university_id
    )
    db.session.add(new_class)
    db.session.commit()
    
    # FIX: Add Rep to the class they just created (Ghost Rep bug fix)
    current_user.class_group_id = new_class.id
    db.session.commit()
    
    flash(f'✅ Class created! Student Code: {join_code}', 'success')
    return redirect(url_for('main.rep_dashboard'))

@main.route('/create_course', methods=['POST'])
@login_required
def create_course():
    if current_user.role != 'Rep':
        flash('Access denied. Rep privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    course_name = request.form.get('course_name')
    class_group_id = request.form.get('class_group_id')
    
    if not course_name or not class_group_id:
        flash('Course name and class group are required.', 'error')
        return redirect(url_for('main.rep_dashboard'))
    
    # Verify the class belongs to this rep
    from app.models import ClassGroup
    class_group = ClassGroup.query.get(class_group_id)
    if not class_group or class_group.created_by != current_user.id:
        flash('Invalid class group.', 'error')
        return redirect(url_for('main.rep_dashboard'))
    
    # Generate unique lecturer_code for this course (8 characters)
    import string
    while True:
        lecturer_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        if not Course.query.filter_by(lecturer_code=lecturer_code).first():
            break
    
    # Create the course
    new_course = Course(
        name=course_name.strip(),
        lecturer_code=lecturer_code,
        class_group_id=class_group_id
    )
    db.session.add(new_course)
    db.session.commit()
    
    flash(f'✅ Course "{course_name}" created! Lecturer Code: {lecturer_code}', 'success')
    return redirect(url_for('main.rep_dashboard'))

@main.route('/claim_class', methods=['GET', 'POST'])
def claim_class():
    if request.method == 'POST':
        lecturer_code = request.form.get('lecturer_code')
        email = request.form.get('email')
        password = request.form.get('password')
        username = request.form.get('username')
        
        if not lecturer_code:
            flash('Please enter the lecturer code.', 'error')
            return redirect(url_for('main.claim_class'))
        
        # Find the COURSE by lecturer_code (NEW: per-course claiming)
        course = Course.query.filter_by(lecturer_code=lecturer_code.strip().upper()).first()
        
        if not course:
            flash('❌ Invalid Lecturer Code. Please check with your Class Rep.', 'error')
            return redirect(url_for('main.claim_class'))
        
        # Check if course already has a lecturer
        if course.lecturer_id:
            flash('❌ This course already has a lecturer assigned.', 'error')
            return redirect(url_for('main.claim_class'))
        
        # Check if user is logged in
        if current_user.is_authenticated:
            # Assign current user as lecturer for this course
            if current_user.role != 'Lecturer':
                current_user.role = 'Lecturer'
            course.lecturer_id = current_user.id
            current_user.university_id = course.class_group.university_id
            db.session.commit()
            flash(f'✅ You are now the lecturer for {course.name}!', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            # Create new lecturer account
            if not all([email, password, username]):
                flash('Please fill in all fields to create your lecturer account.', 'error')
                return redirect(url_for('main.claim_class'))
            
            # Check if user exists
            if User.query.filter_by(username=username).first():
                flash('Username already exists! Please login or use another username.', 'error')
                return redirect(url_for('main.claim_class'))
            
            if User.query.filter_by(email=email).first():
                flash('Email already exists! Please login or use another email.', 'error')
                return redirect(url_for('main.claim_class'))
            
            # Generate verification code
            verification_code = str(random.randint(100000, 999999))
            
            # Create lecturer account
            new_lecturer = User(
                username=username,
                email=email,
                role='Lecturer',
                verification_code=verification_code,
                university_id=course.class_group.university_id
            )
            new_lecturer.set_password(password)
            db.session.add(new_lecturer)
            db.session.commit()
            
            # Assign as lecturer for this course
            course.lecturer_id = new_lecturer.id
            db.session.commit()
            
            # Send verification email
            try:
                msg = Message('UniPortal Verification Code',
                            sender=('UniPortal', 'ko2527600@gmail.com'),
                            recipients=[email])
                msg.body = f'Welcome to UniPortal!\n\nYour verification code is: {verification_code}\n\nYou have been assigned as a lecturer for {course.name}.\n\nPlease enter this code to verify your account.\n\nThank you,\nUniPortal Team'
                mail.send(msg)
                flash(f'✅ Lecturer account created for {course.name}! A verification code has been sent to {email}', 'success')
            except Exception as e:
                # If email fails, log the error but don't show code
                print(f"Email sending failed: {str(e)}")
                flash(f'⚠️ Email service temporarily unavailable. Please contact support.', 'error')
            
            # Store in session for verification
            session['unverified_user_id'] = new_lecturer.id
            
            return redirect(url_for('main.verify'))
    
    return render_template('claim_class.html')
@main.route('/edit_broadcast/<int:broadcast_id>', methods=['POST'])
@login_required
def edit_broadcast(broadcast_id):
    """Edit an existing broadcast"""
    if current_user.role not in ['Rep', 'Admin', 'Lecturer']:
        flash('Access denied.', 'error')
        return redirect(url_for('main.dashboard'))
    
    from app.models import Broadcast
    broadcast = Broadcast.query.get_or_404(broadcast_id)
    
    # Security check: Only the creator or admin can edit
    if broadcast.user_id != current_user.id and current_user.role != 'Admin':
        flash('You can only edit your own broadcasts.', 'error')
        return redirect(url_for('main.dashboard'))
    
    new_message = request.form.get('message')
    
    if not new_message or new_message.strip() == '':
        flash('Broadcast message cannot be empty.', 'error')
        return redirect(url_for('main.rep_dashboard'))
    
    broadcast.message = new_message.strip()
    db.session.commit()
    
    flash('Broadcast updated successfully!', 'success')
    return redirect(url_for('main.rep_dashboard'))

@main.route('/delete_broadcast/<int:broadcast_id>', methods=['POST'])
@login_required
def delete_broadcast(broadcast_id):
    """Delete a broadcast"""
    if current_user.role not in ['Rep', 'Admin', 'Lecturer']:
        flash('Access denied.', 'error')
        return redirect(url_for('main.dashboard'))
    
    from app.models import Broadcast
    broadcast = Broadcast.query.get_or_404(broadcast_id)
    
    # Security check: Only the creator or admin can delete
    if broadcast.user_id != current_user.id and current_user.role != 'Admin':
        flash('You can only delete your own broadcasts.', 'error')
        return redirect(url_for('main.dashboard'))
    
    db.session.delete(broadcast)
    db.session.commit()
    
    flash('Broadcast deleted successfully!', 'success')
    return redirect(url_for('main.rep_dashboard'))

@main.route('/post_broadcast', methods=['POST'])
@login_required
@premium_required
def post_broadcast():
    # Only Rep, Admin, or Lecturer can post broadcasts
    if current_user.role not in ['Rep', 'Admin', 'Lecturer']:
        flash('Access denied. Rep or Lecturer privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    message = request.form.get('message')
    
    if not message or message.strip() == '':
        flash('Broadcast message cannot be empty.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Create new broadcast
    from app.models import Broadcast, ClassGroup
    broadcast = Broadcast(
        message=message.strip(), 
        user_id=current_user.id,
        class_group_id=current_user.class_group_id
    )
    db.session.add(broadcast)
    db.session.commit()
    
    # Send emails to students - SYNCHRONOUS (immediate)
    try:
        sender_name = current_user.full_name if current_user.full_name else current_user.username
        
        # Get students to notify
        if current_user.class_group_id:
            class_group = ClassGroup.query.get(current_user.class_group_id)
            students = User.query.filter_by(
                class_group_id=current_user.class_group_id,
                role='Student',
                receive_emails=True
            ).all()
            class_name = class_group.name if class_group else "Your Class"
            
            print(f"[BROADCAST] Class: {class_name} (ID: {current_user.class_group_id})")
            print(f"[BROADCAST] Found {len(students)} students with email enabled")
        else:
            # Send to all students (for admin broadcasts)
            students = User.query.filter_by(
                role='Student',
                receive_emails=True
            ).all()
            class_name = "All Students"
            print(f"[BROADCAST] Sending to ALL students: {len(students)}")
        
        # Send email to each student
        sent_count = 0
        failed_count = 0
        
        for student in students:
            try:
                print(f"[BROADCAST] Sending to {student.username} ({student.email})...")
                
                msg = Message(
                    f'📢 New Announcement from {sender_name}',
                    sender=('UniPortal', 'ko2527600@gmail.com'),
                    recipients=[student.email]
                )
                msg.body = f'''Hello {student.username},

You have a new announcement from {sender_name}:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{broadcast.message}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Class: {class_name}
Posted: {broadcast.timestamp.strftime('%B %d, %Y at %I:%M %p')}

Login to UniPortal to view more details.

---
To stop receiving email notifications, update your preferences in Settings.

UniPortal Team'''
                
                msg.html = f'''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px 10px 0 0;">
                        <h2 style="color: white; margin: 0;">📢 New Announcement</h2>
                    </div>
                    <div style="background: white; padding: 30px; border-radius: 0 0 10px 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                        <p style="color: #333; font-size: 16px;">Hello <strong>{student.username}</strong>,</p>
                        <p style="color: #666; font-size: 14px;">You have a new announcement from <strong>{sender_name}</strong>:</p>
                        
                        <div style="background: #f8f9fa; border-left: 4px solid #667eea; padding: 20px; margin: 20px 0; border-radius: 5px;">
                            <p style="color: #333; font-size: 15px; line-height: 1.6; margin: 0; white-space: pre-wrap;">{broadcast.message}</p>
                        </div>
                        
                        <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #e0e0e0;">
                            <p style="color: #999; font-size: 13px; margin: 5px 0;">
                                <strong>Class:</strong> {class_name}<br>
                                <strong>Posted:</strong> {broadcast.timestamp.strftime('%B %d, %Y at %I:%M %p')}
                            </p>
                        </div>
                        
                        <p style="color: #999; font-size: 12px; text-align: center; margin-top: 30px;">
                            To stop receiving email notifications, update your preferences in Settings.
                        </p>
                    </div>
                </div>
                '''
                
                mail.send(msg)
                sent_count += 1
                print(f"[BROADCAST] ✅ Sent to {student.email}")
                
            except Exception as e:
                failed_count += 1
                print(f"[BROADCAST] ❌ Failed to send to {student.email}: {str(e)}")
                continue
        
        print(f"[BROADCAST] Summary: {sent_count} sent, {failed_count} failed")
        
        if sent_count > 0:
            flash(f'📢 Broadcast posted! Emails sent to {sent_count} student(s).', 'success')
        elif len(students) == 0:
            flash('📢 Broadcast posted! (No students in your class have email enabled)', 'info')
        else:
            flash(f'📢 Broadcast posted! (Failed to send {failed_count} emails - check console)', 'warning')
            
    except Exception as e:
        print(f"[BROADCAST] ❌ CRITICAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        flash('📢 Broadcast posted! (Email system error - check console)', 'warning')
    
    return redirect(url_for('main.dashboard'))

@main.route('/submit_grade/<int:assignment_id>', methods=['POST'])
@login_required
def submit_grade(assignment_id):
    """Submit grade from speed grading interface"""
    if current_user.role not in ['Admin', 'Lecturer']:
        flash('Access denied. Lecturer privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    assignment = Assignment.query.get_or_404(assignment_id)
    
    # Get rubric scores
    grammar_score = request.form.get('grammar_score', 0)
    logic_score = request.form.get('logic_score', 0)
    research_score = request.form.get('research_score', 0)
    
    # Get total grade and feedback
    grade = request.form.get('grade')
    feedback = request.form.get('feedback', '')
    
    if not grade or grade.strip() == '':
        flash('Grade cannot be empty.', 'error')
        return redirect(url_for('main.grading_room', assignment_id=assignment_id))
    
    # Update assignment with grade and feedback
    assignment.grade = grade.strip()
    assignment.feedback = feedback.strip() if feedback else None
    db.session.commit()
    
    flash(f'✅ Grade {grade} assigned to {assignment.user.username}!', 'success')
    
    # Find next ungraded assignment
    next_assignment = Assignment.query.filter(
        Assignment.id > assignment_id,
        Assignment.grade == None
    ).order_by(Assignment.id.asc()).first()
    
    # Redirect to next assignment or back to dashboard
    if next_assignment:
        return redirect(url_for('main.grading_room', assignment_id=next_assignment.id))
    else:
        flash('🎉 All assignments graded!', 'success')
        return redirect(url_for('main.admin_dashboard'))

@main.route('/grade_assignment/<int:assignment_id>', methods=['POST'])
@login_required
def grade_assignment(assignment_id):
    # Only Admin or Lecturer can grade
    if current_user.role not in ['Admin', 'Lecturer']:
        flash('Access denied. Lecturer privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    assignment = Assignment.query.get_or_404(assignment_id)
    
    grade = request.form.get('grade')
    feedback = request.form.get('feedback', '')
    
    if not grade or grade.strip() == '':
        flash('Grade cannot be empty.', 'error')
        return redirect(url_for('main.admin_dashboard'))
    
    # Update assignment
    assignment.grade = grade.strip()
    assignment.feedback = feedback.strip() if feedback else None
    db.session.commit()
    
    flash(f'Grade "{grade}" assigned to {assignment.user.username}\'s assignment successfully!', 'success')
    return redirect(url_for('main.admin_dashboard'))

@main.route('/upload_slide', methods=['POST'])
@login_required
@premium_required
def upload_slide():
    # Only Admin, Lecturer, or Rep can upload slides
    if current_user.role not in ['Admin', 'Lecturer', 'Rep']:
        flash('Access denied. Lecturer or Rep privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    if 'file' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('main.dashboard'))
    
    file = request.files['file']
    title = request.form.get('title', '')
    description = request.form.get('description', '')
    course_id = request.form.get('course_id', '')
    
    # For course lecturers: verify they can upload to this course
    if current_user.role == 'Lecturer' and course_id:
        course = Course.query.get(course_id)
        if course and course.lecturer_id != current_user.id:
            flash('You can only upload materials to courses you teach.', 'error')
            return redirect(url_for('main.lecturer_dashboard'))
    
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('main.dashboard'))
    
    if not title or title.strip() == '':
        flash('Slide title is required', 'error')
        return redirect(url_for('main.dashboard'))
    
    if not course_id:
        flash('Please select a course', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Check file extension
    allowed_extensions = {'pdf', 'ppt', 'pptx'}
    if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
        flash('Invalid file type. Allowed types: PDF, PPT, PPTX', 'error')
        return redirect(url_for('main.dashboard'))
    
    filename = secure_filename(file.filename)
    # Create slides folder
    slides_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'slides')
    os.makedirs(slides_folder, exist_ok=True)
    
    # Add timestamp to filename to avoid conflicts
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename_parts = filename.rsplit('.', 1)
    unique_filename = f"{filename_parts[0]}_{timestamp}.{filename_parts[1]}"
    
    file_path = os.path.join(slides_folder, unique_filename)
    file.save(file_path)
    
    # Create slide record (using Resource model for library)
    resource = Resource(
        title=title.strip(),
        file_path=file_path,
        author=current_user.username,
        description=description.strip() if description else None,
        category='Lecture Slides',
        is_approved=True,
        uploader_id=current_user.id,
        course_id=int(course_id) if course_id else None,
        class_group_id=current_user.class_group_id  # CRUCIAL: Link to class
    )
    db.session.add(resource)
    db.session.commit()
    
    # Create Broadcast Notification
    if current_user.class_group_id:
        from app.models import Broadcast
        broadcast = Broadcast(
            message=f'📚 New Resource Uploaded: {title.strip()}',
            user_id=current_user.id,
            class_group_id=current_user.class_group_id
        )
        db.session.add(broadcast)
        db.session.commit()
        
        # Send Email Notifications to all students in the class
        try:
            class_students = User.query.filter_by(
                class_group_id=current_user.class_group_id,
                role='Student'
            ).all()
            
            for student in class_students:
                if student.email:
                    try:
                        msg = Message(
                            'New Study Material Available!',
                            sender=('UniPortal', 'ko2527600@gmail.com'),
                            recipients=[student.email]
                        )
                        msg.body = f'''Hello {student.username},

A new study resource has been uploaded to your class library!

📚 Resource: {title.strip()}
👤 Uploaded by: {current_user.username}
📅 Date: {datetime.now().strftime('%B %d, %Y')}

Visit the Library to access this resource.

Best regards,
UniPortal Team'''
                        mail.send(msg)
                    except Exception as e:
                        print(f"Failed to send email to {student.email}: {str(e)}")
        except Exception as e:
            print(f"Error sending notifications: {str(e)}")
    
    flash('✅ Slide Uploaded Successfully!', 'success')
    return redirect(url_for('main.dashboard'))

@main.route('/download_slide/<int:slide_id>')
@login_required
@premium_required
def download_slide(slide_id):
    # This now downloads from Resource model (slides are stored as Resources)
    resource = Resource.query.get_or_404(slide_id)
    
    # Extract filename from file_path
    filename = os.path.basename(resource.file_path)
    return send_file(resource.file_path, as_attachment=True, download_name=filename)

@main.route('/download_resource/<int:resource_id>')
@login_required
@premium_required
def download_resource(resource_id):
    """Download a library resource"""
    resource = Resource.query.get_or_404(resource_id)
    
    # Check if it's an external link
    if resource.external_link:
        return redirect(resource.external_link)
    
    # Download local file
    filename = os.path.basename(resource.file_path)
    return send_file(resource.file_path, as_attachment=True, download_name=filename)

@main.route('/delete_slide/<int:slide_id>', methods=['POST'])
@login_required
def delete_slide(slide_id):
    # Only uploader, Admin, or Lecturer can delete
    # This now deletes from Resource model (slides are stored as Resources)
    resource = Resource.query.get_or_404(slide_id)
    
    if current_user.role not in ['Admin', 'Lecturer'] and resource.uploader_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Delete file from filesystem
    if os.path.exists(resource.file_path):
        os.remove(resource.file_path)
    
    # Delete from database
    db.session.delete(resource)
    db.session.commit()
    
    flash(f'Slide "{resource.title}" deleted successfully!', 'success')
    return redirect(url_for('main.dashboard'))

@main.route('/student/upload', methods=['POST'])
@login_required
@premium_required
def upload_assignment():
    if current_user.role not in ['Student', 'Rep']:
        flash('Access denied', 'error')
        return redirect(url_for('main.dashboard'))
    
    if 'file' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('main.dashboard'))
    
    file = request.files['file']
    course_id = request.form.get('course_id')
    
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('main.dashboard'))
    
    if not course_id:
        flash('Please select a course', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Validate that the course belongs to the user's class group
    course = Course.query.get(course_id)
    if not course or (current_user.class_group_id and course.class_group_id != current_user.class_group_id):
        flash('Invalid course selection.', 'error')
        return redirect(url_for('main.dashboard'))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Create user-specific folder
        user_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], str(current_user.id))
        os.makedirs(user_folder, exist_ok=True)
        
        file_path = os.path.join(user_folder, filename)
        file.save(file_path)
        
        # Calculate file hash
        file_hash = calculate_file_hash(file_path)
        
        # Check for plagiarism
        similarity_score, matched_id = check_plagiarism(file_path, file_hash)
        
        # Create assignment record with course_id
        assignment = Assignment(
            filename=filename,
            file_path=file_path,
            file_hash=file_hash,
            similarity_score=similarity_score,
            matched_assignment_id=matched_id,
            user_id=current_user.id,
            course_id=course_id
        )
        db.session.add(assignment)
        db.session.commit()
        
        if similarity_score > 50:
            flash(f'⚠️ Assignment uploaded! Similarity detected: {similarity_score:.1f}%', 'warning')
        else:
            flash('Assignment uploaded successfully!', 'success')
    else:
        flash('Invalid file type. Allowed types: pdf, doc, docx, txt, ppt, pptx', 'error')
    
    # Redirect based on role
    if current_user.role == 'Rep':
        return redirect(url_for('main.rep_dashboard'))
    else:
        return redirect(url_for('main.student_dashboard'))



@main.route('/lecturer/create_assignment', methods=['GET', 'POST'])
@login_required
@premium_required
def lecturer_create_assignment():
    """Allow lecturers to create assignments for their course"""
    if current_user.role != 'Lecturer':
        flash('Access denied. Lecturer privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Get lecturer's assigned course
    course = Course.query.filter_by(lecturer_id=current_user.id).first()
    if not course:
        flash('No course assigned. Contact your Class Rep.', 'error')
        return redirect(url_for('main.lecturer_dashboard'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        due_date = request.form.get('due_date')
        max_score = request.form.get('max_score', 100)
        
        if not title or not description:
            flash('Title and description are required.', 'error')
            return redirect(url_for('main.lecturer_create_assignment'))
        
        try:
            # Create assignment announcement
            from app.models import Broadcast
            broadcast = Broadcast(
                title=f"📝 New Assignment: {title}",
                message=f"**Course:** {course.name}\n\n**Assignment:** {title}\n\n**Description:** {description}\n\n**Due Date:** {due_date if due_date else 'No specific due date'}\n\n**Max Score:** {max_score} points\n\nSubmit your work through the student dashboard.",
                author_id=current_user.id,
                class_group_id=course.class_group_id,
                course_id=course.id
            )
            
            db.session.add(broadcast)
            db.session.commit()
            
            flash(f'✅ Assignment "{title}" created and announced to students!', 'success')
            return redirect(url_for('main.lecturer_dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating assignment: {str(e)}', 'error')
            return redirect(url_for('main.lecturer_create_assignment'))
    
    return render_template('lecturer_create_assignment.html', course=course)

@main.route('/lecturer/upload_slides', methods=['GET', 'POST'])
@login_required
@premium_required
def lecturer_upload_slides():
    """Allow lecturers to upload multiple slides for their course"""
    if current_user.role != 'Lecturer':
        flash('Access denied. Lecturer privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Get lecturer's assigned course
    course = Course.query.filter_by(lecturer_id=current_user.id).first()
    if not course:
        flash('No course assigned. Contact your Class Rep.', 'error')
        return redirect(url_for('main.lecturer_dashboard'))
    
    if request.method == 'POST':
        files = request.files.getlist('slides')
        title = request.form.get('title', 'Lecture Slides')
        description = request.form.get('description', '')
        
        if not files or all(file.filename == '' for file in files):
            flash('Please select at least one file to upload.', 'error')
            return redirect(url_for('main.lecturer_upload_slides'))
        
        uploaded_files = []
        failed_files = []
        
        for file in files:
            if file and file.filename != '':
                try:
                    # Validate file type
                    allowed_extensions = {'pdf', 'ppt', 'pptx', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png'}
                    if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
                        failed_files.append(f"{file.filename} (invalid file type)")
                        continue
                    
                    # Generate secure filename
                    filename = secure_filename(file.filename)
                    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
                    filename = f"{timestamp}_{filename}"
                    
                    # Create slides folder
                    slides_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'slides')
                    os.makedirs(slides_folder, exist_ok=True)
                    
                    # Save file
                    file_path = os.path.join(slides_folder, filename)
                    file.save(file_path)
                    
                    # Create resource record
                    resource = Resource(
                        filename=file.filename,
                        file_path=filename,
                        category='Lecture Slides',
                        description=description,
                        uploader_id=current_user.id,
                        class_group_id=course.class_group_id,
                        course_id=course.id,
                        is_approved=True  # Auto-approve lecturer uploads
                    )
                    
                    db.session.add(resource)
                    uploaded_files.append(file.filename)
                    
                except Exception as e:
                    failed_files.append(f"{file.filename} (error: {str(e)})")
        
        try:
            db.session.commit()
            
            # Create announcement for uploaded slides
            if uploaded_files:
                from app.models import Broadcast
                file_list = '\n'.join([f"• {filename}" for filename in uploaded_files])
                broadcast = Broadcast(
                    title=f"📚 New Slides: {title}",
                    message=f"**Course:** {course.name}\n\n**Slides Uploaded:**\n{file_list}\n\n{description}\n\nAccess them through the Library section.",
                    author_id=current_user.id,
                    class_group_id=course.class_group_id,
                    course_id=course.id
                )
                db.session.add(broadcast)
                db.session.commit()
            
            # Show results
            if uploaded_files and not failed_files:
                flash(f'✅ Successfully uploaded {len(uploaded_files)} slides!', 'success')
            elif uploaded_files and failed_files:
                flash(f'✅ Uploaded {len(uploaded_files)} slides. Failed: {len(failed_files)}', 'warning')
            else:
                flash('❌ No files were uploaded successfully.', 'error')
                
        except Exception as e:
            db.session.rollback()
            flash(f'Error saving slides: {str(e)}', 'error')
        
        return redirect(url_for('main.lecturer_dashboard'))
    
    return render_template('lecturer_upload_slides.html', course=course)

@main.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role not in ['Admin', 'Lecturer']:
        flash('Access denied', 'error')
        return redirect(url_for('main.dashboard'))
    
    assignments = Assignment.query.order_by(Assignment.created_at.desc()).all()
    users = User.query.all()
    
    # Get latest broadcast
    from app.models import Broadcast
    broadcast = Broadcast.query.order_by(Broadcast.timestamp.desc()).first()
    
    # Get courses for the lecturer's class (with their resources)
    courses = []
    course_counts = {}
    if current_user.class_group_id:
        courses = Course.query.filter_by(class_group_id=current_user.class_group_id).all()
        # Count assignments per course
        for course in courses:
            course_counts[course.id] = Assignment.query.filter_by(course_id=course.id).count()
    
    # Count unassigned assignments
    unassigned_count = Assignment.query.filter(Assignment.course_id.is_(None)).count()
    
    # Get slides (Resources with category 'Lecture Slides') - filter by lecturer's class if applicable
    slides = []
    if current_user.class_group_id:
        slides = Resource.query.filter_by(
            class_group_id=current_user.class_group_id,
            category='Lecture Slides'
        ).order_by(Resource.created_at.desc()).all()
    else:
        # Admin without class sees all slides
        slides = Resource.query.filter_by(
            category='Lecture Slides'
        ).order_by(Resource.created_at.desc()).all()
    
    # Calculate summary statistics
    total_files = Assignment.query.count()
    total_students = User.query.filter_by(role='Student').count()
    pending_count = Assignment.query.filter(Assignment.grade.is_(None)).count()
    alert_count = Assignment.query.filter(Assignment.similarity_score > 50).count()
    
    return render_template('admin_dashboard.html', 
                         assignments=assignments, 
                         users=users, 
                         broadcast=broadcast, 
                         slides=slides,
                         courses=courses,
                         course_counts=course_counts,
                         unassigned_count=unassigned_count,
                         total_files=total_files,
                         total_students=total_students,
                         pending_count=pending_count,
                         alert_count=alert_count)

@main.route('/download/<int:assignment_id>')
@login_required
def download_file(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)
    
    # Check permissions: Admin, Lecturer, Rep, or owner can download
    if current_user.role not in ['Admin', 'Lecturer', 'Rep'] and assignment.user_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('main.dashboard'))
    
    return send_file(assignment.file_path, as_attachment=True, download_name=assignment.filename)

@main.route('/preview/<int:assignment_id>')
@login_required
def preview_file(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)
    
    # Check permissions: Admin, Lecturer, Rep, or owner can preview
    if current_user.role not in ['Admin', 'Lecturer', 'Rep'] and assignment.user_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('main.dashboard'))
    
    return send_file(assignment.file_path, download_name=assignment.filename)

@main.route('/api/get_broadcast')
@login_required
def get_broadcast():
    """API endpoint to get the latest broadcast for the user's class group"""
    from app.models import Broadcast
    
    # Get the latest broadcast for the user's class group
    if current_user.class_group_id:
        broadcast = Broadcast.query.filter_by(class_group_id=current_user.class_group_id).order_by(Broadcast.timestamp.desc()).first()
    else:
        # If no class group, get the latest global broadcast
        broadcast = Broadcast.query.order_by(Broadcast.timestamp.desc()).first()
    
    if broadcast:
        return {
            'message': broadcast.message,
            'timestamp': broadcast.timestamp.strftime('%B %d, %Y at %H:%M'),
            'author': broadcast.user.username,
            'id': broadcast.id
        }
    else:
        return {'message': None}

@main.route('/api/get_broadcast_history')
@login_required
def get_broadcast_history():
    """API endpoint to get all broadcasts for the user's class group"""
    from app.models import Broadcast
    
    # Get all broadcasts for the user's class group
    if current_user.class_group_id:
        broadcasts = Broadcast.query.filter_by(class_group_id=current_user.class_group_id).order_by(Broadcast.timestamp.desc()).all()
    else:
        # If no class group, get all global broadcasts
        broadcasts = Broadcast.query.order_by(Broadcast.timestamp.desc()).all()
    
    return {
        'broadcasts': [
            {
                'message': b.message,
                'timestamp': b.timestamp.strftime('%B %d, %Y at %H:%M'),
                'author': b.user.username,
                'id': b.id
            }
            for b in broadcasts
        ]
    }

@main.route('/view_report/<int:assignment_id>')
@login_required
def view_report(assignment_id):
    """Generate and display visual plagiarism evidence report"""
    if current_user.role not in ['Admin', 'Lecturer', 'Rep']:
        flash('Access denied', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Get the suspicious assignment
    assignment = Assignment.query.get_or_404(assignment_id)
    
    if not assignment.matched_assignment_id or not assignment.similarity_score:
        return '<h1>No plagiarism evidence found</h1><p>This assignment has no similarity matches.</p>'
    
    # Get the matched (original) assignment
    matched_assignment = Assignment.query.get(assignment.matched_assignment_id)
    
    if not matched_assignment or not os.path.exists(assignment.file_path) or not os.path.exists(matched_assignment.file_path):
        return '<h1>Error</h1><p>Could not load comparison files.</p>'
    
    # Extract text from both files
    suspicious_text = extract_text_from_file(assignment.file_path)
    original_text = extract_text_from_file(matched_assignment.file_path)
    
    if not suspicious_text or not original_text:
        return '<h1>Error</h1><p>Could not extract text from files for comparison.</p>'
    
    # Split into lines for comparison
    suspicious_lines = suspicious_text.splitlines()
    original_lines = original_text.splitlines()
    
    # Generate HTML diff
    import difflib
    differ = difflib.HtmlDiff()
    html_diff = differ.make_file(
        original_lines,
        suspicious_lines,
        fromdesc=f'Original: {matched_assignment.user.username} - {matched_assignment.filename}',
        todesc=f'Suspicious: {assignment.user.username} - {assignment.filename}',
        context=True,
        numlines=3
    )
    
    # Add custom styling and header
    report_html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Plagiarism Evidence Report</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }}
            .report-header {{
                background: rgba(255, 255, 255, 0.95);
                padding: 30px;
                border-radius: 15px;
                margin-bottom: 20px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            }}
            .report-header h1 {{
                margin: 0 0 15px 0;
                color: #333;
                font-size: 28px;
            }}
            .similarity-badge {{
                display: inline-block;
                padding: 10px 20px;
                background: {'#ef4444' if assignment.similarity_score > 70 else '#f59e0b' if assignment.similarity_score > 50 else '#10b981'};
                color: white;
                border-radius: 25px;
                font-size: 20px;
                font-weight: bold;
                margin: 10px 0;
            }}
            .info-grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                margin-top: 20px;
            }}
            .info-card {{
                background: #f8f9fa;
                padding: 15px;
                border-radius: 10px;
                border-left: 4px solid #667eea;
            }}
            .info-card h3 {{
                margin: 0 0 10px 0;
                color: #667eea;
                font-size: 14px;
                text-transform: uppercase;
            }}
            .info-card p {{
                margin: 5px 0;
                color: #555;
            }}
            .back-button {{
                display: inline-block;
                padding: 10px 20px;
                background: #667eea;
                color: white;
                text-decoration: none;
                border-radius: 8px;
                margin-top: 15px;
                transition: background 0.3s;
            }}
            .back-button:hover {{
                background: #5568d3;
            }}
            table.diff {{
                background: white;
                border-radius: 15px;
                overflow: hidden;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                width: 100%;
            }}
        </style>
    </head>
    <body>
        <div class="report-header">
            <h1>🔍 Plagiarism Evidence Report</h1>
            <div class="similarity-badge">
                Similarity Score: {assignment.similarity_score:.1f}%
            </div>
            <div class="info-grid">
                <div class="info-card">
                    <h3>📄 Suspicious Submission</h3>
                    <p><strong>Student:</strong> {assignment.user.username}</p>
                    <p><strong>File:</strong> {assignment.filename}</p>
                    <p><strong>Submitted:</strong> {assignment.created_at.strftime('%B %d, %Y at %H:%M')}</p>
                </div>
                <div class="info-card">
                    <h3>📋 Matched Original</h3>
                    <p><strong>Student:</strong> {matched_assignment.user.username}</p>
                    <p><strong>File:</strong> {matched_assignment.filename}</p>
                    <p><strong>Submitted:</strong> {matched_assignment.created_at.strftime('%B %d, %Y at %H:%M')}</p>
                </div>
            </div>
            <a href="javascript:history.back()" class="back-button">← Back to Dashboard</a>
        </div>
        {html_diff}
    </body>
    </html>
    '''
    
    return report_html

@main.route('/generate_groups', methods=['POST'])
@login_required
def generate_groups():
    """Generate random student groups for class activities"""
    if current_user.role != 'Rep':
        flash('Access denied. Rep privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    group_size = request.form.get('group_size', type=int)
    
    if not group_size or group_size < 2:
        flash('Group size must be at least 2 students.', 'error')
        return redirect(url_for('main.rep_dashboard'))
    
    # Get all students in the rep's class group
    if not current_user.class_group_id:
        flash('You must be part of a class group to generate groups.', 'error')
        return redirect(url_for('main.rep_dashboard'))
    
    students = User.query.filter_by(
        class_group_id=current_user.class_group_id,
        role='Student'
    ).all()
    
    if not students:
        flash('No students found in your class group.', 'error')
        return redirect(url_for('main.rep_dashboard'))
    
    if len(students) < group_size:
        flash(f'Not enough students. You have {len(students)} students but requested groups of {group_size}.', 'error')
        return redirect(url_for('main.rep_dashboard'))
    
    # Shuffle students randomly
    import random
    shuffled_students = students.copy()
    random.shuffle(shuffled_students)
    
    # Split into groups
    groups = []
    for i in range(0, len(shuffled_students), group_size):
        group = shuffled_students[i:i + group_size]
        groups.append(group)
    
    # Get class group info
    from app.models import ClassGroup
    class_group = ClassGroup.query.get(current_user.class_group_id)
    
    return render_template('groups_result.html', 
                         groups=groups, 
                         group_size=group_size,
                         class_group=class_group,
                         total_students=len(students))

@main.route('/run_archiver', methods=['POST'])
@login_required
def run_archiver():
    """Archive old assignments to cold storage (simulated)"""
    if current_user.role != 'Admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    import shutil
    
    # Get all assignments that haven't been archived yet
    assignments = Assignment.query.filter(Assignment.archive_link.is_(None)).all()
    
    if not assignments:
        flash('No files to archive. All assignments are already in cold storage.', 'info')
        return redirect(url_for('main.admin_dashboard'))
    
    # Create archive directory if it doesn't exist
    archive_dir = os.path.join(current_app.static_folder, 'archive')
    os.makedirs(archive_dir, exist_ok=True)
    
    archived_count = 0
    failed_count = 0
    
    for assignment in assignments:
        try:
            # Check if original file exists
            if os.path.exists(assignment.file_path):
                # Create unique filename for archive
                timestamp = assignment.created_at.strftime('%Y%m%d_%H%M%S')
                archive_filename = f"{assignment.user_id}_{timestamp}_{assignment.filename}"
                archive_path = os.path.join(archive_dir, archive_filename)
                
                # Move file to archive (simulating cloud upload)
                shutil.move(assignment.file_path, archive_path)
                
                # Update assignment with archive link
                assignment.archive_link = f'/static/archive/{archive_filename}'
                assignment.file_path = archive_path  # Update to new path
                
                archived_count += 1
            else:
                # File doesn't exist, just mark as archived
                assignment.archive_link = f'/static/archive/missing_{assignment.filename}'
                failed_count += 1
        except Exception as e:
            print(f"Error archiving {assignment.filename}: {e}")
            failed_count += 1
    
    # Commit all changes
    db.session.commit()
    
    if archived_count > 0:
        flash(f'📦 Successfully archived {archived_count} files to Cold Storage!', 'success')
    if failed_count > 0:
        flash(f'⚠️ {failed_count} files could not be archived.', 'warning')
    
    return redirect(url_for('main.admin_dashboard'))

@main.route('/class_chat')
@login_required
def class_chat():
    """Real-time class chat using SocketIO"""
    if not current_user.class_group_id:
        flash('You must be in a class group to access the chat.', 'error')
        return redirect(url_for('main.dashboard'))
    
    return render_template('class_chat.html')

@main.route('/forum')
@login_required
def forum():
    """View all forum posts for the user's class group"""
    if not current_user.class_group_id:
        flash('You must be in a class group to access the forum.', 'error')
        return redirect(url_for('main.dashboard'))
    
    from app.models import ForumPost
    posts = ForumPost.query.filter_by(class_group_id=current_user.class_group_id).order_by(ForumPost.timestamp.desc()).all()
    
    return render_template('forum_list.html', posts=posts)

@main.route('/forum/create', methods=['POST'])
@login_required
@premium_required
def forum_create():
    """Create a new forum post"""
    if not current_user.class_group_id:
        flash('You must be in a class group to post.', 'error')
        return redirect(url_for('main.dashboard'))
    
    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()
    
    if not title or not content:
        flash('Title and content are required.', 'error')
        return redirect(url_for('main.forum'))
    
    from app.models import ForumPost
    post = ForumPost(
        title=title,
        content=content,
        user_id=current_user.id,
        class_group_id=current_user.class_group_id
    )
    db.session.add(post)
    db.session.commit()
    
    flash('✅ Question posted successfully!', 'success')
    return redirect(url_for('main.forum_post', post_id=post.id))

@main.route('/forum/<int:post_id>')
@login_required
def forum_post(post_id):
    """View a single forum post with all replies"""
    from app.models import ForumPost
    post = ForumPost.query.get_or_404(post_id)
    
    # Security: Only users in the same class can view
    if post.class_group_id != current_user.class_group_id:
        flash('Access denied.', 'error')
        return redirect(url_for('main.forum'))
    
    return render_template('forum_post.html', post=post)

@main.route('/forum/<int:post_id>/reply', methods=['POST'])
@login_required
@premium_required
def forum_reply(post_id):
    """Add a reply to a forum post"""
    from app.models import ForumPost, ForumReply
    post = ForumPost.query.get_or_404(post_id)
    
    # Security: Only users in the same class can reply
    if post.class_group_id != current_user.class_group_id:
        flash('Access denied.', 'error')
        return redirect(url_for('main.forum'))
    
    content = request.form.get('content', '').strip()
    
    if not content:
        flash('Reply content cannot be empty.', 'error')
        return redirect(url_for('main.forum_post', post_id=post_id))
    
    reply = ForumReply(
        content=content,
        user_id=current_user.id,
        post_id=post_id
    )
    db.session.add(reply)
    db.session.commit()
    
    flash('✅ Reply added!', 'success')
    return redirect(url_for('main.forum_post', post_id=post_id))

@main.route('/download-all-zip')
@login_required
def download_all_zip():
    # Only Admin, Lecturer, and Rep can download all assignments
    if current_user.role not in ['Admin', 'Lecturer', 'Rep']:
        flash('Access denied. Lecturer or Rep privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    import zipfile
    import io
    from datetime import datetime
    
    # Get all assignments
    assignments = Assignment.query.all()
    
    if not assignments:
        flash('No assignments to download.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Create a BytesIO object to store the zip file in memory
    memory_file = io.BytesIO()
    
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for assignment in assignments:
            if os.path.exists(assignment.file_path):
                # Create a unique filename with student name
                student_name = assignment.user.username
                original_filename = assignment.filename
                zip_filename = f"{student_name}_{original_filename}"
                
                # Add file to zip
                zipf.write(assignment.file_path, zip_filename)
    
    # Seek to the beginning of the BytesIO object
    memory_file.seek(0)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    zip_filename = f'all_assignments_{timestamp}.zip'
    
    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name=zip_filename
    )

@main.route('/download-by-course/<int:course_id>')
@login_required
def download_by_course(course_id):
    """Download all assignments for a specific course"""
    if current_user.role not in ['Admin', 'Lecturer', 'Rep']:
        flash('Access denied. Lecturer or Rep privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    import zipfile
    import io
    from datetime import datetime
    
    # Get course
    course = Course.query.get_or_404(course_id)
    
    # For course lecturers: verify they teach this course
    if current_user.role == 'Lecturer' and course.lecturer_id != current_user.id:
        flash('You can only download assignments for courses you teach.', 'error')
        return redirect(url_for('main.lecturer_dashboard'))
    
    # Get assignments for this course
    assignments = Assignment.query.filter_by(course_id=course_id).all()
    
    if not assignments:
        flash(f'No assignments found for {course.name}.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Create a BytesIO object to store the zip file in memory
    memory_file = io.BytesIO()
    
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for assignment in assignments:
            if os.path.exists(assignment.file_path):
                # Create a unique filename with student name
                student_name = assignment.user.username
                original_filename = assignment.filename
                zip_filename = f"{student_name}_{original_filename}"
                
                # Add file to zip
                zipf.write(assignment.file_path, zip_filename)
    
    # Seek to the beginning of the BytesIO object
    memory_file.seek(0)
    
    # Generate filename with course name and timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_course_name = course.name.replace(' ', '_').replace('/', '_')
    zip_filename = f'{safe_course_name}_assignments_{timestamp}.zip'
    
    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name=zip_filename
    )

@main.route('/manage_timetable', methods=['POST'])
@login_required
def manage_timetable():
    """Add or delete timetable events (Rep only)"""
    if current_user.role != 'Rep':
        flash('Access denied. Rep privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    if not current_user.class_group_id:
        flash('You must be part of a class group to manage timetable.', 'error')
        return redirect(url_for('main.rep_dashboard'))
    
    action = request.form.get('action')
    
    if action == 'add':
        # Add new timetable event
        day = request.form.get('day')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        course_name = request.form.get('course_name')
        venue = request.form.get('venue')
        
        # Validation
        if not all([day, start_time, end_time, course_name, venue]):
            flash('All fields are required to add a timetable event.', 'error')
            return redirect(url_for('main.rep_dashboard'))
        
        # Create new event
        event = TimetableEvent(
            day=day,
            start_time=start_time,
            end_time=end_time,
            course_name=course_name.strip(),
            venue=venue.strip(),
            class_group_id=current_user.class_group_id
        )
        db.session.add(event)
        db.session.commit()
        
        flash(f'✅ Timetable event added: {course_name} on {day}', 'success')
    
    elif action == 'delete':
        # Delete timetable event
        event_id = request.form.get('event_id')
        
        if not event_id:
            flash('Event ID is required to delete.', 'error')
            return redirect(url_for('main.rep_dashboard'))
        
        event = TimetableEvent.query.get(event_id)
        
        if not event:
            flash('Event not found.', 'error')
            return redirect(url_for('main.rep_dashboard'))
        
        # Security check: Only rep of the class can delete
        if event.class_group_id != current_user.class_group_id:
            flash('Access denied. You can only delete events from your class.', 'error')
            return redirect(url_for('main.rep_dashboard'))
        
        db.session.delete(event)
        db.session.commit()
        
        flash('✅ Timetable event deleted successfully!', 'success')
    
    else:
        flash('Invalid action.', 'error')
    
    return redirect(url_for('main.rep_dashboard'))

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the distance between two points on Earth using Haversine formula
    Returns distance in kilometers
    """
    # Radius of Earth in kilometers
    R = 6371.0
    
    # Convert degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Differences
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Haversine formula
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c
    return distance

@main.route('/start_attendance', methods=['POST'])
@login_required
@premium_required
def start_attendance():
    """Start an attendance session (Rep and Lecturer)"""
    if current_user.role not in ['Rep', 'Admin', 'Lecturer']:
        flash('Access denied. Lecturer or Rep privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    course_id = request.form.get('course_id')
    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')
    
    # Validation
    if not all([course_id, latitude, longitude]):
        flash('Course and location are required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    try:
        latitude = float(latitude)
        longitude = float(longitude)
        course_id = int(course_id)
    except ValueError:
        flash('Invalid location or course data.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Verify course exists
    course = Course.query.get(course_id)
    if not course:
        flash('Invalid course selection.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # For Reps: verify course belongs to their class
    if current_user.role == 'Rep' and course.class_group_id != current_user.class_group_id:
        flash('Invalid course selection.', 'error')
        return redirect(url_for('main.rep_dashboard'))
    
    # For Lecturers: verify they teach this course
    if current_user.role in ['Admin', 'Lecturer'] and course.lecturer_id != current_user.id:
        flash('You can only start attendance for courses you teach.', 'error')
        return redirect(url_for('main.admin_dashboard'))
    
    # Close any old active sessions for this course
    old_sessions = AttendanceSession.query.filter_by(course_id=course_id, is_active=True).all()
    for old_session in old_sessions:
        old_session.is_active = False
    
    # Create new attendance session
    new_session = AttendanceSession(
        course_id=course_id,
        created_by_id=current_user.id,
        latitude=latitude,
        longitude=longitude,
        is_active=True
    )
    db.session.add(new_session)
    db.session.commit()
    
    flash(f'✅ Attendance session started for {course.name}!', 'success')
    
    # Redirect based on role
    if current_user.role == 'Rep':
        return redirect(url_for('main.rep_dashboard'))
    else:
        return redirect(url_for('main.admin_dashboard'))

@main.route('/mark_attendance', methods=['POST'])
@login_required
@premium_required
def mark_attendance():
    """Mark attendance for a student"""
    if current_user.role not in ['Student', 'Rep']:
        flash('Access denied.', 'error')
        return redirect(url_for('main.dashboard'))
    
    course_id = request.form.get('course_id')
    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')
    student_name = request.form.get('student_name', '').strip()
    index_number = request.form.get('index_number', '').strip()
    
    # Validation
    if not all([course_id, latitude, longitude, student_name, index_number]):
        flash('All fields are required (Course, Name, Index Number, Location).', 'error')
        return redirect(url_for('main.student_dashboard'))
    
    try:
        latitude = float(latitude)
        longitude = float(longitude)
        course_id = int(course_id)
    except ValueError:
        flash('Invalid location or course data.', 'error')
        return redirect(url_for('main.student_dashboard'))
    
    # Find active session for this course
    active_session = AttendanceSession.query.filter_by(
        course_id=course_id,
        is_active=True
    ).order_by(AttendanceSession.timestamp.desc()).first()
    
    if not active_session:
        flash('❌ No active attendance session for this course.', 'error')
        return redirect(url_for('main.student_dashboard'))
    
    # Check if student already marked attendance for this session
    existing_record = AttendanceRecord.query.filter_by(
        session_id=active_session.id,
        student_id=current_user.id
    ).first()
    
    if existing_record:
        flash('⚠️ You have already marked attendance for this session.', 'warning')
        return redirect(url_for('main.student_dashboard'))
    
    # Calculate distance using Haversine formula
    distance = haversine_distance(
        active_session.latitude,
        active_session.longitude,
        latitude,
        longitude
    )
    
    # Check if within 50 meters (0.05 km)
    if distance < 0.05:
        # Mark attendance
        record = AttendanceRecord(
            session_id=active_session.id,
            student_id=current_user.id,
            student_name=student_name,
            index_number=index_number,
            status='Present'
        )
        db.session.add(record)
        db.session.commit()
        
        flash(f'✅ Attendance marked! Welcome {student_name}.', 'success')
    else:
        flash(f'❌ Too far from class! You must be in the room. (Distance: {distance*1000:.0f}m)', 'error')
    
    return redirect(url_for('main.student_dashboard'))

@main.route('/export_attendance/<int:course_id>')
@login_required
def export_attendance(course_id):
    """Export attendance records as CSV (Rep and Lecturer)"""
    if current_user.role not in ['Rep', 'Admin', 'Lecturer']:
        flash('Access denied. Lecturer or Rep privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Verify course exists
    course = Course.query.get_or_404(course_id)
    
    # For Reps: verify course belongs to their class
    if current_user.role == 'Rep' and course.class_group_id != current_user.class_group_id:
        flash('Access denied.', 'error')
        return redirect(url_for('main.rep_dashboard'))
    
    # For Lecturers: verify they teach this course
    if current_user.role in ['Admin', 'Lecturer'] and course.lecturer_id != current_user.id:
        flash('You can only export attendance for courses you teach.', 'error')
        return redirect(url_for('main.admin_dashboard'))
    
    # Get all sessions for this course
    sessions = AttendanceSession.query.filter_by(course_id=course_id).order_by(AttendanceSession.timestamp.desc()).all()
    
    # Create CSV
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Session Date', 'Session Time', 'Student Name', 'Student Email', 'Status', 'Marked At'])
    
    # Write data
    for session in sessions:
        for record in session.records:
            writer.writerow([
                session.timestamp.strftime('%Y-%m-%d'),
                session.timestamp.strftime('%H:%M:%S'),
                record.student.username,
                record.student.email,
                record.status,
                record.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            ])
    
    # Prepare response
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=attendance_{course.name.replace(" ", "_")}_{datetime.now().strftime("%Y%m%d")}.csv'
        }
    )

@main.route('/activate_trial', methods=['POST'])
@login_required
def activate_trial():
    """Activate 14-day free trial for Rep's class group"""
    if current_user.role != 'Rep':
        flash('Access denied. Rep privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    if not current_user.class_group_id:
        flash('You must be part of a class group to activate trial.', 'error')
        return redirect(url_for('main.rep_dashboard'))
    
    from app.models import ClassGroup
    class_group = ClassGroup.query.get(current_user.class_group_id)
    
    if not class_group:
        flash('Class group not found.', 'error')
        return redirect(url_for('main.rep_dashboard'))
    
    # Check if trial already used
    if class_group.trial_used:
        flash('❌ Free trial has already been used for this class.', 'error')
        return redirect(url_for('main.rep_dashboard'))
    
    # Activate 14-day trial
    class_group.trial_used = True
    class_group.premium_expiry = datetime.utcnow() + timedelta(days=14)
    db.session.commit()
    
    flash('🎉 Free Trial Active! Your class has 14 days of premium access.', 'success')
    return redirect(url_for('main.rep_dashboard'))

@main.route('/verify_payment/<reference>')
@login_required
def verify_payment(reference):
    """Verify Paystack payment and extend premium subscription"""
    if current_user.role != 'Rep':
        flash('Access denied. Rep privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    if not current_user.class_group_id:
        flash('You must be part of a class group.', 'error')
        return redirect(url_for('main.rep_dashboard'))
    
    from app.models import ClassGroup
    class_group = ClassGroup.query.get(current_user.class_group_id)
    
    if not class_group:
        flash('Class group not found.', 'error')
        return redirect(url_for('main.rep_dashboard'))
    
    # Paystack Secret Key (PLACEHOLDER - Replace with your actual key)
    PAYSTACK_SECRET_KEY = 'sk_test_YOUR_SECRET_KEY_HERE'
    
    # Verify payment with Paystack API
    try:
        headers = {
            'Authorization': f'Bearer {PAYSTACK_SECRET_KEY}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(
            f'https://api.paystack.co/transaction/verify/{reference}',
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data['status'] and data['data']['status'] == 'success':
                # Payment successful - get amount in kobo (divide by 100 for GHS)
                amount_kobo = data['data']['amount']
                amount_ghs = amount_kobo / 100
                
                # Determine subscription duration based on amount
                if amount_ghs >= 205:
                    # Yearly subscription (365 days)
                    days_to_add = 365
                    plan_name = 'Yearly'
                elif amount_ghs >= 100:
                    # Semester subscription (120 days)
                    days_to_add = 120
                    plan_name = 'Semester'
                else:
                    flash('❌ Payment amount is insufficient for any subscription plan.', 'error')
                    return redirect(url_for('main.rep_dashboard'))
                
                # Extend premium expiry
                if class_group.premium_expiry and class_group.premium_expiry > datetime.utcnow():
                    # Add to existing expiry
                    class_group.premium_expiry = class_group.premium_expiry + timedelta(days=days_to_add)
                else:
                    # Start from now
                    class_group.premium_expiry = datetime.utcnow() + timedelta(days=days_to_add)
                
                db.session.commit()
                
                flash(f'✅ Subscription Extended! {plan_name} plan activated ({days_to_add} days).', 'success')
            else:
                flash('❌ Payment verification failed. Transaction was not successful.', 'error')
        else:
            flash('❌ Could not verify payment. Please contact support.', 'error')
    
    except Exception as e:
        print(f"Payment verification error: {e}")
        flash('❌ Error verifying payment. Please try again or contact support.', 'error')
    
    return redirect(url_for('main.rep_dashboard'))

# PWA Routes
@main.route('/sw.js')
def service_worker():
    """Serve the service worker with correct MIME type"""
    return send_from_directory(current_app.static_folder, 'sw.js', mimetype='application/javascript')

@main.route('/manifest.json')
def manifest():
    """Serve the PWA manifest with correct MIME type"""
    return send_from_directory(current_app.static_folder, 'manifest.json', mimetype='application/json')

@main.route('/favicon.ico')
def favicon():
    """Serve favicon"""
    return send_from_directory(current_app.static_folder, 'icon-192x192.png', mimetype='image/png')

@main.route('/subscribe', methods=['POST'])
@login_required
def subscribe():
    """Save push subscription data for the current user"""
    try:
        subscription_data = request.get_json()
        
        if not subscription_data:
            return jsonify({'error': 'No subscription data provided'}), 400
        
        # Extract subscription details
        endpoint = subscription_data.get('endpoint')
        keys = subscription_data.get('keys', {})
        p256dh_key = keys.get('p256dh')
        auth_key = keys.get('auth')
        
        if not all([endpoint, p256dh_key, auth_key]):
            return jsonify({'error': 'Invalid subscription data'}), 400
        
        # Check if subscription already exists for this user
        existing_subscription = PushSubscription.query.filter_by(
            user_id=current_user.id,
            endpoint=endpoint
        ).first()
        
        if existing_subscription:
            # Update existing subscription
            existing_subscription.p256dh_key = p256dh_key
            existing_subscription.auth_key = auth_key
        else:
            # Create new subscription
            new_subscription = PushSubscription(
                user_id=current_user.id,
                endpoint=endpoint,
                p256dh_key=p256dh_key,
                auth_key=auth_key
            )
            db.session.add(new_subscription)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Subscription saved successfully'})
    
    except Exception as e:
        print(f"Error saving push subscription: {e}")
        return jsonify({'error': 'Failed to save subscription'}), 500

# Password Reset Routes
@main.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password form - send reset email"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        if not email:
            flash('Please enter your email address.', 'error')
            return render_template('forgot_password.html')
        
        # Find user by email
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Generate reset token
            token = user.generate_password_reset_token()
            db.session.commit()
            
            # Send reset email
            try:
                reset_url = url_for('main.reset_password', token=token, _external=True)
                
                msg = Message(
                    'Password Reset Request - UniPortal',
                    sender=('UniPortal', 'ko2527600@gmail.com'),
                    recipients=[user.email]
                )
                
                msg.body = f'''Hello {user.username},

You have requested to reset your password for your UniPortal account.

Click the link below to reset your password:
{reset_url}

This link will expire in 1 hour for security reasons.

If you did not request this password reset, please ignore this email.

Best regards,
UniPortal Team'''
                
                msg.html = f'''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <div style="background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); padding: 2rem; text-align: center; border-radius: 10px 10px 0 0;">
                        <h1 style="color: white; margin: 0;">🔒 Password Reset</h1>
                    </div>
                    
                    <div style="background: #f8fafc; padding: 2rem; border-radius: 0 0 10px 10px;">
                        <p>Hello <strong>{user.username}</strong>,</p>
                        
                        <p>You have requested to reset your password for your UniPortal account.</p>
                        
                        <div style="text-align: center; margin: 2rem 0;">
                            <a href="{reset_url}" 
                               style="background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); 
                                      color: white; 
                                      padding: 12px 24px; 
                                      text-decoration: none; 
                                      border-radius: 8px; 
                                      font-weight: bold;
                                      display: inline-block;">
                                Reset My Password
                            </a>
                        </div>
                        
                        <p style="color: #64748b; font-size: 14px;">
                            <strong>⏰ This link will expire in 1 hour</strong> for security reasons.
                        </p>
                        
                        <p style="color: #64748b; font-size: 14px;">
                            If you did not request this password reset, please ignore this email.
                        </p>
                        
                        <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 2rem 0;">
                        
                        <p style="color: #64748b; font-size: 12px; text-align: center;">
                            Best regards,<br>
                            <strong>UniPortal Team</strong>
                        </p>
                    </div>
                </div>
                '''
                
                mail.send(msg)
                flash('✅ Password reset instructions have been sent to your email address.', 'success')
                
            except Exception as e:
                print(f"Error sending reset email: {str(e)}")
                flash('❌ Error sending reset email. Please try again later.', 'error')
        else:
            # Don't reveal if email exists or not for security
            flash('✅ If an account with that email exists, password reset instructions have been sent.', 'info')
        
        return redirect(url_for('main.login'))
    
    return render_template('forgot_password.html')

@main.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with token"""
    # Find user by token
    user = User.query.filter_by(password_reset_token=token).first()
    
    if not user or not user.verify_password_reset_token(token):
        flash('❌ Invalid or expired password reset link. Please request a new one.', 'error')
        return redirect(url_for('main.forgot_password'))
    
    if request.method == 'POST':
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        # Validation
        if not new_password:
            flash('Please enter a new password.', 'error')
            return render_template('reset_password.html', token=token)
        
        if len(new_password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return render_template('reset_password.html', token=token)
        
        if new_password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('reset_password.html', token=token)
        
        # Reset password
        user.reset_password(new_password)
        db.session.commit()
        
        flash('✅ Your password has been reset successfully! You can now log in with your new password.', 'success')
        return redirect(url_for('main.login'))
    
    return render_template('reset_password.html', token=token, user=user)