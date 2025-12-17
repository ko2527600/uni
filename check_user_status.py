#!/usr/bin/env python3
"""
Check current user status for trial eligibility
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, ClassGroup

def check_user_status():
    """Check user status for trial eligibility"""
    app = create_app()
    
    with app.app_context():
        try:
            # Get all users to see their status
            users = User.query.all()
            
            print("🔍 User Status Check for Trial Eligibility")
            print("=" * 60)
            
            if not users:
                print("❌ No users found in database")
                return
            
            for user in users:
                print(f"\n👤 User: {user.username}")
                print(f"   Email: {user.email}")
                print(f"   Role: {user.role}")
                print(f"   Class Group ID: {user.class_group_id}")
                
                if user.class_group:
                    print(f"   Class Group: {user.class_group.name}")
                    print(f"   Trial Used: {user.class_group.trial_used}")
                    print(f"   Premium Active: {user.class_group.is_active_premium}")
                    if user.class_group.premium_expiry:
                        print(f"   Premium Expiry: {user.class_group.premium_expiry}")
                    
                    # Check trial eligibility
                    can_see_trial = user.class_group and not user.class_group.trial_used
                    can_activate_trial = user.role == 'Rep' and can_see_trial
                    
                    print(f"   ✅ Can See Trial Card: {can_see_trial}")
                    print(f"   ✅ Can Activate Trial: {can_activate_trial}")
                else:
                    print("   ❌ Not in any class group")
                    print("   ✅ Can See Trial Card: False")
                    print("   ✅ Can Activate Trial: False")
                
                print("-" * 40)
            
            # Show all class groups
            print("\n🏫 All Class Groups:")
            print("=" * 60)
            class_groups = ClassGroup.query.all()
            
            for group in class_groups:
                print(f"\n📚 Class: {group.name}")
                print(f"   ID: {group.id}")
                print(f"   Join Code: {group.join_code}")
                print(f"   Lecturer Code: {group.lecturer_code}")
                print(f"   Trial Used: {group.trial_used}")
                print(f"   Premium Active: {group.is_active_premium}")
                if group.premium_expiry:
                    print(f"   Premium Expiry: {group.premium_expiry}")
                
                # Count members
                member_count = User.query.filter_by(class_group_id=group.id).count()
                print(f"   Members: {member_count}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_user_status()