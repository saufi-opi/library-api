# Library Management API - Complete API Documentation

This document provides comprehensive documentation for all API endpoints in the Library Management System.

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Pagination and Filtering](#pagination-and-filtering)
- [API Endpoints](#api-endpoints)
  - [Authentication Endpoints](#authentication-endpoints)
  - [User Management](#user-management)
  - [Book Management](#book-management)
  - [Borrow Management](#borrow-management)
  - [Permission Management](#permission-management)

---

## Overview

**Base URL:** `http://localhost:8000/api/v1`

**API Version:** v1

**Protocol:** HTTP/HTTPS

**Data Format:** JSON

**Character Encoding:** UTF-8

---

## Authentication

This API uses **JWT (JSON Web Token)** bearer authentication.

### Getting a Token

**Endpoint:** `POST /login/access-token`

**Request:**
```http
POST /api/v1/login/access-token HTTP/1.1
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=yourpassword
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Using the Token

Include the token in the `Authorization` header for all authenticated requests:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Token Expiration

- Access tokens expire after **60 minutes** (configurable)
- When a token expires, you'll receive a `401 Unauthorized` response
- Request a new token using the login endpoint

---

## Error Handling

### Standard Error Response

All errors follow a consistent format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request succeeded |
| 400 | Bad Request | Invalid input data or business logic violation |
| 401 | Unauthorized | Missing or invalid authentication token |
| 403 | Forbidden | Insufficient permissions for this action |
| 404 | Not Found | Requested resource doesn't exist |
| 409 | Conflict | Resource conflict (e.g., duplicate email) |
| 422 | Unprocessable Entity | Validation error in request data |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server-side error |

### Common Error Examples

**401 Unauthorized - Missing Token:**
```json
{
  "detail": "Not authenticated"
}
```

**403 Forbidden - Insufficient Permissions:**
```json
{
  "detail": "Not enough permissions"
}
```

**404 Not Found:**
```json
{
  "detail": "Book not found"
}
```

**400 Bad Request - Book Not Available:**
```json
{
  "detail": "Book is not available for borrowing"
}
```

**422 Validation Error:**
```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "password"],
      "msg": "String should have at least 8 characters",
      "input": "short",
      "ctx": {"min_length": 8}
    }
  ]
}
```

---

## Rate Limiting

**Default Limits:**
- Login endpoints: **5 requests per 60 seconds**
- All other endpoints: **60 requests per 60 seconds**

**Rate Limit Headers:**
When rate-limited, you'll receive a `429 Too Many Requests` response. Wait before retrying.

**Note:** Rate limiting is disabled in the testing environment.

---

## Pagination and Filtering

### Pagination Parameters

List endpoints support pagination:

| Parameter | Type | Default | Max | Description |
|-----------|------|---------|-----|-------------|
| `skip` | integer | 0 | - | Number of records to skip |
| `limit` | integer | 100 | 1000 | Maximum number of records to return |

**Example:**
```http
GET /api/v1/books/?skip=20&limit=10
```

### Sorting

Use the `sort` parameter with field names. Prefix with `-` for descending order:

| Value | Description |
|-------|-------------|
| `title` | Sort by title (A-Z) |
| `-title` | Sort by title (Z-A) |
| `created_at` | Sort by creation date (oldest first) |
| `-created_at` | Sort by creation date (newest first) |

**Example:**
```http
GET /api/v1/books/?sort=-created_at
```

---

## API Endpoints

---

## Authentication Endpoints

### 1. Login

Get an access token for authentication.

**Endpoint:** `POST /login/access-token`

**Rate Limit:** 5 requests per 60 seconds

**Authentication:** None (public endpoint)

**Request Body (form-urlencoded):**
```
username=user@example.com
password=yourpassword
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/login/access-token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=yourpassword"
```

**Success Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyQGV4YW1wbGUuY29tIiwiZXhwIjoxNzAyMzE4ODAwfQ.xyz",
  "token_type": "bearer"
}
```

**Error Responses:**

- **400 Bad Request** - Invalid credentials:
```json
{
  "detail": "Incorrect email or password"
}
```

- **400 Bad Request** - Inactive account:
```json
{
  "detail": "Inactive user"
}
```

---

### 2. Test Token

Validate the current access token.

**Endpoint:** `POST /login/test-token`

**Rate Limit:** 5 requests per 60 seconds

**Authentication:** Required

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/login/test-token" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Success Response (200 OK):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "member",
  "is_active": true,
  "is_superuser": false
}
```

**Error Response:**

- **401 Unauthorized** - Invalid token

---

## User Management

### 3. Register New User (Sign Up)

Register a new user account (member by default).

**Endpoint:** `POST /users/signup`

**Rate Limit:** 60 requests per 60 seconds

**Authentication:** None (public endpoint)

**Request Body (JSON):**
```json
{
  "email": "newuser@example.com",
  "password": "securepass123",
  "full_name": "Jane Smith"
}
```

**Field Requirements:**
- `email` (required): Valid email address, must be unique
- `password` (required): 8-40 characters
- `full_name` (optional): Maximum 255 characters

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/users/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "password": "securepass123",
    "full_name": "Jane Smith"
  }'
```

**Success Response (200 OK):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "newuser@example.com",
  "full_name": "Jane Smith",
  "role": "member",
  "is_active": true,
  "is_superuser": false
}
```

**Error Responses:**

- **409 Conflict** - Email already exists:
```json
{
  "detail": "A user with this email already exists"
}
```

- **422 Validation Error** - Invalid email format:
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "email"],
      "msg": "value is not a valid email address"
    }
  ]
}
```

---

### 4. Get Current User

Get the profile of the currently authenticated user.

**Endpoint:** `GET /users/me`

**Authentication:** Required

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Success Response (200 OK):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "member",
  "is_active": true,
  "is_superuser": false
}
```

---

## Book Management

### 5. Register a New Book

Add a new book to the library. Creates a new book record even if the ISBN already exists (allows multiple copies).

**Endpoint:** `POST /books/`

**Authentication:** Required

**Permission:** `books:create` (Librarian role by default)

**Request Body (JSON):**
```json
{
  "isbn": "978-0-13-468599-1",
  "title": "The Pragmatic Programmer",
  "author": "David Thomas, Andrew Hunt"
}
```

**Field Requirements:**
- `isbn` (required): ISBN-10 or ISBN-13 format
  - ISBN-10: 10 digits (last digit can be X)
  - ISBN-13: 13 digits
  - Hyphens and spaces are allowed and will be removed
  - Maximum 20 characters after formatting
- `title` (required): 1-500 characters
- `author` (required): 1-255 characters

**ISBN Consistency Rule:**
- If another book with the same ISBN exists, the new book MUST have the same title and author
- This ensures ISBN integrity across the system

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/books/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "isbn": "978-0-13-468599-1",
    "title": "The Pragmatic Programmer",
    "author": "David Thomas, Andrew Hunt"
  }'
```

