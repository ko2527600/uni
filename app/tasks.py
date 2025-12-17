"""
Celery tasks for UniPortal
Background tasks for email sending, notifications, etc.
"""
from app import create_app, mail
from flask_mail import Message

# Create app and get celery instance
app = create_app()
celery = app.extensions['celery']


@celery.task
def send_email_async(recipient, subject, body):
    """
    Send email asynchronously
    
    Usage:
        from app.tasks import send_email_async
        send_email_async.delay('user@example.com', 'Subject', 'Body text')
    """
    with app.app_context():
        msg = Message(subject, recipients=[recipient])
        msg.body = body
        mail.send(msg)
    return f"Email sent to {recipient}"


@celery.task
def send_verification_email(user_email, verification_code):
    """Send verification code email"""
    with app.app_context():
        msg = Message('UniPortal Verification Code',
                    sender=('UniPortal', 'ko2527600@gmail.com'),
                    recipients=[user_email])
        msg.body = f'''Welcome to UniPortal!

Your verification code is: {verification_code}

Please enter this code to verify your account.

Thank you,
UniPortal Team'''
        mail.send(msg)
    return f"Verification email sent to {user_email}"


@celery.task
def process_plagiarism_check(assignment_id):
    """
    Process plagiarism check in background
    This can be a long-running task
    """
    with app.app_context():
        from app.models import Assignment
        assignment = Assignment.query.get(assignment_id)
        if assignment:
            # Perform plagiarism check
            # ... your plagiarism detection logic here ...
            return f"Plagiarism check completed for assignment {assignment_id}"
    return f"Assignment {assignment_id} not found"


@celery.task
def generate_attendance_report(course_id):
    """Generate attendance report in background"""
    with app.app_context():
        from app.models import Course, AttendanceSession, AttendanceRecord
        course = Course.query.get(course_id)
        if course:
            sessions = AttendanceSession.query.filter_by(course_id=course_id).all()
            total_sessions = len(sessions)
            # Generate report logic here
            return f"Report generated for {course.name}: {total_sessions} sessions"
    return f"Course {course_id} not found"


@celery.task
def send_broadcast_emails(broadcast_id, class_group_id, sender_name):
    """
    Send broadcast message to all students in the class via email
    
    Args:
        broadcast_id: ID of the broadcast message
        class_group_id: ID of the class group (None for all students)
        sender_name: Name of the person who sent the broadcast
    """
    with app.app_context():
        from app.models import Broadcast, User, ClassGroup
        
        broadcast = Broadcast.query.get(broadcast_id)
        if not broadcast:
            return f"Broadcast {broadcast_id} not found"
        
        # Get students to notify
        if class_group_id:
            # Send to students in specific class
            class_group = ClassGroup.query.get(class_group_id)
            students = User.query.filter_by(
                class_group_id=class_group_id,
                role='Student',
                receive_emails=True
            ).all()
            class_name = class_group.name if class_group else "Your Class"
        else:
            # Send to all students (for admin broadcasts)
            students = User.query.filter_by(
                role='Student',
                receive_emails=True
            ).all()
            class_name = "All Students"
        
        # Send email to each student
        sent_count = 0
        for student in students:
            try:
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

