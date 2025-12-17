"""
Test script to verify the join code system
"""
from app import create_app, db
from app.models import ClassGroup, User

app = create_app()

def test_join_codes():
    with app.app_context():
        print("Testing Join Code System...\n")
        
        # Test 1: Check if join codes exist
        print("Test 1: Checking if join codes are set up...")
        class_groups = ClassGroup.query.all()
        
        if not class_groups:
            print("❌ No class groups found. Run setup_database() first.")
            return
        
        print(f"✅ Found {len(class_groups)} class group(s):")
        for group in class_groups:
            if hasattr(group, 'join_code') and group.join_code:
                print(f"   - {group.name}: {group.join_code}")
            else:
                print(f"   ❌ {group.name}: NO JOIN CODE")
        
        # Test 2: Test join code lookup
        print("\nTest 2: Testing join code lookup...")
        test_codes = ['CS100', 'CS200', 'IT300', 'INVALID']
        
        for code in test_codes:
            group = ClassGroup.query.filter_by(join_code=code).first()
            if group:
                print(f"   ✅ '{code}' -> Found: {group.name}")
            else:
                print(f"   ❌ '{code}' -> Not found (expected for INVALID)")
        
        # Test 3: Check uniqueness
        print("\nTest 3: Checking join code uniqueness...")
        all_codes = [g.join_code for g in class_groups if hasattr(g, 'join_code') and g.join_code]
        unique_codes = set(all_codes)
        
        if len(all_codes) == len(unique_codes):
            print(f"   ✅ All {len(all_codes)} join codes are unique")
        else:
            print(f"   ❌ Duplicate join codes found!")
            duplicates = [code for code in all_codes if all_codes.count(code) > 1]
            print(f"   Duplicates: {set(duplicates)}")
        
        # Test 4: Check case insensitivity
        print("\nTest 4: Testing case insensitivity...")
        test_case_codes = ['cs100', 'CS100', 'Cs100']
        for code in test_case_codes:
            group = ClassGroup.query.filter_by(join_code=code.upper()).first()
            if group:
                print(f"   ✅ '{code}' (normalized to '{code.upper()}') -> {group.name}")
        
        print("\n" + "="*50)
        print("✅ Join Code System Test Complete!")
        print("="*50)

if __name__ == '__main__':
    test_join_codes()
