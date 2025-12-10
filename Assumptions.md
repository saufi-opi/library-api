# Library Management API - Assumptions and Design Decisions

This document details all assumptions and design decisions made for requirements that were not explicitly stated in the project task specification.

## Table of Contents

- [System Architecture](#system-architecture)
- [User Management](#user-management)
- [Book Management](#book-management)
- [Borrowing System](#borrowing-system)
- [Authentication & Security](#authentication--security)
- [API Design](#api-design)
- [Data Validation](#data-validation)
- [Performance & Scalability](#performance--scalability)
- [Testing Strategy](#testing-strategy)

---

## System Architecture

### 1. Technology Stack Choice

**Assumption:** Python with FastAPI was chosen

**Rationale:**
- **Development Speed:** FastAPI enables rapid development with automatic API documentation
- **Modern Python:** Leverages Python 3.12+ features (type hints, async/await)
- **Performance:** FastAPI is one of the fastest Python frameworks (comparable to Node.js/Go)
- **Developer Experience:** Excellent IDE support, automatic validation, clear error messages
- **Ecosystem:** Rich Python ecosystem for data processing, ML integration (future features)

**Trade-offs:**
- ✓ Faster development and iteration
- ✓ Better for data-heavy operations
- ✓ Easier to find Python developers
- ✗ Java/Spring Boot bonus points not earned
- ✗ Slightly lower raw performance than compiled languages

### 2. Database Choice: PostgreSQL

**Assumption:** PostgreSQL was chosen for data storage

**Rationale:**
- **ACID Compliance:** Critical for borrowing transactions (prevent double-borrowing)
- **Relational Model:** Natural fit for library domain (users, books, borrows)
- **Concurrent Access:** Excellent handling of multiple simultaneous borrows/returns
- **Mature Technology:** Proven reliability, extensive documentation
- **JSON Support:** Flexibility for future features (metadata, tags, etc.)
- **Open Source:** No licensing costs, community support

**Alternatives Considered:**
- MongoDB: Not suitable for transactional guarantees needed
- MySQL: Similar to PostgreSQL but weaker JSON support
- SQLite: Not suitable for production concurrent access

### 3. Caching Layer: Redis

**Assumption:** Redis is used for rate limiting

**Rationale:**
- **Performance:** In-memory storage for fast rate limit checks
- **Distributed:** Supports horizontal scaling across multiple API instances
- **TTL Support:** Automatic expiration of rate limit counters
- **Atomic Operations:** Prevents race conditions in rate limiting

**Alternatives Considered:**
- In-memory (local): Doesn't work with multiple API instances
- Database: Too slow for every request rate check

### 4. ORM Choice: SQLModel

**Assumption:** SQLModel was chosen over pure SQLAlchemy or other ORMs

**Rationale:**
- **Type Safety:** Full type hints with mypy validation
- **Single Source of Truth:** One model for both database and API schemas
- **Pydantic Integration:** Automatic validation and serialization
- **Developer Experience:** Less boilerplate, clearer intent
- **FastAPI Native:** Designed specifically for FastAPI

### 5. Containerization: Docker

**Assumption:** Docker is required for deployment

**Rationale:**
- **Environment Consistency:** Same behavior in dev, test, production
- **Dependency Isolation:** No system-level dependency conflicts
- **Easy Deployment:** Single command to start entire stack
- **Scalability:** Easy to add more API instances behind load balancer
- **CI/CD Integration:** Docker images can be built and deployed automatically

---

## User Management

### 6. User Terminology: "User" vs "Borrower"

**Assumption:** The system uses "User" terminology instead of "Borrower"

**Rationale:**
- **Flexibility:** Not all users are borrowers (librarians, admins)
- **Industry Standard:** "User" is more common in authentication systems
- **Role-Based:** User roles (member/librarian) better express capabilities
- **API Naming:** RESTful endpoints use `/users/` (standard practice)

**Note:** In documentation and API responses, members are referred to as "borrowers" when discussing the borrowing context.

### 7. User Roles: Two-Tier System

**Assumption:** System has two primary roles (Member, Librarian) + Superuser

**Rationale:**
- **Simplicity:** Minimal roles reduce complexity
- **Clear Separation:** Members borrow, librarians manage
- **Extensibility:** Permission overrides allow customization without new roles
- **Superuser:** Required for initial setup and permission management

**Future Extension:** Additional roles (e.g., "restricted member", "book curator") can be added by creating permission presets.

### 8. Self-Service Borrowing Only

**Assumption:** Users can only borrow books for themselves (not on behalf of others)

**Rationale:**
- **Task Ambiguity:** "On behalf of a borrower" interpreted as self-service
- **Accountability:** Clear tracking of who borrowed what
- **Simplicity:** No need for proxy borrowing logic
- **Librarian Workflow:** If librarians need to borrow for patrons, they can:
  1. Create temporary account for patron
  2. Login as patron to borrow
  3. Or: Future feature for "assisted borrowing"

**Alternative Interpretation:** If "on behalf of" means librarian-assisted borrowing, this can be added by:
- Adding `borrower_id` parameter to borrow endpoint (optional, librarian-only)
- Allowing librarians with `borrows:create_on_behalf` permission to specify borrower

### 9. Single Role Per User

**Assumption:** Each user has exactly one role (member OR librarian)

**Rationale:**
- **Clarity:** Clear permission sets per user
- **Database Design:** Single `role` column (enum type)
- **Permission System:** Role provides base permissions, overrides handle exceptions
- **Real-World Model:** Library staff are either members or librarians, rarely both

**Override Mechanism:** If a librarian needs member-only restrictions, use permission overrides to deny specific actions.

### 10. User Full Name is Optional

**Assumption:** User's `full_name` field is optional (nullable)

**Rationale:**
- **Privacy:** Some users may prefer minimal personal information
- **Email Requirement:** Email is sufficient for authentication
- **Registration Flow:** Faster signup without forcing name entry
- **Flexibility:** Name can be added later via profile update

**Alternative:** Could be made required if library policy mandates it.

### 11. No Email Verification

**Assumption:** Email addresses are not verified (no confirmation email sent)

**Rationale:**
- **Task Scope:** Email verification not mentioned in requirements
- **Implementation:** `emails` library is present but not used
- **Future Feature:** Easy to add email verification flow later
- **Current State:** Users can immediately use their account after signup

**Security Consideration:** In production, email verification is recommended to:
- Prevent fake accounts
- Ensure password reset capability
- Verify user identity

### 12. No Password Reset Flow

**Assumption:** No "forgot password" functionality implemented

**Rationale:**
- **Task Scope:** Not mentioned in requirements
- **Complexity:** Requires email sending, token generation, expiration logic
- **Workaround:** Superusers can manually reset passwords via admin endpoint
- **Future Feature:** Can be added using `emails` library

---

## Book Management

### 13. ISBN Consistency Enforcement

**Assumption:** Books with identical ISBN must have matching title and author

**Rationale:**
- **ISBN Definition:** ISBN is a unique identifier for a specific publication
- **Data Integrity:** Prevents cataloging errors
- **Real-World Accuracy:** Reflects how ISBNs actually work
- **Query Reliability:** Users can search by ISBN and get consistent results

**Implementation:**
- Validation runs on book creation
- Searches for existing books with same ISBN
- Rejects if title/author mismatch
- Allows multiple copies with same ISBN (different book IDs)

**Edge Case:** Different editions (e.g., hardcover vs paperback) have different ISBNs, so this is handled correctly.

### 14. Multiple Copies Allowed

**Assumption:** Libraries can register multiple physical copies of the same book

**Rationale:**
- **Real-World Need:** Libraries own multiple copies of popular books
- **Different IDs:** Each physical copy gets a unique book ID
- **Individual Tracking:** Track which specific copy is borrowed
- **Availability:** One copy borrowed doesn't affect others

**Database Design:**
- `isbn` column is indexed but NOT unique
- Each row = one physical book copy
- `id` (UUID) is the unique identifier for each copy

**Example:**
```
id                                   isbn            title               is_available
123e4567-e89b-12d3-a456-426614174000 9780134685991   Pragmatic Programmer  false (borrowed)
223e4567-e89b-12d3-a456-426614174001 9780134685991   Pragmatic Programmer  true  (available)
```

### 15. ISBN Format Support

**Assumption:** Both ISBN-10 and ISBN-13 formats are accepted

**Rationale:**
- **Legacy Support:** Older books use ISBN-10
- **Modern Standard:** Newer books use ISBN-13
- **User Convenience:** Accept both without requiring conversion
- **Normalization:** Hyphens and spaces automatically removed

**Validation Rules:**
- ISBN-10: Exactly 10 digits (last can be 'X')
- ISBN-13: Exactly 13 digits
- Max 20 characters (allows for hyphens in input)
- Stored normalized (digits only)

### 16. No Book Categories/Genres

**Assumption:** Books don't have categories, tags, or genres

**Rationale:**
- **Task Scope:** Not mentioned in requirements
- **Simplicity:** Keep initial version minimal
- **Search:** Title and author search is sufficient for MVP
- **Future Feature:** Can add `genre`, `tags`, `categories` columns later

**Workaround:** Search by title or author to find related books.

### 17. No Book Deletion Restrictions

**Assumption:** Books can be deleted even if they have borrow history

**Rationale:**
- **Task Scope:** Deletion rules not specified
- **Current Implementation:** Books can be deleted freely
- **Data Integrity:** Foreign key constraints would prevent deletion if borrows exist

**Better Practice (Future):**
- Implement soft delete (mark as deleted, keep record)
- Prevent deletion of books with active borrows
- Allow deletion only if no borrow history exists

### 18. Book Availability is Binary

**Assumption:** Books are either available or unavailable (no "reserved", "damaged", etc.)

**Rationale:**
- **Simplicity:** Binary state is easier to manage
- **Task Scope:** Only borrowing/returning mentioned
- **Implementation:** Single `is_available` boolean flag
- **Automatic Update:** Set to `false` on borrow, `true` on return

**Future Extension:** Could add status enum: available, borrowed, reserved, damaged, lost, etc.

---

## Borrowing System

### 19. No Borrow Duration/Due Dates

**Assumption:** Books can be borrowed indefinitely (no due dates or late fees)

**Rationale:**
- **Task Scope:** Duration not mentioned in requirements
- **Simplicity:** No need for date calculations, overdue notifications
- **Data Model:** `borrow_at` and `returned_at` timestamps recorded
- **Flexibility:** Easy to add duration limits later

**Future Extension:**
- Add `due_date` column
- Add `overdue_fees` calculation
- Add notification system for overdue books
- Add auto-return after extreme delays

### 20. Only Borrower Can Return

**Assumption:** Users can only return books they personally borrowed

**Rationale:**
- **Security:** Prevent unauthorized returns
- **Accountability:** Clear tracking of who had the book
- **Real-World Model:** Libraries track who returns books
- **Permission Check:** `borrower_id` must match current user

**Exception:** Librarians with `borrows:return_any` permission could be allowed to return on behalf of users (not currently implemented).

### 21. No Reservation System

**Assumption:** Books cannot be reserved in advance

**Rationale:**
- **Task Scope:** Reservation not mentioned
- **Simplicity:** First-come, first-served model
- **Current Flow:** Check availability → borrow immediately
- **Future Feature:** Add reservation queue system

**Workaround:** Users must check periodically for availability.

### 22. Complete Borrow History Retained

**Assumption:** All borrow records are kept permanently (never deleted)

**Rationale:**
- **Audit Trail:** Complete history for accountability
- **Analytics:** Future reports on borrowing patterns
- **User History:** Users can see their full borrowing history
- **Data Integrity:** Soft deletes maintain referential integrity

**Storage Consideration:** Old records could be archived after N years if needed.

### 23. No Simultaneous Borrowing Limit

**Assumption:** Users can borrow unlimited books simultaneously

**Rationale:**
- **Task Scope:** Limits not mentioned
- **Flexibility:** Different libraries have different policies
- **Implementation:** No check on number of active borrows per user
- **Future Feature:** Add `max_active_borrows` setting per role

**Easy to Add:**
```python
active_borrows = session.query(BorrowRecord).filter(
    BorrowRecord.borrower_id == user.id,
    BorrowRecord.returned_at.is_(None)
).count()
if active_borrows >= MAX_BORROWS:
    raise TooManyActiveBorrowsError()
```

### 24. No Renewal System

**Assumption:** Borrowed books cannot be renewed (extended)

**Rationale:**
- **Task Scope:** Renewal not mentioned
- **Current Flow:** Return → Re-borrow if available
- **Simplicity:** Avoid complex renewal logic
- **Future Feature:** Add renewal endpoint

**Workaround:** Return and immediately borrow again (if still available).

---

## Authentication & Security

### 25. JWT Token Expiration

**Assumption:** Access tokens expire after 60 minutes

**Rationale:**
- **Security:** Limited window for token theft/misuse
- **Balance:** Long enough to avoid constant re-login, short enough for security
- **Configurable:** Set via `ACCESS_TOKEN_EXPIRE_MINUTES` in `.env`
- **No Refresh Tokens:** Users must re-login after expiration

**Alternative:** Could implement refresh tokens for longer sessions.

### 26. Password Requirements

**Assumption:** Passwords must be 8-40 characters (no complexity requirements)

**Rationale:**
- **Length Over Complexity:** Modern security best practice
- **User Experience:** Easier to remember longer passwords
- **No Special Chars Required:** Avoids user frustration
- **Hashed Storage:** Bcrypt hashing protects stored passwords

**Future Enhancement:** Add optional password strength indicator (client-side).

### 27. No Account Lockout

**Assumption:** No lockout after failed login attempts

**Rationale:**
- **Task Scope:** Security details not specified
- **Trade-off:** Simpler implementation vs. brute-force protection
- **Rate Limiting:** Login endpoints limited to 5 requests/60 seconds
- **Future Feature:** Add account lockout after N failed attempts

**Current Protection:** Rate limiting provides basic brute-force defense.

### 28. Superuser Creation

**Assumption:** First superuser is created automatically on startup

**Rationale:**
- **Bootstrap Problem:** Need initial user to create other users
- **Environment Config:** Credentials set in `.env` file
- **Production Safety:** Change default password immediately
- **One-Time Operation:** Only creates if no superuser exists

**Security Warning:** Default credentials (`admin@example.com` / `changethis`) must be changed in production.

### 29. Permission Override System

**Assumption:** Individual permissions can be granted/denied per user (Django/AWS IAM style)

**Rationale:**
- **Flexibility:** Handle exceptional cases without creating new roles
- **Granular Control:** Grant single permission without full role promotion
- **Deny Wins:** Explicit denies override any allows (security-first)
- **Audit Trail:** Permission changes are timestamped and logged

**Use Cases:**
- Grant `books:create` to a trusted member (without making them librarian)
- Deny `borrows:create` to a member with too many overdue books
- Temporary elevation of permissions

---

## API Design

### 30. RESTful API Design

**Assumption:** API follows REST principles

**Rationale:**
- **Industry Standard:** Familiar to most developers
- **HTTP Methods:** GET (read), POST (create), PATCH (update), DELETE (delete)
- **Resource-Oriented:** URLs represent resources (`/books/{id}`)
- **Stateless:** Each request contains all necessary information
- **JSON Format:** Standard data interchange format

**Alternatives Considered:**
- GraphQL: Overkill for simple CRUD operations
- RPC: Less standard, harder to cache

### 31. API Versioning

**Assumption:** API is versioned with `/api/v1` prefix

**Rationale:**
- **Future-Proofing:** Can introduce `/api/v2` with breaking changes
- **Backward Compatibility:** Old clients continue working
- **Clear Contract:** Version in URL makes it explicit
- **Best Practice:** Industry-standard approach

**Migration Path:** When v2 is needed, maintain v1 for deprecation period.

### 32. Pagination Defaults

**Assumption:** Default pagination returns 100 items, max 1000

**Rationale:**
- **Performance:** Limit data transferred in single request
- **User Experience:** 100 items is reasonable default page size
- **Flexibility:** Clients can adjust with `skip` and `limit` parameters
- **Protection:** Max 1000 prevents abuse (requesting millions of records)

**Endpoints Affected:** All list endpoints (`/books/`, `/borrows/`, `/users/`)

### 33. Filtering and Sorting

**Assumption:** List endpoints support filtering and sorting

**Rationale:**
- **User Experience:** Find specific items without client-side filtering
- **Performance:** Database indexes make this efficient
- **Flexibility:** Multiple filter parameters can be combined
- **Standard Practice:** Expected behavior for list APIs

**Examples:**
- `/books/?available_only=true` - Only available books
- `/books/?search=python` - Search title/author
- `/books/?sort=-created_at` - Newest first

### 34. Error Response Format

**Assumption:** Errors return consistent JSON format with `detail` field

**Rationale:**
- **Consistency:** All errors have same structure
- **Client Parsing:** Easy to extract error message
- **FastAPI Default:** Matches FastAPI's built-in error format
- **HTTP Status Codes:** Proper codes (400, 401, 403, 404, 500)

**Format:**
```json
{
  "detail": "Human-readable error message"
}
```

### 35. Rate Limiting

**Assumption:** Rate limiting is applied per endpoint category

**Rationale:**
- **Abuse Prevention:** Prevent API flooding
- **Resource Protection:** Limit database load
- **Tiered Limits:** Login (5/min) vs general (60/min)
- **Redis Backend:** Distributed rate limiting across instances

**Disabled in Testing:** `ENVIRONMENT=testing` disables rate limits for tests.

---

## Data Validation

### 36. Input Validation

**Assumption:** All request data is validated with Pydantic schemas

**Rationale:**
- **Type Safety:** Automatic type coercion and validation
- **Clear Errors:** Detailed validation error messages
- **API Documentation:** Schemas auto-generate API docs
- **Security:** Prevents injection attacks, malformed data

**Validation Rules:**
- Email format validation
- Password length (8-40 chars)
- ISBN format (10 or 13 digits)
- UUID format for IDs
- String length limits (prevent abuse)

### 37. ISBN Normalization

**Assumption:** ISBNs are normalized (hyphens/spaces removed) before storage

**Rationale:**
- **Consistency:** All ISBNs stored in same format
- **Search Efficiency:** Exact match queries work reliably
- **User Flexibility:** Accept various input formats
- **Display Format:** Can be reformatted for display if needed

**Example:**
- Input: `978-0-13-468599-1`
- Stored: `9780134685991`

### 38. Field Length Limits

**Assumption:** Text fields have maximum lengths

**Rationale:**
- **Database Efficiency:** VARCHAR with limits uses less space
- **Abuse Prevention:** Prevent extremely long inputs
- **Reasonable Limits:** Chosen based on real-world use

**Limits:**
- Email: 255 chars (standard)
- Full name: 255 chars
- Book title: 500 chars (handles long academic titles)
- Book author: 255 chars (multiple authors fit)
- ISBN: 20 chars (allows hyphens in input)

---

## Performance & Scalability

### 39. Database Indexing

**Assumption:** Key columns are indexed for performance

**Rationale:**
- **Query Performance:** Fast lookups on common queries
- **Indexes Added:**
  - User email (unique index)
  - Book ISBN (non-unique index)
  - Foreign keys (automatic)

**Future Indexes:**
- Full-text search on book title/author
- Compound index on (borrower_id, returned_at)

### 40. Connection Pooling

**Assumption:** Database connection pool is configured

**Rationale:**
- **Performance:** Reuse connections instead of creating new ones
- **Resource Management:** Limit total connections to database
- **Configuration:**
  - Pool size: 5 base connections
  - Max overflow: 10 additional connections
  - Pre-ping: Verify connections are alive

### 41. Async/Await

**Assumption:** API uses asynchronous request handling

**Rationale:**
- **Concurrency:** Handle multiple requests simultaneously
- **I/O Efficiency:** Don't block on database/network operations
- **Scalability:** More requests per server instance
- **FastAPI Native:** Framework designed for async

**Note:** Database operations are synchronous (SQLModel), but FastAPI handles this efficiently with thread pools.

### 42. Horizontal Scaling

**Assumption:** Multiple API instances can run behind a load balancer

**Rationale:**
- **Stateless Design:** No session state stored in API server
- **Shared Database:** All instances connect to same PostgreSQL
- **Shared Cache:** All instances connect to same Redis
- **Docker Support:** Easy to spin up multiple containers

**Load Balancer:** Traefik is configured in `docker-compose.yml`.

---

## Testing Strategy

### 43. Comprehensive Test Coverage

**Assumption:** All endpoints and business logic have automated tests

**Rationale:**
- **Quality Assurance:** Catch bugs before production
- **Refactoring Safety:** Tests ensure changes don't break functionality
- **Documentation:** Tests serve as usage examples
- **CI/CD Integration:** Automated testing on every commit

**Test Types:**
- Unit tests: Business logic functions
- Integration tests: API endpoints with database
- Edge case tests: Error conditions, validation failures

### 44. Test Database Isolation

**Assumption:** Tests use isolated test database with cleanup

**Rationale:**
- **Reproducibility:** Each test runs with clean state
- **Parallel Execution:** Tests can run simultaneously
- **No Side Effects:** Tests don't affect each other
- **Auto-Cleanup:** Database reset after each test module

**Implementation:**
- Separate test database
- Transactions rolled back after tests
- Test fixtures for common data

### 45. Rate Limiting Disabled in Tests

**Assumption:** Rate limiting is disabled when `ENVIRONMENT=testing`

**Rationale:**
- **Test Speed:** Don't wait for rate limit windows
- **Reliability:** Tests don't fail due to rate limits
- **Focus:** Test business logic, not rate limiting
- **Configuration:** Environment-aware feature flag

**Rate Limiting Tests:** Separate tests verify rate limiting works in non-test environment.

---

## Summary

These assumptions represent design decisions made to create a complete, production-ready library management system. While some features (email verification, due dates, reservations) were left out of the initial implementation, the architecture supports future extension.

The design prioritizes:
- ✅ **Simplicity:** Start with essential features
- ✅ **Security:** Authentication, authorization, validation
- ✅ **Reliability:** ACID transactions, error handling
- ✅ **Maintainability:** Clean code, comprehensive tests
- ✅ **Scalability:** Stateless design, caching, async operations
- ✅ **User Experience:** Clear errors, fast responses, flexible API

All assumptions can be revisited based on real-world usage and feedback.
