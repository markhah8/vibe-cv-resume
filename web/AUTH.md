# User Authentication System

## Overview
Flask-based authentication system with email/password login and registration.

## Features
- ✅ User registration with email/password
- ✅ Secure password hashing (Werkzeug scrypt)
- ✅ Login/Logout functionality
- ✅ Session management (Flask-Login)
- ✅ Protected routes
- ✅ JSON-based user database

## Database
**Location:** `/web/users.json`

**Structure:**
```json
{
  "user_id": {
    "email": "user@example.com",
    "password_hash": "scrypt:32768:8:1$..."
  }
}
```

## Default Admin Account
```
Email: admin@vibe-cv.com
Password: admin123
```

## Routes

### Public Routes
- `GET /login` - Login page
- `POST /login` - Login form submission
- `GET /register` - Registration page
- `POST /register` - Registration form submission

### Protected Routes (require login)
- `GET /` - Dashboard
- `GET /logout` - Logout
- `POST /api/create-variant` - Create CV variant
- `POST /api/compile-cv` - Compile PDF
- `GET /api/download-pdf/<folder>` - Download PDF
- `DELETE /api/delete-variant/<folder>` - Delete variant

## Registration Validation
- ✅ Email format validation (HTML5)
- ✅ Password minimum 6 characters
- ✅ Confirm password must match
- ✅ Email uniqueness check
- ✅ Flash messages for errors/success

## Security Features
- 🔒 Password hashing with scrypt (32768 rounds)
- 🔒 Session-based authentication
- 🔒 CSRF protection (Flask default)
- 🔒 Secure cookie settings
- 🔒 Auto-redirect for unauthenticated users

## Usage

### Register New User
1. Navigate to `/register`
2. Enter email and password (min 6 chars)
3. Confirm password
4. Click "Create Account"
5. Redirected to login page

### Login
1. Navigate to `/login`
2. Enter registered email/password
3. Click "Sign In"
4. Redirected to dashboard

### Logout
1. Click "Logout" button in header
2. Session cleared
3. Redirected to login page

## User Management

### View All Users
```bash
cat /Applications/Soft/vibe-cv-resume/web/users.json
```

### Manually Add User (via Python)
```python
from werkzeug.security import generate_password_hash
import json

users = json.load(open('users.json'))
new_id = str(max([int(k) for k in users.keys()]) + 1)
users[new_id] = {
    'email': 'newuser@example.com',
    'password_hash': generate_password_hash('password123')
}
json.dump(users, open('users.json', 'w'), indent=2)
```

### Reset Password
```python
from werkzeug.security import generate_password_hash
import json

users = json.load(open('users.json'))
# Find user by email
for uid, data in users.items():
    if data['email'] == 'user@example.com':
        data['password_hash'] = generate_password_hash('newpassword')
        break
json.dump(users, open('users.json', 'w'), indent=2)
```

## Configuration

### Environment Variables (.env)
```bash
SECRET_KEY=your-secret-key-here  # Required for session encryption
```

### Dependencies
```
Flask==3.0.0
Flask-Login==0.6.3
Werkzeug==3.0.1
```

## Troubleshooting

### "Please log in to access this page"
- Session expired or not logged in
- Solution: Navigate to `/login`

### "Email already registered"
- Email exists in database
- Solution: Use different email or login with existing account

### "Invalid email or password"
- Wrong credentials
- Solution: Check email/password or register new account

### Can't access admin account
- Default admin created on first app startup
- Email: admin@vibe-cv.com
- Password: admin123
- Location: users.json with user_id "1"

## Development Notes

- User IDs are auto-incremented integers (as strings)
- First user is always admin (ID: "1")
- Session cookies are secure in production (HTTPS)
- Debug mode shows login_required redirects clearly
- Flash messages auto-dismiss after 5 seconds (success only)
