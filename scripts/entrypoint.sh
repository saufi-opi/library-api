#!/bin/bash
set -e

# Function to run prestart tasks
run_prestart() {
    echo "Running prestart tasks..."

    # Wait for DB to be ready
    echo "Waiting for database..."
    python src/backend_pre_start.py

    # Run migrations
    echo "Running database migrations..."
    alembic upgrade head

    # Create initial data
    echo "Creating initial data..."
    python src/initial_data.py

    echo "Prestart tasks completed!"
}

# Determine which service to run
case "$1" in
    backend)
        echo "Starting backend service..."
        run_prestart
        exec fastapi run --workers 4 src/main.py
        ;;
    celery-worker)
        echo "Starting Celery worker..."
        exec celery -A src.celery_app worker --loglevel=info
        ;;
    celery-beat)
        echo "Starting Celery beat..."
        exec celery -A src.celery_app beat --loglevel=info
        ;;
    *)
        echo "Usage: $0 {backend|celery-worker|celery-beat}"
        exit 1
        ;;
esac
