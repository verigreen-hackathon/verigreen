# VeriGreen Mock Land Registry Service

A demo FastAPI service that simulates a user registry system for generating web proofs in the VeriGreen hackathon project.

## Features

- 🔐 **JWT-based Authentication** - Secure user login/logout
- 👤 **User Registration** - Create new user accounts
- 📋 **User Profile Management** - View and manage user profiles
- 🎭 **Demo Data** - Pre-populated with sample users

## Quick Start

### 1. Install Dependencies

```bash
cd backend/mock_registry
pip install -r requirements.txt
```

### 2. Run the Service

```bash
python3 main.py
```

The service will start on `http://localhost:8001`

### 3. View API Documentation

Visit `http://localhost:8001/docs` for interactive API documentation

## Demo Users

The service comes with pre-configured demo users:

| Username       | Password        | Full Name      |
| -------------- | --------------- | -------------- |
| `user`         | `password`      | `Test User`    |
| `demo_user`    | `demo_password` | `Demo User`    |
| `forest_owner` | `forest123`     | `Forest Owner` |

## API Endpoints

### Authentication

- `POST /auth/register` - Register new user
- `POST /auth/login` - User login (returns JWT token)
- `GET /auth/profile` - Get current user profile

### Utility

- `GET /` - API information
- `GET /health` - Health check

## Example Usage

### 1. Login

```bash
curl -X POST "http://localhost:8001/auth/login" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=user&password=password"
```

Response:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 2. Get User Profile

```bash
curl -X GET "http://localhost:8001/auth/profile" \
     -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### 3. Register New User

```bash
curl -X POST "http://localhost:8001/auth/register" \
     -H "Content-Type: application/json" \
     -d '{
       "username": "new_user",
       "password": "new_password",
       "email": "new_user@example.com",
       "full_name": "New User"
     }'
```

## Integration with VeriGreen

This mock registry serves as a demo environment where:

1. **Users login** to authenticate their identity
2. **User profiles** store basic information
3. **Web proofs** can be generated based on user authentication
4. **vlayer system** can verify the authenticity of user sessions

## Security Note

⚠️ **This is a demo service only!**

- Uses hardcoded secret keys
- Stores data in memory (lost on restart)
- No production security measures
- CORS is open to all origins

For production use, implement:

- Environment-based configuration
- Persistent database storage
- Proper secret management
- Restricted CORS policies
- Rate limiting and input validation

## Development

### Project Structure

```
backend/mock_registry/
├── main.py           # FastAPI application
├── requirements.txt  # Python dependencies
└── README.md        # This file
```

### Extending the Service

To add new features:

1. Define new Pydantic models in `main.py`
2. Add new endpoints following FastAPI patterns
3. Update the in-memory storage or integrate a database
4. Add authentication where needed using `Depends(get_current_user)`

## Demo Flow

For hackathon demonstrations:

1. **Setup**: Start the mock registry service
2. **Login**: Authenticate with demo credentials (`user` / `password`)
3. **Profile**: View user profile information
4. **Generate Proof**: Use the authenticated session for web proof generation
5. **Verify**: Demonstrate the verification process with vlayer

This creates a simple but complete authentication demo for the VeriGreen system!
