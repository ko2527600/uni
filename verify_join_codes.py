"""Quick verification of join code system"""
import sqlite3

# Connect to database
conn = sqlite3.connect('instance/uniportal.db')
cursor = conn.cursor()

print("="*60)
print("JOIN CODE SYSTEM VERIFICATION")
print("="*60)

# Check if join_code column exists
try:
    cursor.execute("PRAGMA table_info(class_groups)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    
    print("\n1. Database Schema Check:")
    if 'join_code' in column_names:
        print("   ✅ join_code column EXISTS in class_groups table")
    else:
        print("   ❌ join_code column MISSING from class_groups table")
        print("   Run: python migrate_add_join_codes.py")
    
    print(f"\n   Columns in class_groups: {', '.join(column_names)}")
    
    # Check if join codes are populated
    print("\n2. Join Code Data Check:")
    cursor.execute("SELECT id, name, code, join_code FROM class_groups")
    groups = cursor.fetchall()
    
    if not groups:
        print("   ⚠️  No class groups found in database")
        print("   Run: python run.py (will auto-create)")
    else:
        print(f"   Found {len(groups)} class group(s):")
        for group in groups:
            id, name, code, join_code = group
            if join_code:
                print(f"   ✅ {name} ({code}) -> JOIN CODE: {join_code}")
            else:
                print(f"   ❌ {name} ({code}) -> NO JOIN CODE")
    
    # Check uniqueness
    if groups:
        print("\n3. Uniqueness Check:")
        join_codes = [g[3] for g in groups if g[3]]
        if len(join_codes) == len(set(join_codes)):
            print(f"   ✅ All {len(join_codes)} join codes are unique")
        else:
            print("   ❌ Duplicate join codes found!")
    
    # Test lookup
    print("\n4. Lookup Test:")
    test_codes = ['CS100', 'CS200', 'IT300']
    for test_code in test_codes:
        cursor.execute("SELECT name FROM class_groups WHERE join_code = ?", (test_code,))
        result = cursor.fetchone()
        if result:
            print(f"   ✅ '{test_code}' -> {result[0]}")
        else:
            print(f"   ⚠️  '{test_code}' -> Not found")

except sqlite3.Error as e:
    print(f"   ❌ Database error: {e}")

finally:
    conn.close()

print("\n" + "="*60)
print("VERIFICATION COMPLETE")
print("="*60)
