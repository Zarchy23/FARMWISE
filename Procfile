release: python manage.py migrate
web: gunicorn farmwise.wsgi:application --bind 0.0.0.0:8000 --workers 4
