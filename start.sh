#!/bin/bash
set -e

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear || true

# Load initial data fixture once per machine (skip if already loaded)
MARKER="/tmp/.farmwise_data_loaded"
if [ ! -f "$MARKER" ]; then
    echo "Checking for initial data fixtures..."
    # Load data.json if it exists (contains system data)
    if [ -f "data.json" ]; then
        echo "Loading initial data fixture..."
        python manage.py loaddata data.json || echo "Loaddata skipped/failed (continuing)"
    fi
    
    # Load user accounts fixture if it exists (contains user accounts)
    if [ -f "users_data.json" ]; then
        echo "Loading user accounts fixture..."
        python manage.py loaddata users_data.json || echo "User accounts loaddata skipped/failed (continuing)"
    fi
    
    # Load production data if it exists (contains local to production migration data)
    if [ -f "production_data.json" ]; then
        echo "Loading production data fixture..."
        python manage.py loaddata production_data.json || echo "Production data loaddata skipped/failed (continuing)"
    fi
    
    touch "$MARKER"
fi

echo "Starting FarmWise..."
python -m gunicorn farmwise.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers 3 \
    --worker-class sync \
    --timeout 120
