"""
WSGI application shim for gunicorn compatibility.
Re-exports the Django WSGI application from farmwise.wsgi.
"""
from farmwise.wsgi import application

app = application
