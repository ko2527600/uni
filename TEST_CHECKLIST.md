# ✅ Implementation Checklist - Unique Class Join Code System

## 📋 Changes Applied

### ✅ 1. Updated `app/models.py`
- [x] Added `join_code` column to `ClassGroup` model
- [x] Set as `unique=True` to prevent duplicates
- [x] Set as `nullable=False` to ensure all classes have codes
- [x] Max length: 10 characters

**Code Added:**
```python
join_code = db.Column(db.String(10), unique=True, nullable=False)
```

---

### ✅ 2. Updated `app/routes.py`
- [x] Removed `class_groups = ClassGroup.query.all()` from register route
- [x] Changed form field from `class_group_id` to `join_code`
- [x] Added validation: Search for class by `join_code`
- [x] Auto-assign both `class_group_id` AND `university_id`
- [x] Show error message: "❌ Invalid Class Code. Please ask your Rep."
- [x] Convert join_code to uppercase with `.strip().upper()`

**Key Logic:**
```python
join_code = request.form.get('join_code')
group = ClassGroup.query.filter_by(join_code=join_code.strip().upper()).first()

if not group:
    flash('❌ Invalid Class Code. Please ask your Rep.', 'error')
    return redirect(url_for('main.register'))

class_group_id = group.id
university_id = group.university_id
```

---

### ✅ 3. Updated `app/templates/register.html`
- [x] Removed `<select>` dropdown for class selection
- [x] Added text `<input>` for join_code
- [x] Placeholder: "Enter Class Code (e.g. CS100)"
- [x] Added helper text: "Ask your Class Rep for this code."
- [x] Auto-converts input to uppercase
- [x] Shows/hides based on role (only for Student/Rep)
- [x] Added JavaScript `toggleClassCode()` function

**UI Changes:**
```html
<div class="form-group" id="classCodeGroup">
    <label for="join_code">Class Code</label>
    <input type="text" id="join_code" name="join_code" 
           placeholder="Enter Class Code (e.g. CS100)" 
           style="text-transform: uppercase;">
    <small>Ask your Class Rep for this code.</small>
</div>
```

---

### ✅ 4. Updated `run.py`
- [x] Created `setup_database()` function
- [x] Auto-creates default classes on first run
- [x] Assigned specific join codes:
  - Level 100 CS → **CS100**
  - Level 200 CS → **CS200**
  - Level 300 IT → **IT300**
- [x] Prints available codes to terminal
- [x] Checks if database already initialized

**Seeder Data:**
```python
classes = [
    {'name': 'Level 100 CS', 'code': 'CS-100', 'join_code': 'CS100'},
    {'name': 'Level 200 CS', 'code': 'CS-200', 'join_code': 'CS200'},
    {'name': 'Level 300 IT', 'code': 'IT-300', 'join_code': 'IT300'}
]
```

---

## 🧪 Testing Instructions

### Test 1: Fresh Installation
```bash
# Delete old database
rm instance/uniportal.db

# Run application
python run.py
```

**Expected Output:**
```
Setting up database with default data...
✅ Database setup complete!

📋 Available Class Join Codes:
   - CS100 (Level 100 CS)
   - CS200 (Level 200 CS)
   - IT300 (Level 300 IT)

Use these codes when registering as Student or Rep.
```

---

### Test 2: Register as Student with Valid Code
1. Go to: http://localhost:5000/register
2. Fill form:
   - Username: `test_student`
   - Email: `student@test.com`
   - Password: `password123`
   - Role: `Student`
   - Class Code: `CS100` ✅
3. Click "Sign Up"

**Expected Result:**
- ✅ Account created successfully
- ✅ Redirected to verification page
- ✅ User assigned to "Level 100 CS" class
- ✅ User assigned to "University of Ghana"

---

### Test 3: Register with Invalid Code
1. Go to: http://localhost:5000/register
2. Fill form:
   - Username: `test_student2`
   - Email: `student2@test.com`
   - Password: `password123`
   - Role: `Student`
   - Class Code: `INVALID999` ❌
3. Click "Sign Up"

**Expected Result:**
- ❌ Error message: "❌ Invalid Class Code. Please ask your Rep."
- ❌ Stays on registration page
- ❌ Account NOT created

---

### Test 4: Register as Lecturer (No Code Required)
1. Go to: http://localhost:5000/register
2. Fill form:
   - Username: `prof_smith`
   - Email: `prof@test.com`
   - Password: `password123`
   - Role: `Lecturer`
   - Class Code: (field hidden) ✅
3. Click "Sign Up"

**Expected Result:**
- ✅ Account created successfully
- ✅ No class code required
- ✅ class_group_id = NULL
- ✅ university_id = NULL

---

### Test 5: Case Insensitivity
Try entering codes in different cases:
- `cs100` → Should work ✅
- `CS100` → Should work ✅
- `Cs100` → Should work ✅
- `cS100` → Should work ✅

All should be converted to uppercase and matched correctly.

---

### Test 6: Duplicate Join Codes (Database Constraint)
Try creating two classes with the same join_code:

```python
from app import create_app, db
from app.models import ClassGroup

app = create_app()
with app.app_context():
    # This should FAIL due to unique constraint
    duplicate = ClassGroup(
        name='Duplicate Class',
        code='DUP-100',
        join_code='CS100',  # Already exists!
        university_id=1
    )
    db.session.add(duplicate)
    db.session.commit()  # Should raise IntegrityError
```

**Expected Result:**
- ❌ Database error: UNIQUE constraint failed
- ✅ Prevents duplicate join codes

---

## 🎯 Success Criteria

All tests should pass:
- [x] Database schema updated with join_code column
- [x] Registration form shows text input instead of dropdown
- [x] Valid codes allow registration
- [x] Invalid codes show error message
- [x] Lecturers don't need codes
- [x] Codes are case-insensitive
- [x] Duplicate codes are prevented
- [x] Default classes created with CS100, CS200, IT300

---

## 📊 Before vs After

### BEFORE (Dropdown System)
```html
<select name="class_group_id">
  <option value="1">Level 100 CS</option>
  <option value="2">Level 200 CS</option>
  <option value="3">Level 300 IT</option>
</select>
```
❌ Students see all classes  
❌ Exposes internal IDs  
❌ Hard to share with others  

### AFTER (Join Code System)
```html
<input type="text" name="join_code" 
       placeholder="Enter Class Code (e.g. CS100)">
```
✅ Students only see their class  
✅ Simple memorable codes  
✅ Easy to share: "Use code CS100"  
✅ Rep-controlled access  

---

## 🚀 Ready to Deploy!

All 4 files have been updated successfully:
1. ✅ `app/models.py` - Database schema
2. ✅ `app/routes.py` - Registration logic
3. ✅ `app/templates/register.html` - User interface
4. ✅ `run.py` - Database seeder

**Next Steps:**
1. Delete old database: `rm instance/uniportal.db`
2. Run application: `python run.py`
3. Test registration with codes: CS100, CS200, IT300
4. Verify error handling with invalid codes

🎉 **Implementation Complete!**