Login to UniPortal to view more details: https://uniportal.com

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
                        
                        <div style="text-align: center; margin-top: 30px;">
                            <a href="https://uniportal.com" style="display: inline-block; padding: 12px 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">
                                View on UniPortal
                            </a>
                        </div>
                        
                        <p style="color: #999; font-size: 12px; text-align: center; margin-top: 30px;">
                            To stop receiving email notifications, update your preferences in Settings.
                        </p>
                    </div>
                </div>
                '''
                
                mail.send(msg)
                sent_count += 1
            except Exception as e:
                print(f"Failed to send email to {student.email}: {str(e)}")
                continue
        
        return f"Broadcast emails sent to {sent_count} students"


@celery.task
def cleanup_old_files():
    """Periodic task to clean up old files"""
    import os
    from datetime import datetime, timedelta
    
    with app.app_context():
        # Clean up files older than 90 days
        cutoff_date = datetime.now() - timedelta(days=90)
        # Add your cleanup logic here
        return "Cleanup completed"


@celery.task
def check_subscription_expiry():
    """
    Check all class subscriptions and send reminder emails
    Run this task daily (scheduled via Celery Beat)
    """
    from datetime import datetime, timedelta
    from app.models import ClassGroup, User
    
    with app.app_context():
        now = datetime.utcnow()
        
        # Get all classes with premium expiry dates
        classes = ClassGroup.query.filter(ClassGroup.premium_expiry.isnot(None)).all()
        
        notifications_sent = 0
        
        for class_group in classes:
            days_remaining = (class_group.premium_expiry - now).days
            
            # Get the class rep (creator)
            rep = User.query.get(class_group.created_by)
            if not rep or not rep.email:
                continue
            
            # 7 days before expiry
            if days_remaining == 7:
                send_expiry_reminder_email.delay(
                    rep.email,
                    rep.username,
                    class_group.name,
                    days_remaining,
                    class_group.premium_expiry.strftime('%B %d, %Y')
                )
                notifications_sent += 1
            
            # 3 days before expiry
            elif days_remaining == 3:
                send_expiry_reminder_email.delay(
                    rep.email,
                    rep.username,
                    class_group.name,
                    days_remaining,
                    class_group.premium_expiry.strftime('%B %d, %Y')
                )
                notifications_sent += 1
            
            # On expiry day
            elif days_remaining == 0:
                send_expiry_notification_email.delay(
                    rep.email,
                    rep.username,
                    class_group.name
                )
                notifications_sent += 1
            
            # 3 days after expiry
            elif days_remaining == -3:
                send_final_reminder_email.delay(
                    rep.email,
                    rep.username,
                    class_group.name
                )
                notifications_sent += 1
        
        return f"Subscription check completed. {notifications_sent} notifications sent."


@celery.task
def send_expiry_reminder_email(rep_email, rep_name, class_name, days_remaining, expiry_date):
    """Send reminder email before subscription expires"""
    with app.app_context():
        urgency = "⚠️ URGENT" if days_remaining <= 3 else "⏰ Reminder"
        
        msg = Message(
            f'{urgency}: Premium Expires in {days_remaining} Days',
            sender=('UniPortal', 'ko2527600@gmail.com'),
            recipients=[rep_email]
        )
        
        msg.body = f'''Hello {rep_name},

This is a reminder that your class premium subscription is expiring soon.

Class: {class_name}
Days Remaining: {days_remaining} days
Expires On: {expiry_date}

⚠️ What happens when premium expires:
- Students cannot upload assignments
- Slides and resources become locked
- Forum access will be disabled
- Attendance marking will be unavailable
- Library access will be restricted

🔄 Renew Now to Avoid Interruption:
Login to UniPortal and visit the Subscription page to renew your premium plan.

Pricing:
- Semester Plan: GH₵105 (~5 months)
- Yearly Plan: GH₵205 (12 months)

Renew now: https://uniportal.com/subscription

Thank you for using UniPortal!

