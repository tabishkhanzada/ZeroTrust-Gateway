# Advanced Asynchronous Backend System (Enterprise Core)

The Advanced Asynchronous Backend System (Enterprise Core) is a high-performance, asynchronous authentication and authorization system built with FastAPI, SQLAlchemy 2.0 (Async), and Redis.

## 🚀 Key Features

- **Async Everything**: Non-blocking database and cache operations using `asyncpg` and `redis.asyncio`.
- **Zero-Trust Architecture**: Strict JWT validation and stateful revocation.
- **Dual-Token System**: Separation of short-lived Access tokens and long-lived Refresh tokens with distinct secrets.
- **Stateful Logout**: Redis-based JTI blacklisting for immediate session invalidation.
- **Enterprise Design**: Repository pattern, Service layer, and Dependency Injection for scalable development.

## 🛠️ Tech Stack

- **Framework**: FastAPI
- **Language**: Python 3.12+
- **Database**: PostgreSQL (SQLAlchemy 2.0 Async + asyncpg)
- **Caching**: Redis (redis.asyncio)
- **Security**: JWT (HS256), Bcrypt (Passlib)
- **Validation**: Pydantic v2
- **Testing**: Pytest-asyncio + httpx

## 📁 Architecture Overview

```text
app/
├── api/             # API routes and dependencies
├── core/            # Configuration, security, and lifecycle
├── models/          # SQLAlchemy async models
├── schemas/         # Pydantic v2 response/request models
├── repositories/    # Async database operations
├── services/        # Business logic
├── exceptions/      # Structured error handling
└── tests/           # Async integration tests
```

## 🔐 Security Design

### Token Lifecycle
1. **Access Token**: 15 minutes, used for route authorization.
2. **Refresh Token**: 7 days, used to obtain new token pairs.
3. **Invalidation**: On `/logout`, the JTI (JWT ID) of the access token is stored in Redis with a TTL matching its remaining life. All protected routes check the blacklist before allowing access.

## 🚦 Getting Started

### 1. Environment Setup
Copy `.env.example` to `.env` and configure your credentials.

### 2. Automatic Database Setup
Run the following script to automatically create the required PostgreSQL database:
```bash
.\venv\Scripts\python.exe init_db.py
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Application
```bash
uvicorn app.main:app --reload
```

## 🧪 Testing
Run the complete async test suite:
```bash
pytest app/tests/
```

## 📡 API Usage Examples

### Register User
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
     -H "Content-Type: application/json" \
     -d '{"email": "user@example.com", "password": "securepassword123"}'
```

### Login
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"email": "user@example.com", "password": "securepassword123"}'
```

### Get Profile (Protected)
```bash
curl -H "Authorization: Bearer <access_token>" "http://localhost:8000/api/v1/users/me"
```

### Logout
```bash
curl -X POST "http://localhost:8000/api/v1/auth/logout" \
     -H "Authorization: Bearer <access_token>"
```
