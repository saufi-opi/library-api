# Database Migration Scripts

Convenient scripts for managing database migrations with Alembic.

## Quick Start

### Create the Template Model Migration

```bash
./scripts/db/create_migration.sh "add template model"
```

Then review the generated file in `alembic/versions/` and run:

```bash
./scripts/db/migrate.sh
```

---

## Available Scripts

### 1. **Create Migration**

Generates a new migration file based on model changes.

```bash
./scripts/db/create_migration.sh "your message here"
```

**Example:**

```bash
./scripts/db/create_migration.sh "add template model"
```

---

### 2. **Run Migration**

Applies all pending migrations to the database.

```bash
./scripts/db/migrate.sh
```

---

### 3. **Check Status**

Shows current migration version and history.

```bash
./scripts/db/migration_status.sh
```

---

### 4. **Rollback**

Rolls back the last N migrations.

```bash
./scripts/db/rollback.sh
./scripts/db/rollback.sh 2
```

---

### 5. **Reset Database**

⚠️ **DANGER**: Drops all tables and recreates them.

```bash
./scripts/db/reset_db.sh
```

---

## Manual Commands

If you prefer to run Alembic directly:

```bash
cd backend

# Create migration
alembic revision --autogenerate -m "your message"

# Run migrations
alembic upgrade head

# Check status
alembic current

# View history
alembic history

# Rollback one migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision_id>

# Reset to beginning
alembic downgrade base
```

---

## Workflow Example

1. **Make model changes** (e.g., add Template model)
2. **Create migration**: `scripts\db\create_migration.bat "add template"`
3. **Review** the generated file in `alembic/versions/`
4. **Apply migration**: `scripts\db\migrate.bat`
5. **Verify**: `scripts\db\migration_status.bat`

---

## Troubleshooting

### "Target database is not up to date"

```bash
alembic stamp head
```

### View SQL without applying

```bash
alembic upgrade head --sql
```

### Force to specific version

```bash
alembic upgrade <revision_id>
```

---

## Tips

- Always review auto-generated migrations before applying
- Test migrations on a development database first
- Keep migrations in version control
- Never edit applied migrations
- Use descriptive migration messages
