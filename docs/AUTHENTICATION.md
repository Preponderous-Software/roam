# JWT Authentication and Authorization

This document describes the JWT-based authentication and authorization system implemented for the Roam game server and Python client.

## Overview

The authentication system provides:
- User registration and login
- JWT-based stateless authentication
- Role-based access control (RBAC)
- Refresh token mechanism
- Token revocation/blacklisting
- Secure password hashing with BCrypt
- Automatic token management in Python client

## Python Client Usage

### Quick Start

```python
from client.api_client import RoamAPIClient

# Create client
client = RoamAPIClient("http://localhost:8080")

# Register new user
response = client.register("myusername", "mypassword", "me@example.com")
print(f"Logged in as {response['username']}")

# Now you can make authenticated API calls
session = client.init_session()
player = client.get_player()

# Logout when done
client.logout()
```

### Registration

```python
client = RoamAPIClient("http://localhost:8080")

try:
    response = client.register(
        username="player1",
        password="securePassword123",
        email="player1@example.com"
    )
    print(f"Welcome, {response['username']}!")
    print(f"Roles: {response['roles']}")
    print(f"Token expires in: {response['expiresIn']} seconds")
except Exception as e:
    print(f"Registration failed: {e}")
```

### Login

```python
client = RoamAPIClient("http://localhost:8080")

try:
    response = client.login(
        username="player1",
        password="securePassword123"
    )
    print(f"Welcome back, {response['username']}!")
    # Client now has authentication tokens stored
except Exception as e:
    print(f"Login failed: {e}")
```

### Using Protected Endpoints

Once authenticated, all API calls automatically include the JWT token:

```python
# No need to manually add authentication headers!
session = client.init_session()
player = client.get_player()
inventory = client.get_inventory()
```

The client automatically:
- Adds `Authorization: Bearer <token>` header to requests
- Refreshes expired tokens using the refresh token
- Handles authentication errors

### Logout

```python
client.logout()  # Revokes tokens and clears client state
```

### Check Authentication Status

```python
if client.is_authenticated():
    print("User is logged in")
else:
    print("User is not authenticated")
```

## Authentication Flow

### 1. User Registration

**Endpoint**: `POST /api/v1/auth/register`

**Request Body**:
```json
{
  "username": "player1",
  "password": "securePassword123",
  "email": "player1@example.com"
}
```

**Response** (201 Created):
```json
{
  "accessToken": "eyJhbGciOiJIUzI1NiIs...",
  "refreshToken": "eyJhbGciOiJIUzI1NiIs...",
  "tokenType": "Bearer",
  "expiresIn": 3600,
  "username": "player1",
  "roles": ["ROLE_USER"]
}
```

### 2. User Login

**Endpoint**: `POST /api/v1/auth/login`

**Request Body**:
```json
{
  "username": "player1",
  "password": "securePassword123"
}
```

**Response** (200 OK):
```json
{
  "accessToken": "eyJhbGciOiJIUzI1NiIs...",
  "refreshToken": "eyJhbGciOiJIUzI1NiIs...",
  "tokenType": "Bearer",
  "expiresIn": 3600,
  "username": "player1",
  "roles": ["ROLE_USER"]
}
```

### 3. Accessing Protected Endpoints

Include the access token in the `Authorization` header:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

Example:
```bash
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
     http://localhost:8080/api/v1/session/12345
```

### 4. Refresh Token

When the access token expires, use the refresh token to get a new access token without re-authenticating.

**Endpoint**: `POST /api/v1/auth/refresh`

**Request Body**:
```json
{
  "refreshToken": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response** (200 OK):
```json
{
  "accessToken": "eyJhbGciOiJIUzI1NiIs...",
  "refreshToken": "eyJhbGciOiJIUzI1NiIs...",
  "tokenType": "Bearer",
  "expiresIn": 3600,
  "username": "player1",
  "roles": ["ROLE_USER"]
}
```

### 5. Logout

**Endpoint**: `POST /api/v1/auth/logout`

**Headers**:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

**Response** (200 OK):
```json
{
  "message": "Logged out successfully"
}
```

Logout blacklists the access token and revokes all refresh tokens for the user.

## Configuration

### JWT Secret

Set a secure JWT secret in production using an environment variable:

```bash
export JWT_SECRET="your-secure-secret-key-at-least-256-bits-long"
```

Or in `application.yml`:
```yaml
jwt:
  secret: ${JWT_SECRET:default-secret-key...}
```

### Token Expiration

Configure token expiration times in `application.yml`:

```yaml
jwt:
  expiration:
    access: 3600000  # 1 hour in milliseconds
    refresh: 86400000  # 24 hours in milliseconds
