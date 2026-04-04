release: python manage.py migrate --noinput
web: gunicorn farmwise.wsgi:application --bind 0.0.0.0:8000 --workers 4 --worker-class sync --timeout 90
