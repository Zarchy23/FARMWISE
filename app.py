"""
WSGI application for Render deployment.
This file is required by Render's auto-detection.
"""
import os
import sys

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farmwise.settings')

# Import Django and get the WSGI application
import django
django.setup()

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

# Expose as 'app' for Render's gunicorn command
app = application
