from app import create_app, db
from app.models import User, ClassGroup

app = create_app()

with app.app_context():
    users = User.query.all()
    
    if users:
        print("\n" + "="*100)
        print("ALL REGISTERED USERS")
        print("="*100)
        print(f"{'ID':<5} {'Username':<20} {'Email':<30} {'Role':<12} {'Verified':<10} {'Class':<20}")
        print("-"*100)
        
        for user in users:
            verified = "✓ Yes" if user.is_verified else "✗ No"
            
            # Get class name if user is in a class
            class_name = "No Class"
            if user.class_group_id:
                class_group = ClassGroup.query.get(user.class_group_id)
                if class_group:
                    class_name = class_group.name
            
            print(f"{user.id:<5} {user.username:<20} {user.email:<30} {user.role:<12} {verified:<10} {class_name:<20}")
        
        print("-"*100)
        print(f"\nTotal Users: {len(users)}")
        
        # Show breakdown by role
        students = [u for u in users if u.role == 'Student']
        reps = [u for u in users if u.role == 'Rep']
        lecturers = [u for u in users if u.role == 'Lecturer']
        admins = [u for u in users if u.role == 'Admin']
        
        print(f"  Students: {len(students)}")
        print(f"  Reps: {len(reps)}")
        print(f"  Lecturers: {len(lecturers)}")
        print(f"  Admins: {len(admins)}")
        
        # Show verified vs unverified
        verified_users = [u for u in users if u.is_verified]
        unverified_users = [u for u in users if not u.is_verified]
        print(f"\n  Verified: {len(verified_users)}")
        print(f"  Unverified: {len(unverified_users)}")
        
        print("="*100 + "\n")
    else:
        print("\n" + "="*100)
        print("No users found in the database.")
        print("Register your first user at: http://localhost:5000/register")
        print("="*100 + "\n")
