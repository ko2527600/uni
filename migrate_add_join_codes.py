"""
Migration script to add join_code column to existing ClassGroup records
Run this ONCE after updating the models.py file
"""
from app import create_app, db
from app.models import ClassGroup

app = create_app()

def migrate_join_codes():
    with app.app_context():
        print("Starting migration to add join codes...")
        
        # Get all existing class groups
        class_groups = ClassGroup.query.all()
        
        if not class_groups:
            print("No class groups found. Database might be empty.")
            return
        
        # Predefined join codes for common classes
        join_code_mapping = {
            'Level 100 CS': 'CS100',
            'Level 200 CS': 'CS200',
            'Level 300 IT': 'IT300',
            'Level 100 IT': 'IT100',
            'Level 200 IT': 'IT200',
            'Level 300 CS': 'CS300',
        }
        
        updated_count = 0
        for group in class_groups:
            # Check if join_code already exists
            if hasattr(group, 'join_code') and group.join_code:
                print(f"✓ {group.name} already has join_code: {group.join_code}")
                continue
            
            # Try to get predefined code, otherwise generate one
            if group.name in join_code_mapping:
                join_code = join_code_mapping[group.name]
            else:
                # Generate a join code from the class name
                # Extract letters and numbers
                code_parts = ''.join(c for c in group.name if c.isalnum()).upper()
                join_code = code_parts[:10]  # Max 10 characters
            
            # Ensure uniqueness
            counter = 1
            original_code = join_code
            while ClassGroup.query.filter_by(join_code=join_code).first():
                join_code = f"{original_code}{counter}"
                counter += 1
            
            group.join_code = join_code
            updated_count += 1
            print(f"✓ Updated {group.name} with join_code: {join_code}")
        
        if updated_count > 0:
            db.session.commit()
            print(f"\n✅ Migration complete! Updated {updated_count} class group(s).")
        else:
            print("\n✅ All class groups already have join codes.")
        
        # Display all join codes
        print("\n📋 Current Class Join Codes:")
        all_groups = ClassGroup.query.all()
        for group in all_groups:
            print(f"   - {group.join_code} ({group.name})")

if __name__ == '__main__':
    migrate_join_codes()
