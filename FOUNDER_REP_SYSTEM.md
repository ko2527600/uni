# 🎯 Founder Rep Registration System

## 📋 Overview
Updated registration logic to allow **Founder Reps** to sign up without a class code. They can then create their own classes and generate codes for students and lecturers.

---

## ✅ What Changed

### 1. **Registration Logic** (`app/routes.py`)

#### New Logic Flow:

**Scenario 1: Join Code Provided**
```python
if join_code is provided:
    - Validate the code
    - If valid: Assign to that class
    - Role becomes 'Student' (even if they selected Rep)
    - Reason: They're joining an existing class
```

**Scenario 2: No Code + Rep Selected**
```python
if NO join_code AND role == 'Rep':
    - Role becomes 'Rep' (Founder Rep)
    - No class assigned yet
    - They will create their own class after verification
```

**Scenario 3: No Code + Student Selected**
```python
if NO join_code AND role == 'Student':
    - Show error: "Students must enter a class code to join"
    - Students cannot be founders
```

**Scenario 4: Lecturer**
```python
if role == 'Lecturer':
    - Class code field hidden
    - No code needed
    - They use /claim_class instead
```

---

### 2. **UI Updates** (`app/templates/register.html`)

#### Class Code Field Changes:

**Before:**
```html
<input required placeholder="Enter Class Code (e.g. CS100)">
<small>Ask your Class Rep for this code.</small>
```

**After:**
```html
<input placeholder="Enter Code (Students) OR Leave Empty (New Reps)">
<small id="codeHintStudent">Students: Ask your Class Rep for this code.</small>
<small id="codeHintRep">Reps: Leave empty to create your own class, or enter a code to join existing class.</small>
```

**Dynamic Hints:**
- **Student selected**: Shows "Ask your Class Rep" + field is REQUIRED
- **Rep selected**: Shows "Leave empty to create" + field is OPTIONAL
- **Lecturer selected**: Field hidden completely

---

## 🔄 Registration Workflows

### Workflow 1: Founder Rep (No Code)
```
1. Go to /register
2. Fill: username, email, password
3. Select role: "Class Representative"
4. Leave class code EMPTY
5. Click "Sign Up"
6. Verify email
7. Login → Rep Dashboard
8. Create class → Get codes
9. Share codes with students/lecturer
```

### Workflow 2: Student Joining Class
```
1. Go to /register
2. Fill: username, email, password
3. Select role: "Student"
4. Enter 6-character class code (REQUIRED)
5. Click "Sign Up"
6. Verify email
7. Login → Student Dashboard
```

### Workflow 3: Rep Joining Existing Class
```
1. Go to /register
2. Fill: username, email, password
3. Select role: "Class Representative"
4. Enter 6-character class code (OPTIONAL)
5. Click "Sign Up"
6. Role becomes "Student" (joined existing class)
7. Verify email
8. Login → Student Dashboard
```

### Workflow 4: Lecturer Claiming Class
```
1. Go to /claim_class
2. Enter 8-character lecturer code
3. Create account or login
4. Assigned as lecturer
5. Login → Admin Dashboard
```

---

## 🎯 Role Assignment Logic

| Selected Role | Code Provided? | Final Role | Class Assigned? |
|--------------|----------------|------------|-----------------|
| Student      | ✅ Yes         | Student    | ✅ Yes          |
| Student      | ❌ No          | ERROR      | ❌ No           |
| Rep          | ✅ Yes         | Student    | ✅ Yes          |
| Rep          | ❌ No          | Rep        | ❌ No           |
| Lecturer     | N/A            | (use /claim_class) | N/A |

**Key Point:** If a Rep provides a code, they become a Student in that class. Only Reps without codes become actual Reps.

---

## 🔒 Validation Rules

### Students:
- ✅ MUST provide a class code
- ❌ Cannot register without code
- ✅ Code must be valid (6 characters)
- ✅ Assigned to class immediately

### Reps:
- ✅ Can provide code (becomes Student)
- ✅ Can leave empty (becomes Founder Rep)
- ✅ If empty, no class assigned yet
- ✅ Must create class after login

### Lecturers:
- ✅ Use separate /claim_class page
- ✅ Need 8-character lecturer code
- ✅ Can create account during claim
- ✅ Assigned to class automatically

---

## 🧪 Testing Scenarios

