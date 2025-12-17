#!/usr/bin/env python3
"""
Debug real-time chat functionality
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, ClassGroup, ForumPost, ForumReply

def debug_chat():
    """Debug chat functionality"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🔍 Debugging Real-Time Chat")
            print("=" * 50)
            
            # Check users and their class groups
            users = User.query.all()
            print(f"\n👥 Total Users: {len(users)}")
            
            for user in users:
                print(f"\n👤 User: {user.username}")
                print(f"   Role: {user.role}")
                print(f"   Class Group ID: {user.class_group_id}")
                if user.class_group:
                    print(f"   Class Group: {user.class_group.name}")
                else:
                    print("   ❌ Not in any class group")
            
            # Check class groups
            class_groups = ClassGroup.query.all()
            print(f"\n🏫 Total Class Groups: {len(class_groups)}")
            
            for group in class_groups:
                print(f"\n📚 Class: {group.name} (ID: {group.id})")
                member_count = User.query.filter_by(class_group_id=group.id).count()
                print(f"   Members: {member_count}")
                
                # Check if there's a chat post for this class
                chat_post = ForumPost.query.filter_by(
                    class_group_id=group.id,
                    title='Class Chat'
                ).first()
                
                if chat_post:
                    message_count = ForumReply.query.filter_by(post_id=chat_post.id).count()
                    print(f"   Chat Messages: {message_count}")
                    
                    # Show recent messages
                    recent_messages = ForumReply.query.filter_by(
                        post_id=chat_post.id
                    ).order_by(ForumReply.timestamp.desc()).limit(5).all()
                    
                    if recent_messages:
                        print("   Recent Messages:")
                        for msg in reversed(recent_messages):
                            print(f"     - {msg.author.username}: {msg.content[:50]}...")
                    else:
                        print("   No messages yet")
                else:
                    print("   No chat post created yet")
            
            print("\n🔧 Troubleshooting Tips:")
            print("1. Make sure users are in the same class group")
            print("2. Check browser console for JavaScript errors")
            print("3. Verify SocketIO connection in browser DevTools")
            print("4. Ensure server is running with socketio.run(), not app.run()")
            
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_chat()