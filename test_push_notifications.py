#!/usr/bin/env python3
"""
Test Push Notifications Script
Use this script to test sending push notifications to subscribed users.
"""

import sys
import os
import json

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, PushSubscription

def send_test_notification(user_id=None, message="Test notification from UniPortal!"):
    """Send a test push notification"""
    app = create_app()
    
    with app.app_context():
        try:
            # Import pywebpush here to handle missing dependency gracefully
            from pywebpush import webpush, WebPushException
            
            # Get subscriptions
            if user_id:
                subscriptions = PushSubscription.query.filter_by(user_id=user_id).all()
                print(f"📤 Sending notification to user {user_id}...")
            else:
                subscriptions = PushSubscription.query.all()
                print("📤 Sending notification to all subscribed users...")
            
            if not subscriptions:
                print("❌ No push subscriptions found!")
                return False
            
            # VAPID keys (replace with your actual keys)
            VAPID_PRIVATE_KEY = "RXvfRNWKIbsNYQ2Y-Oo9jGV23wCG8-8_UGwqJINK1iE"
            VAPID_PUBLIC_KEY = "BJ0NhRxu2xt6WjuwIBZn4nmfuktPH7I6BLAM5FXbB4OQWAKQP8F_9eyXCymxMZpnabVa5x5RI0_8WZ5gA8QzkQ4"
            VAPID_CLAIMS = {
                "sub": "mailto:your-email@example.com"
            }
            
            if VAPID_PRIVATE_KEY == "YOUR_VAPID_PRIVATE_KEY_HERE":
                print("❌ Please update VAPID keys in this script!")
                print("Run: python generate_vapid_keys.py")
                return False
            
            # Notification payload
            notification_payload = {
                "title": "UniPortal Notification",
                "body": message,
                "icon": "/static/logo.png",
                "badge": "/static/logo.png",
                "url": "/"
            }
            
            success_count = 0
            error_count = 0
            
            for subscription in subscriptions:
                try:
                    # Prepare subscription info
                    subscription_info = {
                        "endpoint": subscription.endpoint,
                        "keys": {
                            "p256dh": subscription.p256dh_key,
                            "auth": subscription.auth_key
                        }
                    }
                    
                    # Send notification
                    webpush(
                        subscription_info=subscription_info,
                        data=json.dumps(notification_payload),
                        vapid_private_key=VAPID_PRIVATE_KEY,
                        vapid_claims=VAPID_CLAIMS
                    )
                    
                    success_count += 1
                    print(f"✅ Sent to user {subscription.user_id}")
                    
                except WebPushException as ex:
                    error_count += 1
                    print(f"❌ Failed to send to user {subscription.user_id}: {ex}")
                    
                    # If subscription is invalid, remove it
                    if ex.response and ex.response.status_code in [400, 404, 410]:
                        print(f"🗑️ Removing invalid subscription for user {subscription.user_id}")
                        db.session.delete(subscription)
                        db.session.commit()
                
                except Exception as ex:
                    error_count += 1
                    print(f"❌ Unexpected error for user {subscription.user_id}: {ex}")
            
            print(f"\n📊 Results: {success_count} sent, {error_count} failed")
            return success_count > 0
            
        except ImportError:
            print("❌ pywebpush not installed!")
            print("Install with: pip install pywebpush")
            return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

def list_subscriptions():
    """List all push subscriptions"""
    app = create_app()
    
    with app.app_context():
        subscriptions = PushSubscription.query.all()
        
        if not subscriptions:
            print("📭 No push subscriptions found")
            return
        
        print(f"📱 Found {len(subscriptions)} push subscriptions:")
        print("-" * 60)
        
        for sub in subscriptions:
            user = User.query.get(sub.user_id)
            print(f"User: {user.username if user else 'Unknown'} (ID: {sub.user_id})")
            print(f"Endpoint: {sub.endpoint[:50]}...")
            print(f"Created: {sub.created_at}")
            print("-" * 60)

if __name__ == "__main__":
    print("🔔 UniPortal Push Notification Test")
    print("=" * 40)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "list":
            list_subscriptions()
        elif command == "test":
            user_id = int(sys.argv[2]) if len(sys.argv) > 2 else None
            message = sys.argv[3] if len(sys.argv) > 3 else "Test notification from UniPortal!"
            send_test_notification(user_id, message)
        else:
            print("Usage:")
            print("  python test_push_notifications.py list")
            print("  python test_push_notifications.py test [user_id] [message]")
    else:
        print("Usage:")
        print("  python test_push_notifications.py list")
        print("  python test_push_notifications.py test [user_id] [message]")
        print("\nExamples:")
        print("  python test_push_notifications.py list")
        print("  python test_push_notifications.py test")
        print("  python test_push_notifications.py test 1 'Hello from UniPortal!'")