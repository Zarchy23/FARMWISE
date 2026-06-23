#!/bin/bash
set -e

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear || true

# Load initial data fixture once per machine (skip if already loaded)
MARKER="/tmp/.farmwise_data_loaded"
if [ ! -f "$MARKER" ] && [ -f "data.json" ]; then
    echo "Loading initial data fixture..."
    python manage.py loaddata data.json && touch "$MARKER" || echo "Loaddata skipped/failed (continuing)"
fi

echo "Starting FarmWise..."
python -m gunicorn farmwise.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers 3 \
    --worker-class sync \
    --timeout 120
