#!/bin/bash
# Database initialization script
set -e

echo "Waiting for PostgreSQL to be ready..."
until pg_isready -h postgres -U postgres; do
  sleep 1
done

echo "Running migrations..."
cd /app
alembic upgrade head

echo "Seeding data..."
python seed.py

echo "Database initialization complete!"

