release: python manage.py migrate --noinput && python manage.py collectstatic --noinput --clear
web: python -m gunicorn farmwise.wsgi:application --bind 0.0.0.0:$PORT --workers 3