**Success Response (200 OK):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "isbn": "9780134685991",
  "title": "The Pragmatic Programmer",
  "author": "Data Thomas, Andrew Hunt",
  "is_available": true,
  "created_at": "2024-12-10T10:30:00Z"
}
```

**Note:** The ISBN is normalized (hyphens/spaces removed) in the response.

**Error Responses:**

- **403 Forbidden** - Insufficient permissions:
```json
{
  "detail": "Not enough permissions"
}
```

- **400 Bad Request** - ISBN inconsistency:
```json
{
  "detail": "A book with ISBN 9780134685991 already exists with different title/author"
}
```

- **422 Validation Error** - Invalid ISBN format:
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "isbn"],
      "msg": "ISBN must be 10 or 13 digits"
    }
  ]
}
```

---

### 6. List All Books

Get a paginated list of all books in the library with optional filters.

**Endpoint:** `GET /books/`

**Authentication:** Required

**Permission:** `books:read` (Member and Librarian roles)

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `skip` | integer | 0 | Number of records to skip |
| `limit` | integer | 100 | Max records to return (max: 1000) |
| `search` | string | - | Search in title and author (case-insensitive) |
| `isbn` | string | - | Filter by exact ISBN |
| `available_only` | boolean | false | Show only available books |
| `sort` | string | - | Sort by: `title`, `author`, `created_at` (prefix `-` for descending) |

