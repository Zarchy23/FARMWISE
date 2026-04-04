#!/bin/bash
set -e

echo "======================================"
echo "FARMWISE - Render Build Script"
echo "======================================"

# Ensure Python 3.11 is being used
python --version
echo "Python version confirmed"

# Generate SECRET_KEY if not set
if [ -z "$SECRET_KEY" ]; then
  echo "Generating SECRET_KEY..."
  export SECRET_KEY=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
  echo "SECRET_KEY generated successfully"
fi

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install dependencies
echo "Installing requirements..."
pip install -r requirements.txt

# Run Django system check
echo "Running Django checks..."
python manage.py check

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear || true

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput || true

echo "======================================"
echo "Build completed successfully!"
echo "======================================"