Best regards,
UniPortal Team'''
        
        msg.html = f'''
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
            <div style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); padding: 20px; border-radius: 10px 10px 0 0;">
                <h2 style="color: white; margin: 0;">{urgency}: Premium Expiring Soon</h2>
            </div>
            <div style="background: white; padding: 30px; border-radius: 0 0 10px 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <p style="color: #333; font-size: 16px;">Hello <strong>{rep_name}</strong>,</p>
                <p style="color: #666; font-size: 14px;">Your class premium subscription is expiring soon.</p>
                
                <div style="background: #fff3cd; border-left: 4px solid #f59e0b; padding: 20px; margin: 20px 0; border-radius: 5px;">
                    <p style="color: #333; font-size: 15px; margin: 5px 0;"><strong>Class:</strong> {class_name}</p>
                    <p style="color: #333; font-size: 15px; margin: 5px 0;"><strong>Days Remaining:</strong> {days_remaining} days</p>
                    <p style="color: #333; font-size: 15px; margin: 5px 0;"><strong>Expires On:</strong> {expiry_date}</p>
                </div>
                
                <div style="background: #fee; border-left: 4px solid #ef4444; padding: 15px; margin: 20px 0; border-radius: 5px;">
                    <p style="color: #333; font-size: 14px; margin: 0;"><strong>⚠️ What happens when premium expires:</strong></p>
                    <ul style="color: #666; font-size: 13px; margin: 10px 0;">
                        <li>Students cannot upload assignments</li>
                        <li>Slides and resources become locked</li>
                        <li>Forum access will be disabled</li>
                        <li>Attendance marking unavailable</li>
                        <li>Library access restricted</li>
                    </ul>
                </div>
                
                <div style="background: #f0fdf4; border-left: 4px solid #10b981; padding: 15px; margin: 20px 0; border-radius: 5px;">
                    <p style="color: #333; font-size: 14px; margin: 0 0 10px 0;"><strong>💰 Pricing:</strong></p>
                    <p style="color: #666; font-size: 13px; margin: 5px 0;">• Semester Plan: <strong>GH₵105</strong> (~5 months)</p>
                    <p style="color: #666; font-size: 13px; margin: 5px 0;">• Yearly Plan: <strong>GH₵205</strong> (12 months)</p>
                </div>
                
                <div style="text-align: center; margin-top: 30px;">
                    <a href="https://uniportal.com/subscription" style="display: inline-block; padding: 15px 40px; background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); color: white; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px;">
                        Renew Now
                    </a>
                </div>
                
                <p style="color: #999; font-size: 12px; text-align: center; margin-top: 30px;">
                    Thank you for using UniPortal!
                </p>
            </div>
        </div>
        '''
        
        mail.send(msg)
    return f"Expiry reminder sent to {rep_email}"


@celery.task
def send_expiry_notification_email(rep_email, rep_name, class_name):
    """Send notification when subscription expires"""
    with app.app_context():
        msg = Message(
            '🔴 Premium Subscription Expired',
            sender=('UniPortal', 'ko2527600@gmail.com'),
            recipients=[rep_email]
        )
        
        msg.body = f'''Hello {rep_name},

Your class premium subscription has expired today.

Class: {class_name}
Status: EXPIRED

🔒 Features Now Locked:
- Assignment uploads
- Slide downloads
- Forum access
- Attendance marking
- Library access

🔄 Renew Now to Restore Access:
Login to UniPortal and renew your subscription to restore full access for all students.

Pricing:
- Semester Plan: GH₵105 (~5 months)
- Yearly Plan: GH₵205 (12 months)

Renew now: https://uniportal.com/subscription

