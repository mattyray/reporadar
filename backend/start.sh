#!/bin/bash
set -e

echo "=== RepoRadar Start ==="
echo "PORT=$PORT"
echo "DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE"
echo "DATABASE_URL is set: $([ -n "$DATABASE_URL" ] && echo 'yes' || echo 'NO')"

echo "=== Running migrations ==="
python manage.py migrate 2>&1

echo "=== Seeding ATS mappings (fetch runs in background) ==="
python manage.py seed_ats_mappings 2>&1

echo "=== Starting Celery worker in background ==="
celery -A config worker --beat -l info --concurrency=2 &
echo "Celery started (PID: $!)"

# Give Celery a moment to start, then fetch jobs for any unfetched seed mappings
sleep 3
python -c "
import django; django.setup()
from apps.jobs.tasks import fetch_unfetched_mappings
fetch_unfetched_mappings.delay()
print('Queued fetch_unfetched_mappings task')
" 2>&1

echo "=== Starting gunicorn on port $PORT ==="
exec gunicorn config.wsgi:application --bind [::]:${PORT:-8000} --log-level info
