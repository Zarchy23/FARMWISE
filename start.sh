#!/bin/bash
set -e

echo "Starting FARMWISE application..."
echo "Python version: $(python --version)"
echo "================================"

# Run gunicorn with proper configuration
gunicorn farmwise.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --worker-class sync \
    --worker-connections 1000 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
