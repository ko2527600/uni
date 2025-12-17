#!/usr/bin/env python3
"""
Fix trial access for testing purposes
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, ClassGroup

def fix_trial_access():
    """Fix trial access for current user"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🔧 Fixing Trial Access")
            print("=" * 40)
            
            # Get all users and let user choose
            users = User.query.all()
            
            if not users:
                print("❌ No users found. Please register first.")
                return
            
            if len(users) == 1:
                user = users[0]
                print(f"👤 Working with user: {user.username}")
            else:
                print("👥 Multiple users found:")
                for i, u in enumerate(users):
                    print(f"   {i+1}. {u.username} ({u.email}) - Role: {u.role}")
                
                try:
                    choice = int(input("\nEnter user number (or press Enter for user 1): ") or "1")
                    user = users[choice-1]
                    print(f"👤 Selected user: {user.username}")
                except (ValueError, IndexError):
                    user = users[0]
                    print(f"👤 Using first user: {user.username}")
            
            print(f"   Current role: {user.role}")
            print(f"   Current class group: {user.class_group_id}")
            
            # Step 1: Make user a Rep if not already
            if user.role != 'Rep':
                print(f"🔄 Changing role from {user.role} to Rep...")
                user.role = 'Rep'
            else:
                print("✅ User is already a Rep")
            
            # Step 2: Ensure user is in a class group
            if not user.class_group_id:
                print("🔍 User not in any class group. Finding or creating one...")
                
                # Try to find an existing class group with available trial
                available_class = ClassGroup.query.filter_by(trial_used=False).first()
                
                if available_class:
                    print(f"🏫 Found class with available trial: {available_class.name}")
                    user.class_group_id = available_class.id
                else:
                    print("📚 Creating a new class group with trial available...")
                    from app.models import University
                    
                    # Get or create university
                    university = University.query.first()
                    if not university:
                        university = University(name='Test University', domain='test.edu')
                        db.session.add(university)
                        db.session.commit()
                        print(f"🏛️ Created university: {university.name}")
                    
                    # Create class group with unique codes
                    import random
                    random_num = random.randint(100, 999)
                    
                    class_group = ClassGroup(
                        name=f'My Test Class {random_num}',
                        code=f'TEST-{random_num}',
                        join_code=f'TEST{random_num}',
                        lecturer_code=f'LEC{random_num}',
                        university_id=university.id,
                        trial_used=False,  # Ensure trial is available
                        created_by=user.id,
                        lecturer_id=user.id
                    )
                    db.session.add(class_group)
                    db.session.commit()
                    
                    user.class_group_id = class_group.id
                    print(f"🏫 Created and joined class: {class_group.name}")
                    print(f"   Join Code: {class_group.join_code}")
                    print(f"   Lecturer Code: {class_group.lecturer_code}")
            else:
                print(f"✅ User is in class group: {user.class_group.name}")
            
            # Step 3: Ensure trial is available for the class group
            if user.class_group:
                if user.class_group.trial_used:
                    print("🔄 Resetting trial status for class group...")
                    user.class_group.trial_used = False
                    user.class_group.premium_expiry = None
                else:
                    print("✅ Trial is already available for this class")
            
            # Save all changes
            db.session.commit()
            
            print("\n" + "="*50)
            print("✅ TRIAL ACCESS SUCCESSFULLY FIXED!")
            print("="*50)
            print(f"👤 User: {user.username}")
            print(f"📧 Email: {user.email}")
            print(f"👑 Role: {user.role}")
            print(f"🏫 Class Group: {user.class_group.name}")
            print(f"🎁 Trial Available: YES")
            print(f"💎 Premium Status: {user.class_group.is_active_premium}")
            
            print("\n🎯 NEXT STEPS:")
            print("1. 🌐 Go to your UniPortal subscription page")
            print("2. 🔄 Refresh the page (Ctrl+F5 or Cmd+R)")
            print("3. 👀 You should now see the GREEN 'Free Trial' card")
            print("4. 🎉 Click 'Start Free Trial' to activate 14 days of premium!")
            
            print("\n📋 TEMPLATE CONDITIONS MET:")
            print(f"   ✅ current_user.class_group: {user.class_group is not None}")
            print(f"   ✅ not current_user.class_group.trial_used: {not user.class_group.trial_used}")
            print(f"   ✅ current_user.role == 'Rep': {user.role == 'Rep'}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()

if __name__ == "__main__":
    fix_trial_access()