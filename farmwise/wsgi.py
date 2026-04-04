"""
WSGI config for farmwise project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os
import subprocess

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farmwise.settings')

# Run migrations at startup (needed for Render free tier where
# DATABASE_URL may not be available during the build phase)
if os.environ.get('DATABASE_URL') and os.environ.get('RENDER'):
    try:
        subprocess.run(
            ['python', 'manage.py', 'migrate', '--noinput'],
            check=True,
            timeout=120,
        )
    except Exception as e:
        print(f"Migration warning: {e}")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
