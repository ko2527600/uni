# 🎓 Rep-Led Class Creation System

## 📋 Overview
The system has been updated to a **Rep-led economy** where Class Representatives create classes and invite both students and lecturers using unique codes.

---

## ✅ What Changed

### 1. **Database Model Updates** (`app/models.py`)

#### ClassGroup Model - New Fields:
```python
join_code = db.Column(db.String(10), unique=True, nullable=False)      # For students (6 chars)
lecturer_code = db.Column(db.String(10), unique=True, nullable=False)  # For lecturers (8 chars)
lecturer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Assigned lecturer
created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)   # Rep who created it
```

**Relationships:**
- `lecturer` - The User who claimed the class as lecturer
- `creator` - The Rep who created the class

---

### 2. **New Routes** (`app/routes.py`)

#### `/create_class` (POST) - Rep Only
- Allows Reps to create new classes
- Generates TWO unique codes:
  - **join_code** (6 characters) - For students
  - **lecturer_code** (8 characters) - For lecturers
- Flash message shows both codes to the Rep
- Assigns the Rep as `created_by`

#### `/claim_class` (GET/POST) - Lecturers
- Lecturers enter their 8-character lecturer code
- Two scenarios:
  1. **Logged in user**: Assigns them as lecturer for that class
  2. **New user**: Creates lecturer account + assigns to class
- Validates that class doesn't already have a lecturer
- Redirects to verification if new account created

---

### 3. **UI Updates**

#### `rep_dashboard.html`
**New Section: "Create New Class"**
- Form with class name and code inputs
- Generates both student and lecturer codes
- Shows all classes created by the Rep
- Displays both codes with copy-to-clipboard functionality
- Shows lecturer status (assigned or waiting)

**Features:**
```html
- Click codes to copy them
- Green badge for student code
- Orange badge for lecturer code
- Shows if lecturer has claimed the class
```

#### `claim_class.html` (NEW FILE)
**Lecturer Claiming Page**
- Enter 8-character lecturer code
- Optional: Create new account (username, email, password)
- Toggle between "claim only" and "create + claim"
- Beautiful gradient UI matching the app theme
- Info box explaining the process

#### `register.html`
**New Link Added:**
```
👨‍🏫 Are you a Lecturer? Claim your class here
```
- Links to `/claim_class`
- Positioned below the login link

---

### 4. **Database Seeder Updates** (`run.py`)

Default classes now include lecturer codes:
```python
Level 100 CS:
  Student Code: CS100
  Lecturer Code: LEC100CS

Level 200 CS:
  Student Code: CS200
  Lecturer Code: LEC200CS

Level 300 IT:
  Student Code: IT300
  Lecturer Code: LEC300IT
```

---

## 🔄 New Workflow

### Step 1: Rep Creates Class
1. Rep logs in and goes to dashboard
2. Fills "Create New Class" form
3. System generates:
   - `join_code` (e.g., "A3X9K2")
   - `lecturer_code` (e.g., "L8M4P9Q1")
4. Rep sees both codes displayed

### Step 2: Rep Shares Codes
- **Student Code** → Share with students (WhatsApp, email, etc.)
- **Lecturer Code** → Give to the lecturer privately

### Step 3: Students Join
1. Students go to `/register`
2. Select "Student" role
3. Enter the 6-character student code
4. Account created and assigned to class

### Step 4: Lecturer Claims Class
1. Lecturer goes to `/claim_class` (link on register page)
2. Enters 8-character lecturer code
3. Either:
   - **Has account**: Logs in first, then claims
   - **No account**: Fills form to create account + claim
4. Becomes the lecturer for that class
5. Gets Admin/Lecturer dashboard access

---

## 🎯 Key Features

### For Reps:
✅ Create unlimited classes  
✅ Generate unique codes automatically  
✅ View all created classes  
✅ Copy codes with one click  
✅ See lecturer assignment status  

