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
    python src/initial_data.py

    echo "Prestart tasks completed!"
}

echo "Starting backend service..."
run_prestart
exec fastapi run --workers 4 src/main.py
