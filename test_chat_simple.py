#!/usr/bin/env python3
"""
Simple test to verify chat functionality
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, ClassGroup, ForumPost, ForumReply

def test_chat_message():
    """Test creating a chat message manually"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🧪 Testing Chat Message Creation")
            print("=" * 40)
            
            # Get a user
            user = User.query.first()
            if not user:
                print("❌ No users found")
                return
            
            print(f"👤 User: {user.username}")
            print(f"🏫 Class Group ID: {user.class_group_id}")
            
            if not user.class_group_id:
                print("❌ User not in any class group")
                return
            
            # Get or create chat post
            chat_post = ForumPost.query.filter_by(
                class_group_id=user.class_group_id,
                title='Class Chat'
            ).first()
            
            if not chat_post:
                print("📝 Creating Class Chat post...")
                chat_post = ForumPost(
                    title='Class Chat',
                    content='Real-time class discussion',
                    user_id=user.id,
                    class_group_id=user.class_group_id
                )
                db.session.add(chat_post)
                db.session.commit()
                print("✅ Chat post created")
            else:
                print("✅ Chat post already exists")
            
            # Create a test message
            test_message = ForumReply(
                content="Test message from debug script",
                user_id=user.id,
                post_id=chat_post.id
            )
            db.session.add(test_message)
            db.session.commit()
            
            print("✅ Test message created")
            
            # Check messages
            messages = ForumReply.query.filter_by(post_id=chat_post.id).all()
            print(f"📨 Total messages in chat: {len(messages)}")
            
            for msg in messages[-3:]:  # Show last 3 messages
                print(f"   - {msg.author.username}: {msg.content}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_chat_message()