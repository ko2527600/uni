# 🎓 UniPortal - Join Code System Implementation

## Overview
This document explains the new **Unique Class Join Code** system that replaces the dropdown class selection with a secure code-based registration.

---

## ✅ What Changed?

### 1. **Database Model** (`app/models.py`)
- Added `join_code` column to `ClassGroup` model
- Properties:
  - Type: `String(10)`
  - Unique: `True` (no two classes can share the same code)
  - Required: `nullable=False`

```python
join_code = db.Column(db.String(10), unique=True, nullable=False)
```

### 2. **Registration Logic** (`app/routes.py`)
- Removed class dropdown fetching
- Added join code validation
- Process:
  1. User enters join code (e.g., "CS100")
  2. System searches: `ClassGroup.query.filter_by(join_code=code).first()`
  3. If found: Assigns user to `class_group_id` AND `university_id`
  4. If not found: Shows error "❌ Invalid Class Code. Please ask your Rep."

### 3. **Registration UI** (`app/templates/register.html`)
- Removed `<select>` dropdown
- Added text input field:
  ```html
  <input type="text" name="join_code" placeholder="Enter Class Code (e.g. CS100)">
  ```
- Features:
  - Auto-uppercase transformation
  - Only visible for Students and Reps
  - Hidden for Lecturers
  - Helpful hint: "Ask your Class Rep for this code"

### 4. **Database Seeder** (`run.py`)
- Pre-configured join codes for testing:
  - **CS100** → Level 100 CS
  - **CS200** → Level 200 CS
  - **IT300** → Level 300 IT

---

## 🚀 How to Use

### For New Installations:
1. Delete old database: `rm instance/uniportal.db`
2. Run the app: `python run.py`
3. Database will auto-initialize with join codes

### For Existing Databases:
1. Run migration script:
   ```bash
   python migrate_add_join_codes.py
   ```
2. This adds join codes to existing classes

### Testing the System:
```bash
python test_join_codes.py
```

---

## 📝 Registration Flow

### Student/Rep Registration:
1. Enter username, email, password
2. Select role: "Student" or "Class Representative"
3. **Class Code field appears**
4. Enter join code (e.g., "CS100")
5. System validates code
6. If valid: Account created ✅
7. If invalid: Error message ❌

### Lecturer Registration:
1. Enter username, email, password
2. Select role: "Lecturer"
3. **No class code needed** (field hidden)
4. Account created directly

---

## 🔒 Security Benefits

1. **No Class Enumeration**: Students can't see all available classes
2. **Controlled Access**: Only students with the code can join
3. **Rep Distribution**: Class Reps control who gets the code
4. **Unique Codes**: Each class has a distinct identifier
5. **Case Insensitive**: "cs100", "CS100", "Cs100" all work

---

## 🛠️ Available Scripts

### `migrate_add_join_codes.py`
- Adds join codes to existing database
- Handles uniqueness automatically
- Safe to run multiple times

### `test_join_codes.py`
- Verifies join code setup
- Tests lookup functionality
- Checks uniqueness
- Validates case insensitivity

---

## 📋 Default Join Codes

| Class Name      | Join Code | University        |
|----------------|-----------|-------------------|
| Level 100 CS   | CS100     | University of Ghana |
| Level 200 CS   | CS200     | University of Ghana |
| Level 300 IT   | IT300     | University of Ghana |

---

## 🎯 Testing Instructions

1. **Start the application:**
   ```bash
   python run.py
   ```

2. **Register as a Student:**
   - Go to `/register`
   - Fill in details
   - Select "Student"
   - Enter code: **CS100**
   - Should succeed ✅

3. **Test invalid code:**
   - Try code: **INVALID**
   - Should show error: "❌ Invalid Class Code. Please ask your Rep."

4. **Register as Lecturer:**
   - Select "Lecturer"
   - Class code field should hide
   - Registration should work without code

---

## 🔧 Troubleshooting

### Error: "column class_groups.join_code does not exist"
**Solution:** Run migration script:
```bash
python migrate_add_join_codes.py
```

### Error: "UNIQUE constraint failed"
**Solution:** Join codes must be unique. Check existing codes:
```bash
python test_join_codes.py
```

### Class code field not showing
**Solution:** Check JavaScript console. Ensure `toggleClassCode()` function is working.

---

## 📞 Support

For issues or questions about the join code system:
1. Check this README
2. Run test script: `python test_join_codes.py`
3. Verify database: Check `ClassGroup` table has `join_code` column

---

## ✨ Future Enhancements

Potential improvements:
- [ ] Admin panel to generate/manage join codes
- [ ] Expiring join codes (time-limited)
- [ ] Usage tracking (how many students used each code)
- [ ] QR code generation for easy sharing
- [ ] Bulk code generation for multiple classes

---

**Last Updated:** November 27, 2025
**Version:** 1.0.0
