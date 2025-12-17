from app import create_app, db
from app.models import User, University

app = create_app()

with app.app_context():
    # Create tables
    db.create_all()
    
    # Check if users already exist
    if User.query.first() is None:
        # Create a university
        uni = University(name="Demo University", domain="demo.edu")
        db.session.add(uni)
        db.session.commit()
        
        # Create admin user
        admin = User(username="admin", email="admin@demo.edu", role="Admin", university_id=uni.id, is_verified=True)
        admin.set_password("admin123")
        db.session.add(admin)
        
        # Create student user
        student = User(username="student", email="student@demo.edu", role="Student", university_id=uni.id, is_verified=True)
        student.set_password("student123")
        db.session.add(student)
        
        # Create rep user
        rep = User(username="rep", email="rep@demo.edu", role="Rep", university_id=uni.id, is_verified=True)
        rep.set_password("rep123")
        db.session.add(rep)
        
        db.session.commit()
        
        print("Database initialized successfully!")
        print("\nDefault login credentials:")
        print("-" * 40)
        print("Admin:")
        print("  Email: admin@demo.edu")
        print("  Password: admin123")
        print("\nStudent:")
        print("  Email: student@demo.edu")
        print("  Password: student123")
        print("\nClass Rep:")
        print("  Email: rep@demo.edu")
        print("  Password: rep123")
        print("-" * 40)
    else:
        print("Database already has users. Skipping initialization.")
