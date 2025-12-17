# UniPortal - Setup Instructions

## 🚀 Quick Start (New Installation)

If you're setting up UniPortal for the first time:

```bash
# 1. Delete old database (if exists)
rm instance/uniportal.db

# 2. Run the application (will auto-setup database)
python run.py
```

The database will be automatically initialized with:
- University of Ghana
- 3 default classes with join codes:
  - **CS100** → Level 100 CS
  - **CS200** → Level 200 CS
  - **IT300** → Level 300 IT

## 🔄 Migrating Existing Database

If you already have a database with data:

```bash
# Option 1: Run migration script (attempts to preserve data)
python migrate_add_join_codes.py

# Option 2: Fresh start (deletes all data)
python clear_db.py
python run.py
```

## 📝 How Students Register Now

1. Go to registration page
2. Fill in username, email, password
3. Select role (Student/Rep/Lecturer)
4. **Enter Class Code** (e.g., CS100)
   - Students and Reps MUST enter a valid class code
   - Lecturers don't need a class code
5. Verify email with 6-digit code
6. Login and access dashboard

## 🔑 Testing the System

### Register as Student:
- Username: `john_doe`
- Email: `john@example.com`
- Password: `password123`
- Role: `Student`
- **Class Code: `CS100`** ← Enter this!

### Register as Class Rep:
- Username: `jane_rep`
- Email: `jane@example.com`
- Password: `password123`
- Role: `Class Representative`
- **Class Code: `CS200`** ← Enter this!

### Register as Lecturer:
- Username: `prof_smith`
- Email: `prof@example.com`
- Password: `password123`
- Role: `Lecturer`
- Class Code: (not required)

## ✅ What Changed

### 1. Database Model (`app/models.py`)
- Added `join_code` column to `ClassGroup` model
- Join codes are unique (no duplicates allowed)

### 2. Registration Logic (`app/routes.py`)
- Removed class dropdown selection
- Added join code validation
- Auto-assigns university_id based on class code
- Shows error if invalid code entered

### 3. Registration UI (`app/templates/register.html`)
- Replaced dropdown with text input
- Shows/hides class code field based on role
- Converts input to uppercase automatically
- Displays helper text: "Ask your Class Rep for this code"

### 4. Database Seeder (`run.py`)
- Auto-creates default classes with join codes on first run
- Displays available codes in terminal

## 🎯 Benefits

✅ **No Data Conflicts** - Each class has a unique code  
✅ **Better Security** - Students can't see all available classes  
✅ **Easier Onboarding** - Just share a simple code like "CS100"  
✅ **Scalable** - Works for any number of classes  
✅ **Rep-Controlled** - Class Reps manage who joins their class

## 🛠️ Troubleshooting

### Error: "Invalid Class Code"
- Check if you typed the code correctly (case-insensitive)
- Ask your Class Rep for the correct code
- Verify the class exists in the database

### Error: Database schema mismatch
```bash
# Solution: Reset database
rm instance/uniportal.db
python run.py
```

### Need to add more classes?
Use the admin panel or run:
```python
from app import create_app, db
from app.models import ClassGroup

app = create_app()
with app.app_context():
    new_class = ClassGroup(
        name='Level 400 CS',
        code='CS-400',
        join_code='CS400',
        university_id=1
    )
    db.session.add(new_class)
    db.session.commit()
```

## 📞 Support

If you encounter issues:
1. Check the terminal for error messages
2. Verify database exists: `ls instance/`
3. Try fresh installation (delete DB and restart)
4. Check that all 4 files were updated correctly
