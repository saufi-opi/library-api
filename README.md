# Library Management API

A production-ready RESTful API for managing a library system built with FastAPI, featuring comprehensive book management, borrower tracking, and role-based access control.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Quick Start](#quick-start)
- [Documentation](#documentation)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Testing](#testing)
- [License](#license)

## Overview

This Library Management API provides a complete backend solution for managing library operations including:
- **Borrower Registration** - Register and manage library members
- **Book Inventory** - Manage books with ISBN tracking and multiple copies support
- **Borrowing System** - Track book loans and returns with full history
- **Access Control** - Role-based permissions with fine-grained overrides

Built following modern best practices including containerization, CI/CD, comprehensive testing, and adherence to 12 Factor App principles.

## Features

### Core Functionality
- ✅ **User Management** - Register borrowers with email and password authentication
- ✅ **Book Management** - Add, update, list, and search books by ISBN, title, or author
- ✅ **Borrowing System** - Borrow and return books with automatic availability tracking
- ✅ **Transaction History** - Complete audit trail of all borrowing activities

### Technical Features
- 🔐 **JWT Authentication** - Secure token-based authentication
- 🛡️ **Role-Based Access Control (RBAC)** - Librarian and Member roles with customizable permissions
- 📊 **Flexible Permission Overrides** - Django/AWS IAM-style permission system
- 🔍 **Advanced Filtering** - Search, filter, and sort all resources
- ⚡ **Rate Limiting** - Redis-backed rate limiting on all endpoints
- 📝 **Input Validation** - Comprehensive request validation with Pydantic
- 🚀 **Production-Ready** - Docker containerization with health checks
- 🧪 **Fully Tested** - 2,462 lines of comprehensive unit and integration tests
- 📖 **Auto-Generated API Docs** - Swagger UI and ReDoc interfaces

## Quick Start

### Prerequisites

- **Docker & Docker Compose** (for containerized deployment)
- **Python 3.12+** (for local development)
- **Git** (for version control)

### Option 1: Run with Docker (Recommended)

This will start the API, PostgreSQL database, and Redis cache.

```bash
# 1. Clone the repository
git clone <repository-url>
cd library-api

# 2. Create environment file
cp .env.example .env

# 3. (Optional) Edit .env file to customize settings
# Default first superuser: admin@example.com / changethis

# 4. Start all services
docker-compose up -d

# 5. Check services are running
docker-compose ps

# 6. View logs (optional)
docker-compose logs -f backend
```

**The API is now running at:** http://localhost:8000

**Access the interactive API documentation:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Option 2: Local Development

```bash
# 1. Install dependencies (using uv package manager)
pip install uv
uv sync --all-extras --dev

# 2. Set up environment variables
cp .env.example .env
# Edit .env with your local PostgreSQL and Redis settings

# 3. Run database migrations
uv run alembic upgrade head

# 4. Start the development server
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

**The API is now running at:** http://localhost:8000

### First Steps

After starting the API, try these commands:

```bash
# Login as the default superuser
curl -X POST "http://localhost:8000/api/v1/login/access-token" \
  -d "username=admin@example.com&password=changethis"

# Save the token
export TOKEN="<your-access-token>"

# Create a new book
curl -X POST "http://localhost:8000/api/v1/books/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "isbn": "978-0-13-468599-1",
    "title": "The Pragmatic Programmer",
    "author": "David Thomas, Andrew Hunt"
  }'

# List all books
curl -X GET "http://localhost:8000/api/v1/books/" \
  -H "Authorization: Bearer $TOKEN"
```

## Documentation

Complete documentation is available in the following files:

| Document | Description |
|----------|-------------|
| **[API.md](API.md)** | Complete API reference with all endpoints, request/response examples, and error codes |
| **[ASSUMPTIONS.md](ASSUMPTIONS.md)** | Design decisions and assumptions for requirements not explicitly stated |
| **[DATABASE.md](DATABASE.md)** | Database schema, justification for PostgreSQL, and data model explanations |
| **[Deploy.md](Deploy.md)** | Production deployment guide with Docker Compose |
| **[README.md](README.md)** | This file - project overview and quick start |

### Interactive API Documentation

Once the server is running, access the interactive API docs:

- **Swagger UI:** http://localhost:8000/docs - Try out API calls directly in your browser
- **ReDoc:** http://localhost:8000/redoc - Clean, readable API documentation

## Technology Stack

**Language & Framework:**
- Python 3.12
- FastAPI (async web framework)
- Uvicorn (ASGI server)

**Database & Caching:**
- PostgreSQL 17 (relational database)
- Redis 7 (rate limiting cache)
- SQLModel (ORM with Pydantic integration)
- Alembic (database migrations)

**Authentication & Security:**
- JWT tokens (PyJWT)
- Bcrypt password hashing (passlib)
- Role-based access control (RBAC)
- Rate limiting (fastapi-limiter)

**Development Tools:**
- pytest (testing framework)
- ruff (linting and formatting)
- mypy (type checking)
- pre-commit (git hooks)

**Deployment:**
- Docker & Docker Compose
- Traefik (reverse proxy)
- GitHub Actions (CI/CD)

## API Endpoints Summary

**Base URL:** `/api/v1`

### Core Endpoints

| Category | Key Endpoints | Description |
|----------|---------------|-------------|
| **Authentication** | `POST /login/access-token`<br>`POST /users/signup` | Login and register new users |
| **Books** | `POST /books/`<br>`GET /books/`<br>`GET /books/{id}`<br>`PATCH /books/{id}`<br>`DELETE /books/{id}` | Full CRUD operations for books |
| **Borrows** | `POST /borrows/`<br>`POST /borrows/{id}/return`<br>`GET /borrows/me`<br>`GET /borrows/` | Borrow, return, and view borrowing history |
| **Users** | `GET /users/me`<br>`PATCH /users/me`<br>`PATCH /users/me/password` | User profile management |
| **Permissions** | `GET /users/{id}/permissions`<br>`POST /users/{id}/permissions/overrides` | Manage user permissions |

**→ For complete endpoint documentation, see [API.md](API.md)**

---

## Key Concepts

### Roles and Permissions

The system supports three user roles:

| Role | Capabilities |
|------|--------------|
| **Member** | Browse books, borrow books, return own books, view own history |
| **Librarian** | All member permissions + manage books (add/update/delete), view all borrows |
| **Superuser** | Full system access + manage users, assign permissions, create librarians |

**Permission System:**
- Role-based permissions (default set per role)
- Individual overrides (grant/deny specific permissions)
- Deny always wins (if both allow and deny exist, deny takes precedence)

**→ For detailed permission documentation, see [API.md - Permission Management](API.md#permission-management)**

---

### Data Models

The system uses four main models:

**1. User (Borrower)**
- Unique ID, email (unique), name
- Role (member/librarian), active status
- Password (bcrypt hashed)

**2. Book**
- Unique ID, ISBN, title, author
- Availability flag, creation timestamp
- Multiple copies allowed (same ISBN, different IDs)

**3. BorrowRecord**
- Unique ID, book_id, borrower_id
- Borrowed timestamp, returned timestamp (nullable)
- Complete transaction history

**4. UserPermissionOverride**
- Fine-grained permission control
- Per-user allow/deny rules

**→ For database schema and justification, see [DATABASE.md](DATABASE.md)**

---

### ISBN Handling

The system enforces these ISBN rules:

✓ Supports both ISBN-10 and ISBN-13 formats
✓ Hyphens and spaces are allowed in input (automatically normalized)
✓ Multiple copies of the same ISBN are allowed (each gets a unique book ID)
✓ **ISBN Consistency Rule:** Books with identical ISBN must have matching title and author

**Example:**
```json
// First book with ISBN 978-0-13-468599-1
{
  "isbn": "978-0-13-468599-1",
  "title": "The Pragmatic Programmer",
  "author": "David Thomas, Andrew Hunt"
}

// Second copy (allowed - same ISBN, same title/author)
{
  "isbn": "9780134685991",  // Same ISBN, different format
  "title": "The Pragmatic Programmer",
  "author": "David Thomas, Andrew Hunt"
}

// This would be REJECTED - same ISBN, different title
{
  "isbn": "978-0-13-468599-1",
  "title": "Different Title",  // ❌ Mismatch!
  "author": "David Thomas, Andrew Hunt"
}
```

---

### Business Rules

**Borrowing:**
- ✓ One book copy can only be borrowed by one user at a time
- ✓ Books must be available (`is_available = true`) to borrow
- ✓ Users borrow books for themselves (self-service)
- ✓ Borrowing automatically marks book as unavailable

**Returning:**
- ✓ Users can only return books they personally borrowed
- ✓ Cannot return a book that's already been returned
- ✓ Returning automatically marks book as available
- ✓ Timestamps are recorded for both borrow and return

**Other Rules:**
- ✓ No due dates or late fees (configurable for future)
- ✓ Complete borrowing history is maintained
- ✓ Soft deletes can be implemented (books with history cannot be deleted)

**→ For all assumptions and design decisions, see [ASSUMPTIONS.md](ASSUMPTIONS.md)**

---

## Project Structure

```
src/
├── auth/
│   ├── permissions.py    # Permission definitions and utilities
│   └── router.py         # Authentication endpoints
├── books/
│   ├── models.py         # Book SQLModel
│   ├── schemas.py        # API schemas
│   ├── router.py         # Book endpoints
│   └── service.py        # Business logic
├── borrows/
│   ├── models.py         # BorrowRecord SQLModel
│   ├── schemas.py        # API schemas
│   ├── router.py         # Borrow/Return endpoints
│   └── service.py        # Business logic
├── users/
│   ├── models.py         # User + UserPermissionOverride
│   ├── schemas.py        # API schemas
│   └── router.py         # User + Permission endpoints
├── core/
│   ├── dependencies.py   # FastAPI dependencies (require_permission)
│   └── db.py             # Database setup
└── main.py               # Application entry point
```

## Testing

The project includes comprehensive test coverage with 2,462 lines of tests.

### Run Tests

```bash
# Run all tests
uv run pytest tests/ -v

# Run with coverage report
uv run pytest tests/ --cov=src --cov-report=html --cov-report=term-missing

# Run specific test file
uv run pytest tests/api/routes/test_books.py -v

# Run tests in parallel (faster)
uv run pytest tests/ -n auto
```

### Test Coverage

The test suite covers:
- ✓ All API endpoints (CRUD operations)
- ✓ Authentication and authorization
- ✓ Permission system (roles + overrides)
- ✓ Business logic (borrowing rules, ISBN validation)
- ✓ Edge cases and error handling
- ✓ Data validation

### View Coverage Report

After running tests with coverage:
```bash
# Open HTML coverage report
open htmlcov/index.html  # macOS
start htmlcov/index.html  # Windows
xdg-open htmlcov/index.html  # Linux
```

---

## Development

### Code Quality Tools

```bash
# Lint code
uv run ruff check src/

# Format code
uv run ruff format src/

# Type check
uv run mypy src/

# Run all checks (lint + format + type check)
uv run ruff check src/ && uv run ruff format --check src/ && uv run mypy src/
```

### Pre-commit Hooks

The project uses pre-commit hooks to ensure code quality:

```bash
# Install pre-commit hooks
uv run pre-commit install

# Run manually
uv run pre-commit run --all-files
```

### Database Migrations

```bash
# Create a new migration
uv run alembic revision --autogenerate -m "description"

# Apply migrations
uv run alembic upgrade head

# Rollback one migration
uv run alembic downgrade -1

# View migration history
uv run alembic history
```

---

## Deployment

See [Deploy.md](Deploy.md) for complete deployment instructions.

**Quick deployment with Docker Compose:**
```bash
docker-compose up -d
```

**CI/CD:**
- GitHub Actions workflow runs on every push
- Automated linting, testing, type checking, and security scanning
- Docker image build and deployment (staging/production)

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`uv run pytest tests/`)
5. Run code quality checks (`uv run ruff check src/`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

---

## Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check existing documentation in the `/docs` folder
- Review the API documentation at `/docs` (Swagger UI)

---

## License

MIT License
