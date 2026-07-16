#!/bin/bash
set -e

echo "Running migrations (ensure database schema is up to date)..."
python manage.py migrate --run-syncdb --noinput || echo "Migrations may have already run"

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear || true

# Skip data loading on initial deployment to ensure schema is created first
# Data loading will be done manually after successful deployment
echo "Skipping automatic data loading on initial deployment..."

echo "Starting FarmWise..."
python -m gunicorn farmwise.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers 3 \
    --worker-class sync \
    --timeout 120
