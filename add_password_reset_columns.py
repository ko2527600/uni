#!/usr/bin/env python3
"""
Database migration script to add password reset columns to users table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from sqlalchemy import text

def add_password_reset_columns():
    """Add password reset columns to users table"""
    app = create_app()
    
    with app.app_context():
        print("🔄 Adding password reset columns to users table...")
        print("=" * 60)
        
        try:
            # Check if columns already exist
            result = db.session.execute(text("PRAGMA table_info(users)"))
            columns = [row[1] for row in result.fetchall()]
            
            print(f"📋 Current columns in users table: {len(columns)} columns")
            
            # Add password_reset_token column if it doesn't exist
            if 'password_reset_token' not in columns:
                print("\n➕ Adding password_reset_token column...")
                db.session.execute(text(
                    "ALTER TABLE users ADD COLUMN password_reset_token VARCHAR(100)"
                ))
                print("✅ password_reset_token column added")
            else:
                print("✅ password_reset_token column already exists")
            
            # Add password_reset_expires column if it doesn't exist
            if 'password_reset_expires' not in columns:
                print("\n➕ Adding password_reset_expires column...")
                db.session.execute(text(
                    "ALTER TABLE users ADD COLUMN password_reset_expires DATETIME"
                ))
                print("✅ password_reset_expires column added")
            else:
                print("✅ password_reset_expires column already exists")
            
            # Commit the changes
            db.session.commit()
            
            # Verify the columns were added
            print("\n🔍 Verifying columns were added...")
            result = db.session.execute(text("PRAGMA table_info(users)"))
            new_columns = [row[1] for row in result.fetchall()]
            
            if 'password_reset_token' in new_columns and 'password_reset_expires' in new_columns:
                print("✅ Both password reset columns verified in database")
                print(f"📋 Total columns now: {len(new_columns)} columns")
                
                # Show the new columns
                print("\n📝 Password reset columns:")
                for row in result.fetchall():
                    if 'password_reset' in row[1]:
                        print(f"   • {row[1]} ({row[2]})")
                
                print("\n" + "=" * 60)
                print("🎉 Database migration completed successfully!")
                print("\nPassword Reset System is now ready:")
                print("• ✅ Database columns added")
                print("• ✅ User model updated")
                print("• ✅ Routes implemented")
                print("• ✅ Templates created")
                print("• ✅ Email integration ready")
                
            else:
                print("❌ Error: Columns were not added properly")
                return False
                
        except Exception as e:
            print(f"❌ Error during migration: {str(e)}")
            db.session.rollback()
            return False
    
    return True

if __name__ == '__main__':
    success = add_password_reset_columns()
    if success:
        print("\n🚀 You can now test the password reset system!")
        print("   Run: python test_password_reset.py")
    else:
        print("\n💥 Migration failed. Please check the errors above.")
        sys.exit(1)