#!/bin/bash
# Create a new database migration

set -e

if [ -z "$1" ]; then
    echo "❌ Error: Migration message required"
    echo "Usage: ./create_migration.sh 'your migration message'"
    exit 1
fi

MESSAGE="$1"

echo "📝 Creating migration: $MESSAGE"

cd "$(dirname "$0")/../.."

# Create migration with autogenerate
alembic revision --autogenerate -m "$MESSAGE"

echo "✅ Migration created successfully!"
echo "📁 Check: alembic/versions/"
echo ""
echo "Next steps:"
echo "  1. Review the generated migration file"
echo "  2. Run: ./scripts/migrate.sh"
