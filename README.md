# Library Management API

A RESTful API for managing a library system built with FastAPI, featuring role-based access control (RBAC) with flexible permissions.

## Features

- **User Authentication** - JWT-based authentication
- **Role-Based Access Control** - Librarian and Member roles with permission system
- **Flexible Permissions** - Django/AWS IAM-style permission overrides
- **Book Management** - Register and manage library books
- **Borrowing System** - Borrow and return books with transaction tracking

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)

### Running with Docker

```bash
# Clone the repository
git clone <repository-url>
cd library-api

# Create .env file from example
cp .env.example .env

# Start the application
docker-compose up -d

# Run database migrations
docker-compose exec backend alembic upgrade head
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start the server
uvicorn src.main:app --reload
```

## API Documentation

Once running, access the interactive API docs at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## API Endpoints

### Authentication

| Method | Endpoint                     | Description       |
| ------ | ---------------------------- | ----------------- |
| POST   | `/api/v1/login/access-token` | Get access token  |
| POST   | `/api/v1/users/signup`       | Register new user |

### Books

| Method | Endpoint             | Permission     | Description         |
| ------ | -------------------- | -------------- | ------------------- |
| POST   | `/api/v1/books/`     | `books:create` | Register a new book |
| GET    | `/api/v1/books/`     | `books:read`   | List all books      |
| GET    | `/api/v1/books/{id}` | `books:read`   | Get book by ID      |
| PATCH  | `/api/v1/books/{id}` | `books:update` | Update a book       |
| DELETE | `/api/v1/books/{id}` | `books:delete` | Delete a book       |

### Borrows

| Method | Endpoint                      | Permission         | Description             |
| ------ | ----------------------------- | ------------------ | ----------------------- |
| POST   | `/api/v1/borrows/`            | `borrows:create`   | Borrow a book           |
| POST   | `/api/v1/borrows/{id}/return` | `borrows:return`   | Return a borrowed book  |
| GET    | `/api/v1/borrows/me`          | `borrows:read`     | List my borrow records  |
| GET    | `/api/v1/borrows/`            | `borrows:read_all` | List all borrow records |
| GET    | `/api/v1/borrows/{id}`        | `borrows:read`     | Get borrow record by ID |

### Users & Permissions

| Method | Endpoint                                                 | Permission        | Description                |
| ------ | -------------------------------------------------------- | ----------------- | -------------------------- |
| GET    | `/api/v1/users/{id}/permissions`                         | Self or Superuser | Get effective permissions  |
| GET    | `/api/v1/users/{id}/permissions/overrides`               | Superuser         | List permission overrides  |
| POST   | `/api/v1/users/{id}/permissions/overrides`               | Superuser         | Add permission override    |
| DELETE | `/api/v1/users/{id}/permissions/overrides/{override_id}` | Superuser         | Delete permission override |

---

## Permission System

### Roles and Default Permissions

| Role          | Default Permissions                                                                                            |
| ------------- | -------------------------------------------------------------------------------------------------------------- |
| **Librarian** | `books:create`, `books:read`, `books:update`, `books:delete`, `borrows:read`, `borrows:read_all`, `users:read` |
| **Member**    | `books:read`, `borrows:create`, `borrows:return`, `borrows:read`                                               |

### Permission Overrides

Individual users can have permissions added or revoked:

```json
// Grant a member the ability to manage books
POST /api/v1/users/{user_id}/permissions/overrides
{
    "permission": "books:create",
    "effect": "allow"
}

// Revoke borrowing ability from a member
POST /api/v1/users/{user_id}/permissions/overrides
{
    "permission": "borrows:create",
    "effect": "deny"
}
```

> **Note:** Deny always takes precedence over Allow.

---

## Data Models

### Book

```json
{
  "id": "uuid",
  "isbn": "978-0-13-468599-1",
  "title": "The Pragmatic Programmer",
  "author": "David Thomas, Andrew Hunt",
  "is_available": true,
  "created_at": "2024-12-10T10:00:00Z"
}
```

### Borrower (User)

```json
{
  "id": "uuid",
  "email": "borrower@example.com",
  "full_name": "John Doe",
  "role": "member",
  "is_active": true
}
```

### Borrow Record

```json
{
  "id": "uuid",
  "book_id": "uuid",
  "borrower_id": "uuid",
  "borrowed_at": "2024-12-10T10:00:00Z",
  "returned_at": null
}
```

---

## Example Workflows

### Register and Borrow a Book

```bash
# 1. Register a new user (as member by default)
curl -X POST "http://localhost:8000/api/v1/users/signup" \
  -H "Content-Type: application/json" \
  -d '{"email": "member@example.com", "password": "password123", "full_name": "John Doe"}'

# 2. Login to get access token
curl -X POST "http://localhost:8000/api/v1/login/access-token" \
  -d "username=member@example.com&password=password123"

# 3. List available books
curl -X GET "http://localhost:8000/api/v1/books/?available_only=true" \
  -H "Authorization: Bearer <token>"

# 4. Borrow a book
curl -X POST "http://localhost:8000/api/v1/borrows/" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"book_id": "<book-uuid>"}'

# 5. Return the book
curl -X POST "http://localhost:8000/api/v1/borrows/<borrow-id>/return" \
  -H "Authorization: Bearer <token>"
```

### Librarian: Add a Book

```bash
# Login as librarian
curl -X POST "http://localhost:8000/api/v1/login/access-token" \
  -d "username=librarian@example.com&password=password123"

# Register a new book
curl -X POST "http://localhost:8000/api/v1/books/" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "isbn": "978-0-13-468599-1",
    "title": "The Pragmatic Programmer",
    "author": "David Thomas, Andrew Hunt"
  }'
```

---

## Assumptions

1. **No Borrow Duration Limit** - No due dates or late fees
2. **Single Role Per User** - Users have one role (librarian or member)
3. **Self-Service Borrowing** - Members borrow books for themselves
4. **Return Own Books** - Members can only return books they borrowed
5. **ISBN Consistency** - Books with the same ISBN must have matching title and author
6. **Multiple Copies** - Same ISBN books are registered separately with unique IDs
7. **Deny Wins** - Permission deny overrides always take precedence

---

## Database

**PostgreSQL** is used because:

- ACID compliance for transaction integrity
- Relational model fits the domain well
- Concurrent access handling for borrow/return operations

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

---

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

---

## License

MIT License
