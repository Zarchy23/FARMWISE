"""
Context processors for FarmWise application.
These functions provide common data to all templates.
"""

from django.conf import settings


def site_settings(request):
    """
    Provide common site settings to all templates.
    """
    return {
        'site_name': 'FarmWise',
        'site_description': 'Agricultural Management Platform',
        'debug': settings.DEBUG,
        'environment': 'development' if settings.DEBUG else 'production',
        'version': '1.0.0',
    }