**cURL Examples:**

Get all books:
```bash
curl -X GET "http://localhost:8000/api/v1/books/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Get only available books:
```bash
curl -X GET "http://localhost:8000/api/v1/books/?available_only=true" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Search for books by title or author:
```bash
curl -X GET "http://localhost:8000/api/v1/books/?search=python" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Get books by ISBN:
```bash
curl -X GET "http://localhost:8000/api/v1/books/?isbn=9780134685991" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Success Response (200 OK):**
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "isbn": "9780134685991",
    "title": "The Pragmatic Programmer",
    "author": "David Thomas, Andrew Hunt",
    "is_available": true,
    "created_at": "2024-12-10T10:30:00Z"
  },
  {
    "id": "223e4567-e89b-12d3-a456-426614174001",
    "isbn": "9780134685991",
    "title": "The Pragmatic Programmer",
    "author": "David Thomas, Andrew Hunt",
    "is_available": false,
    "created_at": "2024-12-10T11:00:00Z"
  }
]
```

**Note:** Multiple books can have the same ISBN (multiple copies).

---

### 7. Get Book by ID

Get details of a specific book.

**Endpoint:** `GET /books/{book_id}`

**Authentication:** Required

**Permission:** `books:read`

**Path Parameters:**
- `book_id` (UUID): The unique identifier of the book

**cURL Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/books/123e4567-e89b-12d3-a456-426614174000" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Success Response (200 OK):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "isbn": "9780134685991",
  "title": "The Pragmatic Programmer",
  "author": "David Thomas, Andrew Hunt",
  "is_available": true,
  "created_at": "2024-12-10T10:30:00Z"
}
```

**Error Response:**

- **404 Not Found** - Book doesn't exist:
```json
{
  "detail": "Book not found"
}
```

---

### 8. Update Book

Update book details (ISBN, title, or author).

**Endpoint:** `PATCH /books/{book_id}`

**Authentication:** Required

**Permission:** `books:update` (Librarian role by default)

**Path Parameters:**
- `book_id` (UUID): The unique identifier of the book

**Request Body (JSON):**
```json
{
  "title": "The Pragmatic Programmer: 20th Anniversary Edition",
  "author": "David Thomas, Andrew Hunt"
}
```

**Note:** All fields are optional. Only include fields you want to update.

**cURL Example:**
```bash
curl -X PATCH "http://localhost:8000/api/v1/books/123e4567-e89b-12d3-a456-426614174000" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "The Pragmatic Programmer: 20th Anniversary Edition"
  }'
```

**Success Response (200 OK):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "isbn": "9780134685991",
  "title": "The Pragmatic Programmer: 20th Anniversary Edition",
  "author": "David Thomas, Andrew Hunt",
  "is_available": true,
  "created_at": "2024-12-10T10:30:00Z"
}
```

**Error Response:**

- **404 Not Found** - Book doesn't exist

---

### 9. Delete Book

Remove a book from the library.

**Endpoint:** `DELETE /books/{book_id}`

**Authentication:** Required

**Permission:** `books:delete` (Librarian role by default)

**Path Parameters:**
- `book_id` (UUID): The unique identifier of the book

**cURL Example:**
```bash
curl -X DELETE "http://localhost:8000/api/v1/books/123e4567-e89b-12d3-a456-426614174000" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Success Response (200 OK):**
```json
{
  "message": "Book deleted successfully"
}
```

**Error Response:**

- **404 Not Found** - Book doesn't exist

---

## Borrow Management

### 10. Borrow a Book

Borrow an available book on behalf of the current user.

**Endpoint:** `POST /borrows/`

**Authentication:** Required

**Permission:** `borrows:create` (Member and Librarian roles)

