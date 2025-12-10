#!/bin/bash
# Rollback database migration

set -e

STEPS="${1:-1}"

echo "⏪ Rolling back $STEPS migration(s)..."

cd "$(dirname "$0")/../.."

# Rollback
alembic downgrade -$STEPS

echo "✅ Rollback completed!"
echo ""
echo "Current migration:"
alembic current
