#!/bin/bash
# Reset database (DANGER: Drops all data!)

set -e

echo "⚠️  WARNING: This will delete ALL data!"
read -p "Are you sure? (type 'yes' to confirm): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "❌ Aborted"
    exit 1
fi

cd "$(dirname "$0")/../.."

echo "🗑️  Dropping all tables..."
alembic downgrade base

echo "🔨 Running all migrations..."
alembic upgrade head

echo "✅ Database reset complete!"
