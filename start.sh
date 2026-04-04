#!/bin/bash
set -e

echo "Starting FarmWise..."
python -m gunicorn farmwise.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers 3 \
    --worker-class sync \
    --timeout 120