```

## Security Features

### Password Hashing
Passwords are hashed using BCrypt with a strength of 10 (default), providing strong protection against brute-force attacks.

### CSRF Protection
CSRF protection is disabled for this stateless REST API as JWT tokens in headers provide protection against CSRF attacks. The tokens are not stored in cookies, preventing CSRF vulnerabilities.

### Token Blacklisting
When a user logs out, their access token is added to a blacklist, preventing its reuse. The blacklist is stored in the database and automatically cleaned up when tokens expire.

### Session Isolation
Each user's session is isolated. Sessions created by one user cannot be accessed by another user, enforcing proper authorization.

### CORS Configuration
CORS is configured to allow specific origins. In production, configure allowed origins via the `ALLOWED_ORIGINS` environment variable:

```bash
export ALLOWED_ORIGINS="https://yourdomain.com,https://app.yourdomain.com"
```

## Role-Based Access Control

The system supports role-based access control. By default, all registered users get the `ROLE_USER` role.

To check roles programmatically:
```java
@PreAuthorize("hasRole('USER')")
public void userOnlyMethod() {
    // Only users with ROLE_USER can access this
}

@PreAuthorize("hasRole('ADMIN')")
public void adminOnlyMethod() {
    // Only users with ROLE_ADMIN can access this
}
```

## Database Schema

The authentication system creates the following tables:

- **users**: Stores user accounts
- **user_roles**: Stores user roles (many-to-many relationship)
- **refresh_tokens**: Stores refresh tokens
- **token_blacklist**: Stores revoked access tokens

## Error Handling

### 401 Unauthorized
Returned when:
- No authentication token is provided
- Token is invalid or expired
- Invalid credentials during login

### 400 Bad Request
Returned when:
- Required fields are missing
- Field validation fails (e.g., invalid email format, password too short)

### 500 Internal Server Error
Returned when:
- Username or email already exists (registration)
- Other server errors

## Testing

Authentication integration tests are located in:
```
server/src/test/java/com/preponderous/roam/controller/AuthControllerIntegrationTest.java
```

Run tests with:
```bash
cd server
mvn test
```

## Security Considerations

1. **JWT Secret**: Always use a strong, randomly generated secret in production (at least 256 bits).
2. **HTTPS**: Always use HTTPS in production to protect tokens in transit.
3. **Token Storage**: Store tokens securely on the client side (e.g., in memory or secure storage, not localStorage for sensitive applications).
4. **Token Expiration**: Keep access token expiration short (e.g., 1 hour) and use refresh tokens for longer sessions.
5. **Password Policy**: Enforce strong password requirements on the client side.
6. **Rate Limiting**: Consider implementing rate limiting on authentication endpoints to prevent brute-force attacks.

## GUI Client (Roam Game)

The Roam game client includes a graphical login screen that appears on startup.

### Login Screen Features

- **Interactive Form**: Enter username and password with keyboard input
- **Toggle Mode**: Click the "Switch to Registration" / "Switch to Login" button to toggle between modes
- **Navigation**: 
  - TAB: Switch between input fields
  - ENTER: Submit form
  - ESC: Cancel or return to previous screen
- **Visual Feedback**: Active field is highlighted, error messages displayed
- **Auto-Authentication**: Once logged in, the client stores tokens for API calls
- **Remember Username**: Check the "Remember username" box to save your username between sessions

### First Time Setup

1. Start the Roam client
2. Click "Switch to Registration" button to switch to Registration mode
3. Enter username, press TAB
4. Enter password, press TAB  
5. Enter email, press ENTER
6. On success, you'll be logged in and taken to the main menu

### Subsequent Sessions

The client will show the login screen on startup:
1. Enter your username (or use the saved username if "Remember username" was checked)
2. Press TAB and enter your password
3. Press ENTER to login

## Security Summary

The implemented authentication system provides:
- ✅ Secure password storage with BCrypt hashing
- ✅ Stateless JWT authentication
- ✅ Token refresh mechanism
- ✅ Token revocation/blacklisting
- ✅ Role-based access control
- ✅ CORS protection
- ✅ Protection against CSRF attacks (via JWT in headers)
- ✅ Session isolation between users
- ✅ Proper error handling and security headers
- ✅ Python client with automatic token management
- ✅ GUI login screen for game client

### Known Considerations

- **CSRF Protection Disabled**: This is intentional for a stateless REST API using JWT tokens in headers. Tokens are not stored in cookies, so traditional CSRF attacks are not applicable.
- **H2 Console**: Frame options are disabled for the H2 console in development. This should be secured or disabled in production.
