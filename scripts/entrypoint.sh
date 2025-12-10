#!/bin/bash
set -e

run_prestart() {
    echo "Running prestart tasks..."

    echo "Waiting for database..."
    python src/pre_start.py

    # Run migrations
    echo "Running database migrations..."
    alembic upgrade head

    # Create initial data
    echo "Creating initial data..."
    python src/core/initial_data.py

    echo "Prestart tasks completed!"
}

echo "Starting backend service..."
run_prestart
exec uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
