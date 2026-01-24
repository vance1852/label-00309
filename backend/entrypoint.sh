#!/bin/bash
set -e

echo "Waiting for database..."
sleep 10

echo "Running migrations..."
python manage.py migrate --noinput

echo "Initializing data..."
python manage.py init_data || true

echo "Starting server..."
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2 --threads 4
