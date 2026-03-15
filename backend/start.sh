#!/bin/bash
set -e

echo "=== RepoRadar Start ==="
echo "PORT=$PORT"
echo "DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE"
echo "DATABASE_URL is set: $([ -n "$DATABASE_URL" ] && echo 'yes' || echo 'NO')"

# Download MaxMind GeoLite2-City DB for analytics GeoIP (if key is set)
if [ -n "$MAXMIND_LICENSE_KEY" ]; then
  echo "=== Downloading GeoLite2-City database ==="
  curl -sSL "https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-City&license_key=${MAXMIND_LICENSE_KEY}&suffix=tar.gz" \
    | tar -xz --strip-components=1 -C /app/ --wildcards '*.mmdb' 2>&1 \
    && echo "GeoLite2-City.mmdb downloaded" \
    || echo "WARNING: GeoLite2 download failed, falling back to ip-api.com"
fi

echo "=== Running migrations ==="
python manage.py migrate 2>&1

echo "=== Seeding ATS mappings ==="
python manage.py seed_ats_mappings 2>&1

echo "=== Seeding from aggregator (6500+ slugs) ==="
python manage.py seed_from_aggregator 2>&1

echo "=== Starting Celery worker in background ==="
celery -A config worker --beat -l info --concurrency=2 &
echo "Celery started (PID: $!)"

# Give Celery a moment to start, then queue job fetches
sleep 3
python -c "
import django; django.setup()
from apps.jobs.tasks import fetch_unfetched_mappings, fetch_remoteok_jobs, fetch_remotive_jobs, fetch_wwr_jobs, fetch_hn_hiring
fetch_unfetched_mappings.delay()
fetch_remoteok_jobs.delay()
fetch_remotive_jobs.delay()
fetch_wwr_jobs.delay()
fetch_hn_hiring.delay()
print('Queued all job fetch tasks')
" 2>&1

echo "=== Starting gunicorn on port $PORT ==="
exec gunicorn config.wsgi:application --bind [::]:${PORT:-8000} --log-level info
