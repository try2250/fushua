#!/bin/bash
set -e

echo "Running database migrations..."
alembic upgrade head || {
    echo "Alembic migration failed, falling back to create_all..."
    python -c "from app.database import Base, engine; from app.models import *; Base.metadata.create_all(bind=engine)"
}

echo "Starting application..."
exec "$@"
