#!/bin/bash
set -e

echo "=== RepoRadar Start ==="
echo "PORT=$PORT"
echo "DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE"
echo "DATABASE_URL is set: $([ -n "$DATABASE_URL" ] && echo 'yes' || echo 'NO')"

echo "=== Running migrations ==="
python manage.py migrate 2>&1

echo "=== Starting gunicorn on port $PORT ==="
exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --log-level info
