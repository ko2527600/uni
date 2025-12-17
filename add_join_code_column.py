"""
Add join_code column to class_groups table
"""
import sqlite3

# Connect to database
conn = sqlite3.connect('instance/uniportal.db')
cursor = conn.cursor()

try:
    print("Adding join_code column to class_groups table...")
    
    # Add the column
    cursor.execute("ALTER TABLE class_groups ADD COLUMN join_code VARCHAR(10)")
    
    # Get existing class groups
    cursor.execute("SELECT id, name FROM class_groups")
    groups = cursor.fetchall()
    
    # Assign join codes
    join_code_mapping = {
        'Level 100 CS': 'CS100',
        'Level 200 CS': 'CS200',
        'Level 300 IT': 'IT300',
        'Level 100 IT': 'IT100',
        'Level 200 IT': 'IT200',
        'Level 300 CS': 'CS300',
    }
    
    for group_id, name in groups:
        if name in join_code_mapping:
            join_code = join_code_mapping[name]
        else:
            # Generate from name
            join_code = ''.join(c for c in name if c.isalnum()).upper()[:10]
        
        cursor.execute("UPDATE class_groups SET join_code = ? WHERE id = ?", (join_code, group_id))
        print(f"✅ {name} -> {join_code}")
    
    conn.commit()
    print("\n✅ Migration complete!")
    
    # Verify
    print("\n📋 Current Join Codes:")
    cursor.execute("SELECT name, join_code FROM class_groups")
    for name, code in cursor.fetchall():
        print(f"   - {code} ({name})")

except sqlite3.Error as e:
    if "duplicate column name" in str(e).lower():
        print("✅ Column already exists!")
    else:
        print(f"❌ Error: {e}")
        conn.rollback()

finally:
    conn.close()