Best regards,
UniPortal Team'''
        
        msg.html = f'''
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
            <div style="background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); padding: 20px; border-radius: 10px 10px 0 0;">
                <h2 style="color: white; margin: 0;">🔴 Premium Subscription Expired</h2>
            </div>
            <div style="background: white; padding: 30px; border-radius: 0 0 10px 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <p style="color: #333; font-size: 16px;">Hello <strong>{rep_name}</strong>,</p>
                <p style="color: #666; font-size: 14px;">Your class premium subscription has expired today.</p>
                
                <div style="background: #fee; border-left: 4px solid #ef4444; padding: 20px; margin: 20px 0; border-radius: 5px;">
                    <p style="color: #333; font-size: 15px; margin: 5px 0;"><strong>Class:</strong> {class_name}</p>
                    <p style="color: #ef4444; font-size: 18px; margin: 10px 0; font-weight: bold;">Status: EXPIRED</p>
                </div>
                
                <div style="background: #fef2f2; padding: 15px; margin: 20px 0; border-radius: 5px;">
                    <p style="color: #333; font-size: 14px; margin: 0 0 10px 0;"><strong>🔒 Features Now Locked:</strong></p>
                    <ul style="color: #666; font-size: 13px; margin: 0;">
                        <li>Assignment uploads</li>
                        <li>Slide downloads</li>
                        <li>Forum access</li>
                        <li>Attendance marking</li>
                        <li>Library access</li>
                    </ul>
                </div>
                
                <div style="background: #f0fdf4; border-left: 4px solid #10b981; padding: 15px; margin: 20px 0; border-radius: 5px;">
                    <p style="color: #333; font-size: 14px; margin: 0 0 10px 0;"><strong>💰 Renew Now:</strong></p>
                    <p style="color: #666; font-size: 13px; margin: 5px 0;">• Semester Plan: <strong>GH₵105</strong> (~5 months)</p>
                    <p style="color: #666; font-size: 13px; margin: 5px 0;">• Yearly Plan: <strong>GH₵205</strong> (12 months)</p>
                </div>
                
                <div style="text-align: center; margin-top: 30px;">
                    <a href="https://uniportal.com/subscription" style="display: inline-block; padding: 15px 40px; background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); color: white; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px;">
                        Renew Subscription
                    </a>
                </div>
                
                <p style="color: #999; font-size: 12px; text-align: center; margin-top: 30px;">
                    UniPortal Team
                </p>
            </div>
        </div>
        '''
        
        mail.send(msg)
    return f"Expiry notification sent to {rep_email}"


@celery.task
def send_final_reminder_email(rep_email, rep_name, class_name):
    """Send final reminder 3 days after expiry"""
    with app.app_context():
        msg = Message(
            '⚠️ Final Reminder: Renew Your Subscription',
            sender=('UniPortal', 'ko2527600@gmail.com'),
            recipients=[rep_email]
        )
        
        msg.body = f'''Hello {rep_name},

This is a final reminder that your class premium subscription expired 3 days ago.

Class: {class_name}
Status: EXPIRED (3 days ago)

Your students currently have no access to:
- Assignment uploads
- Slide downloads
- Forum discussions
- Attendance marking
- Library resources

Renew now to restore full access: https://uniportal.com/subscription

Pricing:
- Semester Plan: GH₵105 (~5 months)
- Yearly Plan: GH₵205 (12 months)

If you have any questions, please contact support.

Best regards,
UniPortal Team'''
        
        msg.html = f'''
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
            <div style="background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%); padding: 20px; border-radius: 10px 10px 0 0;">
                <h2 style="color: white; margin: 0;">⚠️ Final Reminder</h2>
            </div>
            <div style="background: white; padding: 30px; border-radius: 0 0 10px 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <p style="color: #333; font-size: 16px;">Hello <strong>{rep_name}</strong>,</p>
                <p style="color: #666; font-size: 14px;">Your class premium subscription expired 3 days ago.</p>
                
                <div style="background: #f3f4f6; border-left: 4px solid #6b7280; padding: 20px; margin: 20px 0; border-radius: 5px;">
                    <p style="color: #333; font-size: 15px; margin: 5px 0;"><strong>Class:</strong> {class_name}</p>
                    <p style="color: #6b7280; font-size: 16px; margin: 10px 0; font-weight: bold;">Status: EXPIRED (3 days ago)</p>
                </div>
                
                <p style="color: #666; font-size: 14px;">Your students currently have no access to premium features.</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://uniportal.com/subscription" style="display: inline-block; padding: 15px 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px;">
                        Renew Now
                    </a>
                </div>
                
                <div style="background: #f0fdf4; padding: 15px; margin: 20px 0; border-radius: 5px; text-align: center;">
                    <p style="color: #666; font-size: 13px; margin: 5px 0;">Semester: <strong>GH₵105</strong> | Yearly: <strong>GH₵205</strong></p>
                </div>
                
                <p style="color: #999; font-size: 12px; text-align: center; margin-top: 30px;">
                    UniPortal Team
                </p>
            </div>
        </div>
        '''
        
        mail.send(msg)
    return f"Final reminder sent to {rep_email}"
