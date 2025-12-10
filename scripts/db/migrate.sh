#!/bin/bash
# Run database migrations

set -e

echo "🚀 Running database migrations..."

cd "$(dirname "$0")/../.."

# Run migrations
alembic upgrade head

echo "✅ Database migrated successfully!"