### For Lecturers:
✅ Simple claim process with code  
✅ Can create account during claim  
✅ Or claim if already registered  
✅ Automatic role assignment  
✅ Immediate dashboard access  

### For Students:
✅ Same registration flow (unchanged)  
✅ Use 6-character student code  
✅ Join class automatically  

---

## 🔒 Security Features

1. **Unique Codes**: Both codes are unique across all classes
2. **One Lecturer Per Class**: System prevents multiple lecturers claiming same class
3. **Code Validation**: Invalid codes show clear error messages
4. **Rep Ownership**: Only the Rep who created a class sees its codes
5. **Case Insensitive**: Codes work in any case (ABC123 = abc123)

---

## 📝 Code Generation Logic

### Student Code (6 characters):
```python
join_code = random uppercase letters + digits (e.g., "A3X9K2")
```

### Lecturer Code (8 characters):
```python
lecturer_code = random uppercase letters + digits (e.g., "L8M4P9Q1")
```

Both checked for uniqueness before saving.

---

## 🧪 Testing Instructions

### Test 1: Rep Creates Class
1. Login as Rep
2. Go to dashboard
3. Fill "Create New Class" form:
   - Class Name: "Test Class"
   - Class Code: "TEST-100"
4. Click "Create Class & Generate Codes"
5. **Expected**: See both codes displayed

### Test 2: Student Joins with Code
1. Go to `/register`
2. Fill form, select "Student"
3. Enter the 6-character student code
4. **Expected**: Account created, assigned to class

### Test 3: Lecturer Claims (New Account)
1. Go to `/claim_class`
2. Enter 8-character lecturer code
3. Fill account creation form
4. **Expected**: Account created, assigned as lecturer, redirected to verify

### Test 4: Lecturer Claims (Existing Account)
1. Login as any user
2. Go to `/claim_class`
3. Enter 8-character lecturer code
4. **Expected**: Role changed to Lecturer, assigned to class

### Test 5: Duplicate Lecturer Attempt
1. Try to claim a class that already has a lecturer
2. **Expected**: Error message "Class already has a lecturer"

---

## 🚀 How to Start

### Fresh Installation:
```bash
# Delete old database
rm instance/uniportal.db

# Run the app
python run.py
```

**You'll see:**
```
✅ Database setup complete!

📋 Available Class Codes:
   Level 100 CS:
      Student Code: CS100
      Lecturer Code: LEC100CS
   ...
```

### Test the System:
1. Register as Rep with code CS100
2. Login and create a new class
3. Use generated codes to test student/lecturer registration

---

## 📂 Files Modified

1. ✅ `app/models.py` - Added lecturer_code, lecturer_id, created_by
2. ✅ `app/routes.py` - Added /create_class and /claim_class routes
3. ✅ `app/templates/rep_dashboard.html` - Added create class form
4. ✅ `app/templates/claim_class.html` - NEW FILE for lecturer claiming
5. ✅ `app/templates/register.html` - Added lecturer claim link
6. ✅ `run.py` - Updated seeder with lecturer codes

---

## 🎉 Benefits of Rep-Led System

1. **Decentralized**: Reps control their own classes
2. **Scalable**: No admin bottleneck for class creation
3. **Flexible**: Each class has its own codes
4. **Secure**: Lecturer codes are separate from student codes
5. **Trackable**: System knows who created each class
6. **Simple**: Clear workflow for all user types

---

## 🔧 Future Enhancements

Potential improvements:
- [ ] Code expiration dates
- [ ] Regenerate codes if compromised
- [ ] Bulk student import via CSV
- [ ] QR codes for easy sharing
- [ ] Analytics on code usage
- [ ] Multiple lecturers per class
- [ ] Transfer class ownership

---

**Status:** ✅ **COMPLETE & READY**  
**Last Updated:** November 27, 2025  
**System:** Rep-Led Class Creation  
**Version:** 2.0.0
