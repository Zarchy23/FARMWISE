"""
WSGI config for farmwise project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farmwise.settings')

# Ensure migrations run before application starts
# This is critical for custom User model to ensure tables exist
django.setup()

from django.core.management import call_command
from django.db import connection

# Run migrations if needed (only once per startup)
try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename='core_user'")
        if not cursor.fetchone():
            print("Running migrations to create database tables...")
            call_command('migrate', '--run-syncdb', '--noinput', verbosity=1)
            print("Migrations completed successfully.")
        else:
            print("Database tables already exist, skipping migrations.")
except Exception as e:
    print(f"Migration check failed: {e}")
    # Try running migrations anyway as fallback
    try:
        print("Attempting to run migrations as fallback...")
        call_command('migrate', '--run-syncdb', '--noinput', verbosity=1)
        print("Fallback migrations completed.")
    except Exception as fallback_error:
        print(f"Fallback migration failed: {fallback_error}")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