**Request Body (JSON):**
```json
{
  "book_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

**Business Rules:**
- Book must exist
- Book must be available (`is_available` = true)
- One book can only be borrowed by one user at a time
- User borrows the book for themselves (cannot borrow on behalf of others)

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/borrows/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "book_id": "123e4567-e89b-12d3-a456-426614174000"
  }'
```

**Success Response (200 OK):**
```json
{
  "id": "987e6543-e89b-12d3-a456-426614174999",
  "book_id": "123e4567-e89b-12d3-a456-426614174000",
  "borrower_id": "456e7890-e89b-12d3-a456-426614175555",
  "borrowed_at": "2024-12-10T14:30:00Z",
  "returned_at": null
}
```

**Error Responses:**

- **404 Not Found** - Book doesn't exist:
```json
{
  "detail": "Book not found"
}
```

- **400 Bad Request** - Book not available:
```json
{
  "detail": "Book is not available for borrowing"
}
```

---

### 11. Return a Borrowed Book

Return a book that was previously borrowed.

**Endpoint:** `POST /borrows/{borrow_id}/return`

**Authentication:** Required

**Permission:** `borrows:return` (Member and Librarian roles)

**Path Parameters:**
- `borrow_id` (UUID): The unique identifier of the borrow record

**Business Rules:**
- Borrow record must exist
- Book must not be already returned
- Only the borrower can return their own book

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/borrows/987e6543-e89b-12d3-a456-426614174999/return" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Success Response (200 OK):**
```json
{
  "id": "987e6543-e89b-12d3-a456-426614174999",
  "book_id": "123e4567-e89b-12d3-a456-426614174000",
  "borrower_id": "456e7890-e89b-12d3-a456-426614175555",
  "borrowed_at": "2024-12-10T14:30:00Z",
  "returned_at": "2024-12-10T16:45:00Z"
}
```

**Error Responses:**

- **404 Not Found** - Borrow record doesn't exist:
```json
{
  "detail": "Borrow record not found"
}
```

- **400 Bad Request** - Book already returned:
```json
{
  "detail": "Book has already been returned"
}
```

- **403 Forbidden** - Not the borrower:
```json
{
  "detail": "You can only return books you borrowed"
}
```

---

### 12. List My Borrow Records

Get a list of borrow records for the current user.

**Endpoint:** `GET /borrows/me`

**Authentication:** Required

**Permission:** `borrows:read` (Member and Librarian roles)

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `skip` | integer | 0 | Number of records to skip |
| `limit` | integer | 100 | Max records to return (max: 1000) |
| `active_only` | boolean | false | Show only unreturned books |
| `book_id` | UUID | - | Filter by specific book |
| `sort` | string | - | Sort by: `borrowed_at`, `returned_at` (prefix `-` for descending) |

**cURL Examples:**

Get all my borrows:
```bash
curl -X GET "http://localhost:8000/api/v1/borrows/me" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Get only active (unreturned) borrows:
```bash
curl -X GET "http://localhost:8000/api/v1/borrows/me?active_only=true" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Success Response (200 OK):**
```json
[
  {
    "id": "987e6543-e89b-12d3-a456-426614174999",
    "book_id": "123e4567-e89b-12d3-a456-426614174000",
    "borrower_id": "456e7890-e89b-12d3-a456-426614175555",
    "borrowed_at": "2024-12-10T14:30:00Z",
    "returned_at": null
  }
]
```

---

### 13. List All Borrow Records (Librarian)

Get a list of all borrow records in the system (librarian only).

**Endpoint:** `GET /borrows/`

**Authentication:** Required

**Permission:** `borrows:read_all` (Librarian role by default)

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `skip` | integer | 0 | Number of records to skip |
| `limit` | integer | 100 | Max records to return (max: 1000) |
| `active_only` | boolean | false | Show only unreturned books |
| `book_id` | UUID | - | Filter by specific book |
| `borrower_id` | UUID | - | Filter by specific borrower |
| `sort` | string | - | Sort by: `borrowed_at`, `returned_at` (prefix `-` for descending) |

