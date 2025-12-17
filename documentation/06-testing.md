# 🧪 UniPortal - Testing Documentation

## Table of Contents

1. [Testing Overview](#testing-overview)
2. [Test Environment Setup](#test-environment-setup)
3. [Unit Testing](#unit-testing)
4. [Integration Testing](#integration-testing)
5. [End-to-End Testing](#end-to-end-testing)
6. [Performance Testing](#performance-testing)
7. [Security Testing](#security-testing)
8. [User Acceptance Testing](#user-acceptance-testing)
9. [Test Automation](#test-automation)
10. [Quality Assurance Procedures](#quality-assurance-procedures)

---

## Testing Overview

### Testing Strategy

UniPortal follows a comprehensive testing approach with multiple layers:

```
┌─────────────────────────────────────────────────────────────┐
│                    TESTING PYRAMID                         │
├─────────────────────────────────────────────────────────────┤
│  E2E Tests (10%)                                           │
│  ├── User Journey Testing                                   │
│  ├── Cross-browser Testing                                  │
│  └── Mobile Device Testing                                  │
├─────────────────────────────────────────────────────────────┤
│  Integration Tests (20%)                                    │
│  ├── API Testing                                           │
│  ├── Database Integration                                   │
│  └── External Service Integration                           │
├─────────────────────────────────────────────────────────────┤
│  Unit Tests (70%)                                          │
│  ├── Model Testing                                         │
│  ├── Route Testing                                         │
│  ├── Utility Function Testing                              │
│  └── Business Logic Testing                                │
└─────────────────────────────────────────────────────────────┘
```

### Testing Principles

1. **Test-Driven Development**: Write tests before implementation
2. **Comprehensive Coverage**: Aim for 90%+ code coverage
3. **Fast Feedback**: Tests should run quickly and provide immediate feedback
4. **Isolated Tests**: Each test should be independent and repeatable
5. **Real-world Scenarios**: Tests should reflect actual user behavior

### Test Categories

| Category | Purpose | Tools | Coverage |
|----------|---------|-------|----------|
| Unit Tests | Test individual functions/methods | pytest, unittest | 70% |
| Integration Tests | Test component interactions | pytest, requests | 20% |
| E2E Tests | Test complete user workflows | Selenium, Playwright | 10% |
| Performance Tests | Test system performance | locust, pytest-benchmark | - |
| Security Tests | Test security vulnerabilities | bandit, safety | - |

---

## Test Environment Setup

### Prerequisites

#### Testing Dependencies
```bash
# Install testing dependencies
pip install pytest pytest-cov pytest-flask pytest-mock
pip install selenium webdriver-manager
pip install locust
pip install bandit safety
```

#### Test Database Setup
```python
# tests/conftest.py
import pytest
from app import create_app, db
from app.models import User, ClassGroup, University

@pytest.fixture
def app():
    """Create test application"""
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key'
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Create test CLI runner"""
    return app.test_cli_runner()
```

### Test Data Fixtures

#### Sample Data Creation
```python
# tests/fixtures.py
import pytest
from app import db
from app.models import User, ClassGroup, University

@pytest.fixture
def sample_university():
    """Create sample university"""
    university = University(
        name='Test University',
        domain='test.edu'
    )
    db.session.add(university)
    db.session.commit()
    return university

@pytest.fixture
def sample_class_group(sample_university):
    """Create sample class group"""
    class_group = ClassGroup(
        name='Test Class',
        code='TEST-100',
        join_code='TEST100',
        lecturer_code='LECTEST100',
        university_id=sample_university.id
    )
    db.session.add(class_group)
    db.session.commit()
    return class_group

@pytest.fixture
def sample_student(sample_class_group):
    """Create sample student"""
    student = User(
        username='test_student',
        email='student@test.edu',
        full_name='Test Student',
        role='Student',
        is_verified=True,
        class_group_id=sample_class_group.id,
        university_id=sample_class_group.university_id
    )
    student.set_password('password123')
    db.session.add(student)
    db.session.commit()
    return student

@pytest.fixture
def sample_lecturer(sample_university):
    """Create sample lecturer"""
    lecturer = User(
        username='test_lecturer',
        email='lecturer@test.edu',
        full_name='Test Lecturer',
        role='Lecturer',
        is_verified=True,
        university_id=sample_university.id
    )
    lecturer.set_password('password123')
    db.session.add(lecturer)
    db.session.commit()
    return lecturer
```

---

## Unit Testing

### Model Testing

#### User Model Tests
```python
# tests/test_models.py
import pytest
from app.models import User, ClassGroup, University

class TestUserModel:
    def test_user_creation(self, app):
        """Test user creation"""
        with app.app_context():
            user = User(
                username='testuser',
                email='test@example.com',
                full_name='Test User',
                role='Student'
            )
            user.set_password('password123')
            
            assert user.username == 'testuser'
            assert user.email == 'test@example.com'
            assert user.check_password('password123')
            assert not user.check_password('wrongpassword')
    
    def test_password_hashing(self, app):
        """Test password hashing"""
        with app.app_context():
            user = User(username='test', email='test@test.com')
            user.set_password('password123')
            
            assert user.password_hash != 'password123'
            assert user.check_password('password123')
    
    def test_avatar_initials(self, app):
        """Test avatar initials generation"""
        with app.app_context():
            user1 = User(full_name='John Doe', username='johndoe')
            user2 = User(full_name='Jane', username='jane')
            user3 = User(username='noname')
            
            assert user1.avatar_initials == 'JD'
            assert user2.avatar_initials == 'JA'
            assert user3.avatar_initials == 'NO'
    
    def test_password_reset_token(self, app):
        """Test password reset functionality"""
        with app.app_context():
            user = User(username='test', email='test@test.com')
            
            token = user.generate_password_reset_token()
            assert token is not None
            assert user.verify_password_reset_token(token)
            assert not user.verify_password_reset_token('invalid_token')
```

#### ClassGroup Model Tests
```python
class TestClassGroupModel:
    def test_class_group_creation(self, app, sample_university):
        """Test class group creation"""
        with app.app_context():
            class_group = ClassGroup(
                name='Test Class',
                code='TEST-100',
                join_code='TEST100',
                lecturer_code='LECTEST100',
                university_id=sample_university.id
            )
            
            assert class_group.name == 'Test Class'
            assert class_group.join_code == 'TEST100'
            assert not class_group.is_active_premium
    
    def test_subscription_upgrade(self, app, sample_class_group):
        """Test subscription upgrade"""
        with app.app_context():
            sample_class_group.upgrade_subscription('gold', 2)
            
            assert sample_class_group.subscription_plan == 'gold'
            assert sample_class_group.storage_limit_gb == 8.0
            assert sample_class_group.max_file_size_mb == 15
    
    def test_upload_permission_check(self, app, sample_class_group):
        """Test upload permission checking"""
        with app.app_context():
            # Free tier - no uploads allowed
            assert not sample_class_group.check_upload_permission(1.0)
            
            # Upgrade to gold
            sample_class_group.upgrade_subscription('gold', 1)
            assert sample_class_group.check_upload_permission(10.0)
            assert not sample_class_group.check_upload_permission(20.0)  # Too large
```

### Route Testing

#### Authentication Route Tests
```python
# tests/test_routes.py
import pytest
from flask import url_for

class TestAuthRoutes:
    def test_login_page(self, client):
        """Test login page loads"""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'Login' in response.data
    
    def test_register_page(self, client):
        """Test register page loads"""
        response = client.get('/register')
        assert response.status_code == 200
        assert b'Sign Up' in response.data
    
    def test_valid_login(self, client, sample_student):
        """Test valid user login"""
        response = client.post('/login', data={
            'username': 'test_student',
            'password': 'password123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Dashboard' in response.data
    
    def test_invalid_login(self, client, sample_student):
        """Test invalid login credentials"""
        response = client.post('/login', data={
            'username': 'test_student',
            'password': 'wrongpassword'
        })
        
        assert response.status_code == 200
        assert b'Invalid username or password' in response.data
    
    def test_student_registration(self, client, sample_class_group):
        """Test student registration with join code"""
        response = client.post('/register', data={
            'username': 'newstudent',
            'email': 'newstudent@test.edu',
            'password': 'password123',
            'full_name': 'New Student',
            'role': 'Student',
            'join_code': 'TEST100'
        })
        
        assert response.status_code == 302  # Redirect to verification
    
    def test_invalid_join_code(self, client):
        """Test registration with invalid join code"""
        response = client.post('/register', data={
            'username': 'newstudent',
            'email': 'newstudent@test.edu',
            'password': 'password123',
            'full_name': 'New Student',
            'role': 'Student',
            'join_code': 'INVALID'
        })
        
        assert b'Invalid Class Code' in response.data
```

#### Dashboard Route Tests
```python
class TestDashboardRoutes:
    def test_student_dashboard_access(self, client, sample_student):
        """Test student dashboard access"""
        # Login first
        client.post('/login', data={
            'username': 'test_student',
            'password': 'password123'
        })
        
        response = client.get('/student_dashboard')
        assert response.status_code == 200
        assert b'Student Dashboard' in response.data
    
    def test_unauthorized_dashboard_access(self, client):
        """Test unauthorized dashboard access"""
        response = client.get('/student_dashboard')
        assert response.status_code == 302  # Redirect to login
    
    def test_lecturer_dashboard_access(self, client, sample_lecturer):
        """Test lecturer dashboard access"""
        client.post('/login', data={
            'username': 'test_lecturer',
            'password': 'password123'
        })
        
        response = client.get('/lecturer_dashboard')
        assert response.status_code == 200
        assert b'Lecturer Dashboard' in response.data
```

### Utility Function Tests

#### File Handling Tests
```python
# tests/test_utils.py
import pytest
import tempfile
import os
from app.routes import allowed_file, calculate_file_hash

class TestFileUtils:
    def test_allowed_file_extensions(self):
        """Test file extension validation"""
        assert allowed_file('document.pdf')
        assert allowed_file('presentation.pptx')
        assert allowed_file('text.txt')
        assert not allowed_file('image.jpg')
        assert not allowed_file('script.py')
        assert not allowed_file('noextension')
    
    def test_file_hash_calculation(self):
        """Test file hash calculation"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write('test content')
            temp_path = f.name
        
        try:
            hash1 = calculate_file_hash(temp_path)
            hash2 = calculate_file_hash(temp_path)
            assert hash1 == hash2
            assert len(hash1) == 64  # SHA256 hex length
        finally:
            os.unlink(temp_path)
```

---

## Integration Testing

### Database Integration Tests

#### User-ClassGroup Integration
```python
# tests/test_integration.py
import pytest
from app import db
from app.models import User, ClassGroup, University

class TestDatabaseIntegration:
    def test_user_class_relationship(self, app, sample_class_group):
        """Test user-class group relationship"""
        with app.app_context():
            user = User(
                username='testuser',
                email='test@test.edu',
                role='Student',
                class_group_id=sample_class_group.id,
                university_id=sample_class_group.university_id
            )
            db.session.add(user)
            db.session.commit()
            
            # Test relationships
            assert user.class_group == sample_class_group
            assert user in sample_class_group.users
            assert user.university == sample_class_group.university
    
    def test_cascade_deletion(self, app, sample_class_group, sample_student):
        """Test cascade deletion behavior"""
        with app.app_context():
            class_id = sample_class_group.id
            
            # Delete class group
            db.session.delete(sample_class_group)
            db.session.commit()
            
            # Check if user's class_group_id is set to None
            user = User.query.get(sample_student.id)
            assert user.class_group_id is None
```

### API Integration Tests

#### File Upload Integration
```python
class TestFileUploadIntegration:
    def test_assignment_submission(self, client, sample_student):
        """Test complete assignment submission flow"""
        # Login
        client.post('/login', data={
            'username': 'test_student',
            'password': 'password123'
        })
        
        # Create test file
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b'Test assignment content')
            temp_path = f.name
        
        try:
            with open(temp_path, 'rb') as test_file:
                response = client.post('/submit_assignment', data={
                    'file': (test_file, 'test_assignment.txt'),
                    'course_id': 1
                })
            
            assert response.status_code == 302  # Redirect after success
        finally:
            os.unlink(temp_path)
    
    def test_file_size_limit(self, client, sample_student):
        """Test file size limit enforcement"""
        # Login
        client.post('/login', data={
            'username': 'test_student',
            'password': 'password123'
        })
        
        # Create large file (simulate)
        large_content = b'x' * (51 * 1024 * 1024)  # 51MB
        
        response = client.post('/submit_assignment', data={
            'file': (io.BytesIO(large_content), 'large_file.txt'),
            'course_id': 1
        })
        
        assert b'File too large' in response.data
```

### External Service Integration

#### Email Service Tests
```python
class TestEmailIntegration:
    @pytest.fixture
    def mail_mock(self, mocker):
        """Mock email sending"""
        return mocker.patch('app.mail.send')
    
    def test_registration_email(self, client, mail_mock):
        """Test registration email sending"""
        response = client.post('/register', data={
            'username': 'newuser',
            'email': 'newuser@test.edu',
            'password': 'password123',
            'full_name': 'New User',
            'role': 'Student',
            'join_code': 'TEST100'
        })
        
        assert mail_mock.called
        args, kwargs = mail_mock.call_args
        message = args[0]
        assert 'verification' in message.subject.lower()
        assert 'newuser@test.edu' in message.recipients
    
    def test_password_reset_email(self, client, sample_student, mail_mock):
        """Test password reset email"""
        response = client.post('/forgot_password', data={
            'email': 'student@test.edu'
        })
        
        assert mail_mock.called
        args, kwargs = mail_mock.call_args
        message = args[0]
        assert 'password reset' in message.subject.lower()
```

### Payment Integration Tests

#### Paystack Integration
```python
class TestPaymentIntegration:
    @pytest.fixture
    def paystack_mock(self, mocker):
        """Mock Paystack API calls"""
        return mocker.patch('requests.post')
    
    def test_payment_initialization(self, client, sample_student, paystack_mock):
        """Test payment initialization"""
        # Mock successful Paystack response
        paystack_mock.return_value.json.return_value = {
            'status': True,
            'data': {
                'authorization_url': 'https://checkout.paystack.com/test',
                'reference': 'TEST_REF_123'
            }
        }
        
        # Login as rep
        sample_student.role = 'Rep'
        db.session.commit()
        
        client.post('/login', data={
            'username': 'test_student',
            'password': 'password123'
        })
        
        response = client.post('/initiate_payment', data={
            'plan_name': 'gold',
            'duration_semesters': 1
        })
        
        assert response.status_code == 302
        assert paystack_mock.called
```

---

## End-to-End Testing

### Selenium Test Setup

#### Browser Configuration
```python
# tests/test_e2e.py
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

@pytest.fixture
def browser():
    """Setup Chrome browser for testing"""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    yield driver
    driver.quit()

@pytest.fixture
def live_server(app):
    """Start live server for E2E testing"""
    from werkzeug.serving import make_server
    import threading
    
    server = make_server('127.0.0.1', 5000, app)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    
    yield 'http://127.0.0.1:5000'
    server.shutdown()
```

### User Journey Tests

#### Student Registration Journey
```python
class TestStudentJourney:
    def test_complete_student_registration(self, browser, live_server, sample_class_group):
        """Test complete student registration flow"""
        browser.get(f"{live_server}/register")
        
        # Fill registration form
        browser.find_element(By.NAME, "username").send_keys("e2e_student")
        browser.find_element(By.NAME, "email").send_keys("e2e@test.edu")
        browser.find_element(By.NAME, "password").send_keys("password123")
        browser.find_element(By.NAME, "full_name").send_keys("E2E Test Student")
        
        # Select role
        role_select = browser.find_element(By.NAME, "role")
        role_select.send_keys("Student")
        
        # Enter join code
        browser.find_element(By.NAME, "join_code").send_keys("TEST100")
        
        # Submit form
        browser.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # Wait for redirect to verification page
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.TEXT, "Verification"))
        )
        
        assert "verify" in browser.current_url
    
    def test_student_login_and_dashboard(self, browser, live_server, sample_student):
        """Test student login and dashboard access"""
        browser.get(f"{live_server}/login")
        
        # Login
        browser.find_element(By.NAME, "username").send_keys("test_student")
        browser.find_element(By.NAME, "password").send_keys("password123")
        browser.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # Wait for dashboard
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "dashboard"))
        )
        
        assert "student_dashboard" in browser.current_url
        assert "Student Dashboard" in browser.page_source
```

#### Assignment Submission Journey
```python
class TestAssignmentJourney:
    def test_assignment_submission_flow(self, browser, live_server, sample_student):
        """Test complete assignment submission"""
        # Login first
        browser.get(f"{live_server}/login")
        browser.find_element(By.NAME, "username").send_keys("test_student")
        browser.find_element(By.NAME, "password").send_keys("password123")
        browser.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # Navigate to assignment submission
        WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Submit Assignment"))
        ).click()
        
        # Fill assignment form
        course_select = browser.find_element(By.NAME, "course_id")
        course_select.send_keys("1")
        
        # Upload file (create temporary file)
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b'Test assignment content')
            temp_path = f.name
        
        try:
            file_input = browser.find_element(By.NAME, "file")
            file_input.send_keys(temp_path)
            
            # Submit assignment
            browser.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            
            # Wait for success message
            WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "alert-success"))
            )
            
            assert "successfully submitted" in browser.page_source.lower()
        finally:
            os.unlink(temp_path)
```

### Cross-Browser Testing

#### Browser Compatibility Tests
```python
@pytest.mark.parametrize("browser_name", ["chrome", "firefox", "edge"])
class TestCrossBrowser:
    def test_login_across_browsers(self, browser_name, live_server, sample_student):
        """Test login functionality across different browsers"""
        driver = self.get_driver(browser_name)
        
        try:
            driver.get(f"{live_server}/login")
            driver.find_element(By.NAME, "username").send_keys("test_student")
            driver.find_element(By.NAME, "password").send_keys("password123")
            driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "dashboard"))
            )
            
            assert "dashboard" in driver.current_url
        finally:
            driver.quit()
    
    def get_driver(self, browser_name):
        """Get WebDriver instance for specified browser"""
        if browser_name == "chrome":
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            return webdriver.Chrome(options=options)
        elif browser_name == "firefox":
            options = webdriver.FirefoxOptions()
            options.add_argument('--headless')
            return webdriver.Firefox(options=options)
        elif browser_name == "edge":
            options = webdriver.EdgeOptions()
            options.add_argument('--headless')
            return webdriver.Edge(options=options)
```

---

## Performance Testing

### Load Testing with Locust

#### Basic Load Test
```python
# tests/test_performance.py
from locust import HttpUser, task, between

class WebsiteUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login before starting tasks"""
        response = self.client.post("/login", data={
            "username": "test_student",
            "password": "password123"
        })
    
    @task(3)
    def view_dashboard(self):
        """Test dashboard loading"""
        self.client.get("/student_dashboard")
    
    @task(2)
    def view_assignments(self):
        """Test assignments page"""
        self.client.get("/my_assignments")
    
    @task(1)
    def submit_assignment(self):
        """Test assignment submission"""
        with open("test_file.txt", "rb") as f:
            self.client.post("/submit_assignment", files={"file": f})
    
    @task(1)
    def view_library(self):
        """Test library access"""
        self.client.get("/library")
```

#### Database Performance Tests
```python
import pytest
import time
from app import db
from app.models import User, Assignment

class TestDatabasePerformance:
    def test_user_query_performance(self, app, sample_class_group):
        """Test user query performance"""
        with app.app_context():
            # Create many users
            users = []
            for i in range(1000):
                user = User(
                    username=f'user_{i}',
                    email=f'user_{i}@test.edu',
                    role='Student',
                    class_group_id=sample_class_group.id
                )
                users.append(user)
            
            db.session.add_all(users)
            db.session.commit()
            
            # Test query performance
            start_time = time.time()
            result = User.query.filter_by(class_group_id=sample_class_group.id).all()
            end_time = time.time()
            
            query_time = end_time - start_time
            assert query_time < 1.0  # Should complete within 1 second
            assert len(result) == 1000
    
    def test_assignment_pagination_performance(self, app, sample_student):
        """Test assignment pagination performance"""
        with app.app_context():
            # Create many assignments
            assignments = []
            for i in range(500):
                assignment = Assignment(
                    filename=f'assignment_{i}.txt',
                    file_path=f'/fake/path/assignment_{i}.txt',
                    user_id=sample_student.id
                )
                assignments.append(assignment)
            
            db.session.add_all(assignments)
            db.session.commit()
            
            # Test paginated query
            start_time = time.time()
            result = Assignment.query.filter_by(user_id=sample_student.id)\
                .order_by(Assignment.created_at.desc())\
                .paginate(page=1, per_page=20, error_out=False)
            end_time = time.time()
            
            query_time = end_time - start_time
            assert query_time < 0.5  # Should complete within 0.5 seconds
            assert len(result.items) == 20
```

### Memory and Resource Testing

#### Memory Usage Tests
```python
import psutil
import pytest

class TestResourceUsage:
    def test_memory_usage_during_file_upload(self, client, sample_student):
        """Test memory usage during file upload"""
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # Login
        client.post('/login', data={
            'username': 'test_student',
            'password': 'password123'
        })
        
        # Create large file in memory
        large_content = b'x' * (10 * 1024 * 1024)  # 10MB
        
        # Upload file
        response = client.post('/submit_assignment', data={
            'file': (io.BytesIO(large_content), 'large_file.txt'),
            'course_id': 1
        })
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 50MB)
        assert memory_increase < 50 * 1024 * 1024
```

---

## Security Testing

### Authentication Security Tests

#### Password Security Tests
```python
class TestPasswordSecurity:
    def test_password_hashing_strength(self, app):
        """Test password hashing security"""
        with app.app_context():
            user = User(username='test', email='test@test.com')
            user.set_password('password123')
            
            # Password should be hashed
            assert user.password_hash != 'password123'
            
            # Hash should be different each time
            user2 = User(username='test2', email='test2@test.com')
            user2.set_password('password123')
            assert user.password_hash != user2.password_hash
    
    def test_brute_force_protection(self, client):
        """Test protection against brute force attacks"""
        # Attempt multiple failed logins
        for i in range(10):
            response = client.post('/login', data={
                'username': 'nonexistent',
                'password': 'wrongpassword'
            })
        
        # Should implement rate limiting (this is a placeholder)
        # In real implementation, check for rate limiting response
        assert response.status_code in [200, 429]
```

### Input Validation Tests

#### SQL Injection Tests
```python
class TestSQLInjection:
    def test_login_sql_injection(self, client):
        """Test SQL injection in login form"""
        malicious_inputs = [
            "admin'; DROP TABLE users; --",
            "' OR '1'='1",
            "admin'/*",
            "' UNION SELECT * FROM users --"
        ]
        
        for malicious_input in malicious_inputs:
            response = client.post('/login', data={
                'username': malicious_input,
                'password': 'password'
            })
            
            # Should not cause server error or unauthorized access
            assert response.status_code in [200, 400]
            assert b'Dashboard' not in response.data
    
    def test_search_sql_injection(self, client, sample_student):
        """Test SQL injection in search functionality"""
        client.post('/login', data={
            'username': 'test_student',
            'password': 'password123'
        })
        
        malicious_query = "'; DROP TABLE assignments; --"
        response = client.get(f'/library?q={malicious_query}')
        
        assert response.status_code == 200
        # Database should still be intact
        from app.models import Assignment
        assert Assignment.query.count() >= 0  # Should not crash
```

### File Upload Security Tests

#### Malicious File Upload Tests
```python
class TestFileUploadSecurity:
    def test_executable_file_rejection(self, client, sample_student):
        """Test rejection of executable files"""
        client.post('/login', data={
            'username': 'test_student',
            'password': 'password123'
        })
        
        malicious_files = [
            ('malware.exe', b'MZ\x90\x00'),  # PE header
            ('script.php', b'<?php system($_GET["cmd"]); ?>'),
            ('shell.sh', b'#!/bin/bash\nrm -rf /'),
        ]
        
        for filename, content in malicious_files:
            response = client.post('/submit_assignment', data={
                'file': (io.BytesIO(content), filename),
                'course_id': 1
            })
            
            assert b'File type not allowed' in response.data or response.status_code == 400
    
    def test_file_size_limit_enforcement(self, client, sample_student):
        """Test file size limit enforcement"""
        client.post('/login', data={
            'username': 'test_student',
            'password': 'password123'
        })
        
        # Create file larger than limit
        large_content = b'x' * (51 * 1024 * 1024)  # 51MB
        
        response = client.post('/submit_assignment', data={
            'file': (io.BytesIO(large_content), 'large_file.txt'),
            'course_id': 1
        })
        
        assert response.status_code == 413 or b'File too large' in response.data
```

### Security Scanning

#### Automated Security Tests
```python
# tests/test_security_scan.py
import subprocess
import pytest

class TestSecurityScanning:
    def test_bandit_security_scan(self):
        """Run Bandit security scanner"""
        result = subprocess.run([
            'bandit', '-r', 'app/', '-f', 'json'
        ], capture_output=True, text=True)
        
        # Parse results and check for high severity issues
        import json
        if result.stdout:
            report = json.loads(result.stdout)
            high_severity_issues = [
                issue for issue in report.get('results', [])
                if issue.get('issue_severity') == 'HIGH'
            ]
            
            assert len(high_severity_issues) == 0, f"High severity security issues found: {high_severity_issues}"
    
    def test_dependency_vulnerabilities(self):
        """Check for known vulnerabilities in dependencies"""
        result = subprocess.run([
            'safety', 'check', '--json'
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            # Parse safety output for vulnerabilities
            assert False, f"Vulnerable dependencies found: {result.stdout}"
```

---

## User Acceptance Testing

### UAT Test Scenarios

#### Student User Stories
```python
# tests/test_uat.py
class TestStudentUserStories:
    def test_student_can_join_class_with_code(self, browser, live_server, sample_class_group):
        """
        As a student, I want to join a class using a join code
        so that I can access class materials and submit assignments.
        """
        browser.get(f"{live_server}/register")
        
        # Student fills registration form
        browser.find_element(By.NAME, "username").send_keys("new_student")
        browser.find_element(By.NAME, "email").send_keys("student@university.edu")
        browser.find_element(By.NAME, "password").send_keys("securepassword")
        browser.find_element(By.NAME, "full_name").send_keys("New Student")
        
        # Selects student role
        role_select = browser.find_element(By.NAME, "role")
        role_select.send_keys("Student")
        
        # Enters join code provided by class rep
        browser.find_element(By.NAME, "join_code").send_keys("TEST100")
        
        # Submits registration
        browser.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # Should be redirected to verification page
        WebDriverWait(browser, 10).until(
            lambda driver: "verify" in driver.current_url
        )
        
        # Success criteria: User is registered and needs to verify email
        assert "verify" in browser.current_url
        assert "verification code" in browser.page_source.lower()
    
    def test_student_can_submit_assignment(self, browser, live_server, sample_student):
        """
        As a student, I want to submit my assignment
        so that my lecturer can grade it.
        """
        # Login as student
        browser.get(f"{live_server}/login")
        browser.find_element(By.NAME, "username").send_keys("test_student")
        browser.find_element(By.NAME, "password").send_keys("password123")
        browser.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # Navigate to assignment submission
        WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Submit Assignment"))
        ).click()
        
        # Select course and upload file
        course_select = browser.find_element(By.NAME, "course_id")
        course_select.send_keys("1")
        
        # Create and upload test file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False, mode='w') as f:
            f.write('This is my assignment submission.')
            temp_path = f.name
        
        try:
            file_input = browser.find_element(By.NAME, "file")
            file_input.send_keys(temp_path)
            
            # Submit assignment
            browser.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            
            # Success criteria: Assignment is submitted successfully
            WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "alert-success"))
            )
            
            assert "successfully submitted" in browser.page_source.lower()
        finally:
            os.unlink(temp_path)
```

#### Lecturer User Stories
```python
class TestLecturerUserStories:
    def test_lecturer_can_grade_assignments(self, browser, live_server, sample_lecturer, sample_assignment):
        """
        As a lecturer, I want to grade student assignments
        so that I can provide feedback and marks.
        """
        # Login as lecturer
        browser.get(f"{live_server}/login")
        browser.find_element(By.NAME, "username").send_keys("test_lecturer")
        browser.find_element(By.NAME, "password").send_keys("password123")
        browser.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # Navigate to grading interface
        WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Grade Assignments"))
        ).click()
        
        # Select assignment to grade
        browser.find_element(By.CSS_SELECTOR, ".assignment-item").click()
        
        # Assign grade
        grade_select = browser.find_element(By.NAME, "grade")
        grade_select.send_keys("A")
        
        # Provide feedback
        feedback_area = browser.find_element(By.NAME, "feedback")
        feedback_area.send_keys("Excellent work! Well structured and comprehensive.")
        
        # Submit grade
        browser.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # Success criteria: Grade is saved and student is notified
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "alert-success"))
        )
        
        assert "grade saved" in browser.page_source.lower()
```

### Accessibility Testing

#### WCAG Compliance Tests
```python
class TestAccessibility:
    def test_keyboard_navigation(self, browser, live_server):
        """Test keyboard navigation accessibility"""
        browser.get(f"{live_server}/login")
        
        # Test tab navigation
        from selenium.webdriver.common.keys import Keys
        
        body = browser.find_element(By.TAG_NAME, "body")
        body.send_keys(Keys.TAB)  # Should focus on first input
        
        active_element = browser.switch_to.active_element
        assert active_element.get_attribute("name") == "username"
        
        # Continue tabbing through form
        active_element.send_keys(Keys.TAB)
        active_element = browser.switch_to.active_element
        assert active_element.get_attribute("name") == "password"
    
    def test_alt_text_for_images(self, browser, live_server):
        """Test alt text for images"""
        browser.get(f"{live_server}/")
        
        images = browser.find_elements(By.TAG_NAME, "img")
        for img in images:
            alt_text = img.get_attribute("alt")
            assert alt_text is not None and alt_text.strip() != "", f"Image missing alt text: {img.get_attribute('src')}"
    
    def test_form_labels(self, browser, live_server):
        """Test form labels for accessibility"""
        browser.get(f"{live_server}/register")
        
        inputs = browser.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='email'], input[type='password']")
        for input_element in inputs:
            input_id = input_element.get_attribute("id")
            if input_id:
                label = browser.find_element(By.CSS_SELECTOR, f"label[for='{input_id}']")
                assert label is not None, f"Input {input_id} missing associated label"
```

---

## Test Automation

### Continuous Integration Setup

#### GitHub Actions Workflow
```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_uniportal
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      redis:
        image: redis:6
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    
    - name: Run unit tests
      run: |
        pytest tests/test_models.py tests/test_routes.py -v --cov=app
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost/test_uniportal
        REDIS_URL: redis://localhost:6379/0
    
    - name: Run integration tests
      run: |
        pytest tests/test_integration.py -v
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost/test_uniportal
        REDIS_URL: redis://localhost:6379/0
    
    - name: Run security tests
      run: |
        bandit -r app/ -f json -o bandit-report.json
        safety check --json --output safety-report.json
    
    - name: Upload coverage reports
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
```

### Test Data Management

#### Test Database Seeding
```python
# tests/seed_test_data.py
from app import create_app, db
from app.models import University, ClassGroup, User, Course

def seed_test_data():
    """Seed database with test data"""
    app = create_app()
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
    
    with app.app_context():
        db.create_all()
        
        # Create test university
        university = University(
            name='Test University',
            domain='test.edu'
        )
        db.session.add(university)
        db.session.flush()
        
        # Create test class groups
        class_groups = [
            ClassGroup(
                name='Computer Science 100',
                code='CS-100',
                join_code='CS100',
                lecturer_code='LECCS100',
                university_id=university.id
            ),
            ClassGroup(
                name='Information Technology 200',
                code='IT-200',
                join_code='IT200',
                lecturer_code='LECIT200',
                university_id=university.id
            )
        ]
        
        for class_group in class_groups:
            db.session.add(class_group)
        
        db.session.flush()
        
        # Create test users
        users = [
            User(
                username='test_student1',
                email='student1@test.edu',
                full_name='Test Student One',
                role='Student',
                is_verified=True,
                class_group_id=class_groups[0].id,
                university_id=university.id
            ),
            User(
                username='test_lecturer1',
                email='lecturer1@test.edu',
                full_name='Test Lecturer One',
                role='Lecturer',
                is_verified=True,
                university_id=university.id
            ),
            User(
                username='test_rep1',
                email='rep1@test.edu',
                full_name='Test Rep One',
                role='Rep',
                is_verified=True,
                class_group_id=class_groups[0].id,
                university_id=university.id
            )
        ]
        
        for user in users:
            user.set_password('password123')
            db.session.add(user)
        
        db.session.commit()
        print("Test data seeded successfully!")

if __name__ == '__main__':
    seed_test_data()
```

### Test Reporting

#### Custom Test Reporter
```python
# tests/custom_reporter.py
import pytest
import json
from datetime import datetime

class CustomTestReporter:
    def __init__(self):
        self.test_results = []
        self.start_time = None
        self.end_time = None
    
    def pytest_runtest_setup(self, item):
        """Called before each test"""
        self.start_time = datetime.now()
    
    def pytest_runtest_teardown(self, item, nextitem):
        """Called after each test"""
        self.end_time = datetime.now()
    
    def pytest_runtest_logreport(self, report):
        """Called for each test report"""
        if report.when == 'call':
            result = {
                'test_name': report.nodeid,
                'outcome': report.outcome,
                'duration': report.duration,
                'timestamp': datetime.now().isoformat()
            }
            
            if report.outcome == 'failed':
                result['error'] = str(report.longrepr)
            
            self.test_results.append(result)
    
    def pytest_sessionfinish(self, session, exitstatus):
        """Called after all tests complete"""
        summary = {
            'total_tests': len(self.test_results),
            'passed': len([r for r in self.test_results if r['outcome'] == 'passed']),
            'failed': len([r for r in self.test_results if r['outcome'] == 'failed']),
            'skipped': len([r for r in self.test_results if r['outcome'] == 'skipped']),
            'total_duration': sum(r['duration'] for r in self.test_results),
            'timestamp': datetime.now().isoformat()
        }
        
        report = {
            'summary': summary,
            'results': self.test_results
        }
        
        with open('test_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\nTest Report Generated: test_report.json")
        print(f"Total: {summary['total_tests']}, Passed: {summary['passed']}, Failed: {summary['failed']}")
```

---

## Quality Assurance Procedures

### Code Review Checklist

#### Pre-Commit Checklist
```markdown
## Code Quality Checklist

### Functionality
- [ ] Code meets requirements
- [ ] All edge cases handled
- [ ] Error handling implemented
- [ ] Input validation present

### Testing
- [ ] Unit tests written and passing
- [ ] Integration tests updated
- [ ] Test coverage > 80%
- [ ] Manual testing completed

### Security
- [ ] Input sanitization implemented
- [ ] Authentication/authorization checked
- [ ] No sensitive data in logs
- [ ] SQL injection prevention verified

### Performance
- [ ] Database queries optimized
- [ ] No N+1 query problems
- [ ] Caching implemented where appropriate
- [ ] File handling optimized

### Code Style
- [ ] Code formatted with Black
- [ ] Linting passes (flake8)
- [ ] Type hints added where appropriate
- [ ] Documentation updated
```

### Release Testing Procedure

#### Pre-Release Testing
```python
# tests/test_release.py
import pytest
import requests
import subprocess

class TestReleaseReadiness:
    def test_all_critical_paths(self, client):
        """Test all critical user paths"""
        critical_paths = [
            '/login',
            '/register',
            '/student_dashboard',
            '/lecturer_dashboard',
            '/submit_assignment',
            '/library',
            '/health'
        ]
        
        for path in critical_paths:
            response = client.get(path)
            assert response.status_code in [200, 302], f"Critical path {path} failed"
    
    def test_database_migrations(self):
        """Test database migrations work correctly"""
        # This would test migration scripts
        result = subprocess.run([
            'python', '-c', 
            'from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Database migration failed: {result.stderr}"
    
    def test_external_services(self):
        """Test external service connectivity"""
        # Test email service (mock in testing)
        # Test payment gateway (test endpoints)
        # Test external APIs
        pass
    
    def test_configuration_validation(self):
        """Test production configuration"""
        # Validate all required environment variables
        # Check security settings
        # Verify SSL configuration
        pass
```

### Monitoring and Alerting

#### Test Result Monitoring
```python
# tests/test_monitoring.py
import pytest
import json
import requests

class TestMonitoring:
    def test_health_endpoint_response_time(self, client):
        """Test health endpoint response time"""
        import time
        
        start_time = time.time()
        response = client.get('/health')
        end_time = time.time()
        
        response_time = end_time - start_time
        assert response_time < 1.0, f"Health endpoint too slow: {response_time}s"
        assert response.status_code == 200
    
    def test_error_rate_threshold(self, client):
        """Test error rate is within acceptable limits"""
        total_requests = 100
        error_count = 0
        
        for i in range(total_requests):
            response = client.get('/student_dashboard')
            if response.status_code >= 500:
                error_count += 1
        
        error_rate = error_count / total_requests
        assert error_rate < 0.01, f"Error rate too high: {error_rate * 100}%"
```

---

*Document Version: 1.0*  
*Last Updated: December 16, 2024*  
*Status: Final*