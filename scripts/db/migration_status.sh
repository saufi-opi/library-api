#!/bin/bash
# Check migration status

set -e

cd "$(dirname "$0")/../.."

echo "📊 Database Migration Status"
echo "============================"
echo ""

echo "Current Migration:"
alembic current
echo ""

echo "Migration History:"
alembic history --verbose