**cURL Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/borrows/?active_only=true" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Success Response (200 OK):**
```json
[
  {
    "id": "987e6543-e89b-12d3-a456-426614174999",
    "book_id": "123e4567-e89b-12d3-a456-426614174000",
    "borrower_id": "456e7890-e89b-12d3-a456-426614175555",
    "borrowed_at": "2024-12-10T14:30:00Z",
    "returned_at": null
  }
]
```

---

### 14. Get Borrow Record by ID

Get details of a specific borrow record.

**Endpoint:** `GET /borrows/{borrow_id}`

**Authentication:** Required

**Permission:** `borrows:read` (own records) or `borrows:read_all` (all records)

**Path Parameters:**
- `borrow_id` (UUID): The unique identifier of the borrow record

**cURL Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/borrows/987e6543-e89b-12d3-a456-426614174999" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Success Response (200 OK):**
```json
{
  "id": "987e6543-e89b-12d3-a456-426614174999",
  "book_id": "123e4567-e89b-12d3-a456-426614174000",
  "borrower_id": "456e7890-e89b-12d3-a456-426614175555",
  "borrowed_at": "2024-12-10T14:30:00Z",
  "returned_at": "2024-12-10T16:45:00Z"
}
```

**Error Responses:**

- **404 Not Found** - Borrow record doesn't exist
- **403 Forbidden** - Cannot access other users' records without `borrows:read_all` permission

---

## Permission Management

### 15. Get User's Effective Permissions

Get the complete list of effective permissions for a user (role permissions + overrides).

**Endpoint:** `GET /users/{user_id}/permissions`

**Authentication:** Required

**Permission:** Self or Superuser only

**Path Parameters:**
- `user_id` (UUID): The unique identifier of the user

**cURL Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/users/456e7890-e89b-12d3-a456-426614175555/permissions" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Success Response (200 OK):**
```json
{
  "role": "member",
  "role_permissions": [
    "books:read",
    "borrows:create",
    "borrows:return",
    "borrows:read"
  ],
  "permission_overrides": [
    {
      "id": "111e2222-e89b-12d3-a456-426614173333",
      "permission": "books:create",
      "effect": "allow",
      "created_at": "2024-12-10T10:00:00Z"
    }
  ],
  "effective_permissions": [
    "books:read",
    "books:create",
    "borrows:create",
    "borrows:return",
    "borrows:read"
  ]
}
```

---

### 16. List Permission Overrides

Get all permission overrides for a specific user (superuser only).

**Endpoint:** `GET /users/{user_id}/permissions/overrides`

**Authentication:** Required

**Permission:** Superuser only

**Path Parameters:**
- `user_id` (UUID): The unique identifier of the user

**cURL Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/users/456e7890-e89b-12d3-a456-426614175555/permissions/overrides" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Success Response (200 OK):**
```json
[
  {
    "id": "111e2222-e89b-12d3-a456-426614173333",
    "user_id": "456e7890-e89b-12d3-a456-426614175555",
    "permission": "books:create",
    "effect": "allow",
    "created_at": "2024-12-10T10:00:00Z"
  }
]
```

---

### 17. Add Permission Override

Grant or deny a specific permission to a user (superuser only).

**Endpoint:** `POST /users/{user_id}/permissions/overrides`

**Authentication:** Required

**Permission:** Superuser only

**Path Parameters:**
- `user_id` (UUID): The unique identifier of the user

**Request Body (JSON):**
```json
{
  "permission": "books:create",
  "effect": "allow"
}
```

**Fields:**
- `permission` (required): Permission string (e.g., "books:create", "borrows:read_all")
- `effect` (required): Either "allow" or "deny"

**Permission Evaluation:**
- DENY overrides always take precedence over ALLOW
- Overrides are evaluated after role-based permissions

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/users/456e7890-e89b-12d3-a456-426614175555/permissions/overrides" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "permission": "books:create",
    "effect": "allow"
  }'
