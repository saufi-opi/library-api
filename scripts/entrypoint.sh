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

# If the command is "run-server", we execute the prestart sequence and start uvicorn
if [ "$1" = 'run-server' ]; then
    echo "Starting backend service..."
    run_prestart
    exec uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
fi

# Otherwise, we just exec the passed command (e.g. for testing or debugging)
exec "$@"
