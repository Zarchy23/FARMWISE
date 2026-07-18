#!/bin/bash
set -e

echo "Running migrations (ensure database schema is up to date)..."
python manage.py migrate --run-syncdb --noinput || echo "Migrations may have already run"

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear || true

# Force data loading for this deployment to ensure user accounts are available
echo "Loading production data (including user accounts)..."
if [ -f "production_data.json" ]; then
    python manage.py loaddata production_data.json || echo "Production data loaddata failed (continuing)"
else
    echo "production_data.json not found, skipping..."
fi

# Load additional data files if they exist
if [ -f "data.json" ]; then
    echo "Loading additional system data..."
    python manage.py loaddata data.json || echo "Additional data loaddata failed (continuing)"
fi

if [ -f "users_data.json" ]; then
    echo "Loading user accounts..."
    python manage.py loaddata users_data.json || echo "User accounts loaddata failed (continuing)"
fi

echo "Data loading completed."

echo "Starting FarmWise..."
echo "PORT environment variable: ${PORT:-8000}"

# Try to start with gunicorn, fallback to development server if it fails
python -m gunicorn farmwise.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers 1 \
    --worker-class sync \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - || \
    echo "Gunicorn failed, trying development server..." && \
    python manage.py runserver 0.0.0.0:${PORT:-8000}