### Test 1: Founder Rep Registration
```
Input:
- Username: founder_rep
- Email: rep@test.com
- Password: password123
- Role: Class Representative
- Class Code: [EMPTY]

Expected:
✅ Account created
✅ Role = 'Rep'
✅ class_group_id = NULL
✅ university_id = NULL
✅ Redirected to verification
✅ After login → Rep Dashboard
✅ Can create classes
```

### Test 2: Student with Code
```
Input:
- Username: student1
- Email: student@test.com
- Password: password123
- Role: Student
- Class Code: CS100

Expected:
✅ Account created
✅ Role = 'Student'
✅ class_group_id = 1 (CS100 class)
✅ university_id = 1
✅ Redirected to verification
✅ After login → Student Dashboard
```

### Test 3: Student without Code
```
Input:
- Username: student2
- Email: student2@test.com
- Password: password123
- Role: Student
- Class Code: [EMPTY]

Expected:
❌ Error: "Students must enter a class code to join"
❌ Account NOT created
❌ Stays on registration page
```

### Test 4: Rep with Code (Joins as Student)
```
Input:
- Username: rep_student
- Email: repstudent@test.com
- Password: password123
- Role: Class Representative
- Class Code: CS100

Expected:
✅ Account created
✅ Role = 'Student' (NOT Rep!)
✅ class_group_id = 1 (CS100 class)
✅ university_id = 1
✅ After login → Student Dashboard (NOT Rep Dashboard)
```

### Test 5: Invalid Code
```
Input:
- Username: test_user
- Email: test@test.com
- Password: password123
- Role: Student
- Class Code: INVALID

Expected:
❌ Error: "Invalid Class Code. Please check and try again"
❌ Account NOT created
❌ Stays on registration page
```

---

## 📝 Code Changes Summary

### `app/routes.py` - register() function:
```python
# NEW LOGIC:
if join_code provided:
    validate and assign to class
    actual_role = 'Student' (if Student or Rep selected)
elif role == 'Rep' and no code:
    actual_role = 'Rep' (Founder)
    no class assignment
elif role == 'Student' and no code:
    show error
```

### `app/templates/register.html`:
```html
<!-- Class code field now OPTIONAL for Reps -->
<input type="text" name="join_code" 
       placeholder="Enter Code (Students) OR Leave Empty (New Reps)">

<!-- Dynamic hints based on role -->
<small id="codeHintStudent">Students: Ask your Class Rep...</small>
<small id="codeHintRep">Reps: Leave empty to create...</small>
```

### JavaScript:
```javascript
// Updated toggleClassCode() function
if (role === 'Student') {
    joinCodeInput.required = true;  // REQUIRED
} else if (role === 'Rep') {
    joinCodeInput.required = false; // OPTIONAL
}
```

---

## 🎉 Benefits

1. **Self-Service**: Reps can start without admin intervention
2. **Flexible**: Reps can either create or join classes
3. **Clear**: Different hints for Students vs Reps
4. **Secure**: Students still need codes to join
5. **Scalable**: Unlimited Reps can create classes
6. **Simple**: One registration form for all scenarios

---

## 🚀 Complete User Journey

### Day 1: Founder Rep
```
1. Rep registers (no code)
2. Verifies email
3. Logs in → Rep Dashboard
4. Creates "Level 100 CS" class
5. Gets codes: A3X9K2 (students) + L8M4P9Q1 (lecturer)
```

### Day 2: Students Join
```
1. Rep shares A3X9K2 in WhatsApp group
2. Students register with code A3X9K2
3. All assigned to "Level 100 CS"
4. Can upload assignments
```

### Day 3: Lecturer Claims
```
1. Rep gives L8M4P9Q1 to lecturer
2. Lecturer goes to /claim_class
3. Enters code + creates account
4. Becomes lecturer for "Level 100 CS"
5. Can grade assignments
```

---

## 🔧 Edge Cases Handled

1. ✅ Rep tries to join with invalid code → Error shown
2. ✅ Student tries to register without code → Error shown
3. ✅ Rep leaves code empty → Becomes Founder Rep
4. ✅ Rep enters valid code → Becomes Student in that class
5. ✅ Lecturer tries to use register page → Redirected to /claim_class
6. ✅ Case insensitive codes (CS100 = cs100)
7. ✅ Whitespace trimmed from codes

---

## 📂 Files Modified

1. ✅ `app/routes.py` - Updated register() logic
2. ✅ `app/templates/register.html` - Made code optional, added dynamic hints

---

**Status:** ✅ **COMPLETE**  
**Last Updated:** November 27, 2025  
**Feature:** Founder Rep Registration  
**Version:** 2.1.0
