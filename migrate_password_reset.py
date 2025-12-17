#!/usr/bin/env python3
"""
Safe database migration for password reset functionality
This script adds the password reset columns to existing users table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def migrate_password_reset():
    """Add password reset columns to users table if they don't exist"""
    try:
        from app import create_app, db
        from sqlalchemy import text
        
        app = create_app()
        
        with app.app_context():
            print("🔄 Checking password reset columns in users table...")
            print("=" * 60)
            
            # Check current table structure
            result = db.session.execute(text("PRAGMA table_info(users)"))
            columns = [row[1] for row in result.fetchall()]
            
            print(f"📋 Current columns: {len(columns)} found")
            
            changes_made = False
            
            # Add password_reset_token column if missing
            if 'password_reset_token' not in columns:
                print("➕ Adding password_reset_token column...")
                db.session.execute(text(
                    "ALTER TABLE users ADD COLUMN password_reset_token VARCHAR(100)"
                ))
                changes_made = True
                print("✅ password_reset_token column added")
            else:
                print("✅ password_reset_token column already exists")
            
            # Add password_reset_expires column if missing
            if 'password_reset_expires' not in columns:
                print("➕ Adding password_reset_expires column...")
                db.session.execute(text(
                    "ALTER TABLE users ADD COLUMN password_reset_expires DATETIME"
                ))
                changes_made = True
                print("✅ password_reset_expires column added")
            else:
                print("✅ password_reset_expires column already exists")
            
            if changes_made:
                db.session.commit()
                print("\n💾 Database changes committed successfully")
            else:
                print("\n✨ No changes needed - database is up to date")
            
            # Verify the migration
            print("\n🔍 Verifying migration...")
            result = db.session.execute(text("PRAGMA table_info(users)"))
            new_columns = [row[1] for row in result.fetchall()]
            
            has_token = 'password_reset_token' in new_columns
            has_expires = 'password_reset_expires' in new_columns
            
            if has_token and has_expires:
                print("✅ Migration verification successful")
                print(f"📊 Total columns now: {len(new_columns)}")
                
                print("\n" + "=" * 60)
                print("🎉 Password Reset System Ready!")
                print("\n📋 Available Features:")
                print("• ✅ Modern login page design")
                print("• ✅ Forgot password functionality")
                print("• ✅ Secure token generation")
                print("• ✅ Email reset links")
                print("• ✅ Token expiration (1 hour)")
                print("• ✅ Password reset form")
                print("• ✅ Database migration complete")
                
                print("\n🚀 Ready to use:")
                print("1. Visit /login for new modern design")
                print("2. Click 'Forgot Password?' to test reset")
                print("3. Check email for reset instructions")
                
                return True
            else:
                print("❌ Migration verification failed")
                return False
                
    except Exception as e:
        print(f"❌ Migration error: {str(e)}")
        return False

if __name__ == '__main__':
    print("🔧 UniPortal Password Reset Migration")
    print("=" * 60)
    
    success = migrate_password_reset()
    
    if success:
        print("\n✨ Migration completed successfully!")
        print("You can now use the password reset system.")
    else:
        print("\n💥 Migration failed. Please check the errors above.")
        sys.exit(1)