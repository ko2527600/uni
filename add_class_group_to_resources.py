"""
Migration script to add class_group_id column to resources table
Run this once to update your existing database
"""

from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        # Check if column already exists
        result = db.session.execute(text("PRAGMA table_info(resources)"))
        columns = [row[1] for row in result]
        
        if 'class_group_id' not in columns:
            print("Adding class_group_id column to resources table...")
            db.session.execute(text(
                "ALTER TABLE resources ADD COLUMN class_group_id INTEGER"
            ))
            db.session.commit()
            print("✅ Column added successfully!")
            
            # Update existing resources to link them to classes based on their course
            print("\nUpdating existing resources with class_group_id...")
            result = db.session.execute(text("""
                UPDATE resources 
                SET class_group_id = (
                    SELECT class_group_id 
                    FROM courses 
                    WHERE courses.id = resources.course_id
                )
                WHERE course_id IS NOT NULL
            """))
            db.session.commit()
            print(f"✅ Updated {result.rowcount} resources with class_group_id!")
        else:
            print("✅ Column class_group_id already exists!")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        db.session.rollback()