```

**Success Response (200 OK):**
```json
{
  "id": "111e2222-e89b-12d3-a456-426614173333",
  "user_id": "456e7890-e89b-12d3-a456-426614175555",
  "permission": "books:create",
  "effect": "allow",
  "created_at": "2024-12-10T10:00:00Z"
}
```

---

### 18. Delete Permission Override

Remove a permission override for a user (superuser only).

**Endpoint:** `DELETE /users/{user_id}/permissions/overrides/{override_id}`

**Authentication:** Required

**Permission:** Superuser only

**Path Parameters:**
- `user_id` (UUID): The unique identifier of the user
- `override_id` (UUID): The unique identifier of the permission override

**cURL Example:**
```bash
curl -X DELETE "http://localhost:8000/api/v1/users/456e7890-e89b-12d3-a456-426614175555/permissions/overrides/111e2222-e89b-12d3-a456-426614173333" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Success Response (200 OK):**
```json
{
  "message": "Permission override deleted successfully"
}
```

**Error Response:**

- **404 Not Found** - Override doesn't exist

---

## Complete User Journeys

### Journey 1: Member Registers and Borrows a Book

```bash
# Step 1: Register a new user
curl -X POST "http://localhost:8000/api/v1/users/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "member@example.com",
    "password": "securepass123",
    "full_name": "John Doe"
  }'

# Step 2: Login to get access token
TOKEN=$(curl -X POST "http://localhost:8000/api/v1/login/access-token" \
  -d "username=member@example.com&password=securepass123" \
  | jq -r '.access_token')

# Step 3: List available books
curl -X GET "http://localhost:8000/api/v1/books/?available_only=true" \
  -H "Authorization: Bearer $TOKEN"

# Step 4: Borrow a book (use book_id from step 3)
curl -X POST "http://localhost:8000/api/v1/borrows/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "book_id": "123e4567-e89b-12d3-a456-426614174000"
  }'

# Step 5: View my active borrows
curl -X GET "http://localhost:8000/api/v1/borrows/me?active_only=true" \
  -H "Authorization: Bearer $TOKEN"

# Step 6: Return the book (use borrow_id from step 4)
curl -X POST "http://localhost:8000/api/v1/borrows/987e6543-e89b-12d3-a456-426614174999/return" \
  -H "Authorization: Bearer $TOKEN"
```

### Journey 2: Librarian Manages Books

```bash
# Step 1: Login as librarian
TOKEN=$(curl -X POST "http://localhost:8000/api/v1/login/access-token" \
  -d "username=librarian@example.com&password=librarianpass" \
  | jq -r '.access_token')

# Step 2: Register a new book
BOOK_ID=$(curl -X POST "http://localhost:8000/api/v1/books/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "isbn": "978-0-13-468599-1",
    "title": "The Pragmatic Programmer",
    "author": "David Thomas, Andrew Hunt"
  }' | jq -r '.id')

# Step 3: Register another copy of the same book
curl -X POST "http://localhost:8000/api/v1/books/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "isbn": "978-0-13-468599-1",
    "title": "The Pragmatic Programmer",
    "author": "David Thomas, Andrew Hunt"
  }'

# Step 4: View all books with this ISBN
curl -X GET "http://localhost:8000/api/v1/books/?isbn=9780134685991" \
  -H "Authorization: Bearer $TOKEN"

# Step 5: View all active borrows in the system
curl -X GET "http://localhost:8000/api/v1/borrows/?active_only=true" \
  -H "Authorization: Bearer $TOKEN"

# Step 6: Update book details
curl -X PATCH "http://localhost:8000/api/v1/books/$BOOK_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "The Pragmatic Programmer: 20th Anniversary Edition"
  }'
```

---

## Interactive API Documentation

For interactive API testing, visit:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

Both interfaces provide:
- Complete API schema
- Request/response examples
- Try-it-out functionality
- Authentication support
- Schema validation

---

## Additional Resources

- [README.md](README.md) - Project overview and quick start
- [ASSUMPTIONS.md](ASSUMPTIONS.md) - Complete list of assumptions and design decisions
- [Deploy.md](Deploy.md) - Deployment guide
- [DATABASE.md](DATABASE.md) - Database design and justification
