"""
WSGI config for farmwise project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farmwise.settings')

# Migrations and data loading are handled at deploy time by start.sh and the
# render.yaml buildCommand, not on WSGI import. Running subprocesses here would
# execute once per worker and slow down/destabilise startup.

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
