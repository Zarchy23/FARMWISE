"""
Context processors for FarmWise application.
These functions provide common data to all templates.
"""

from django.conf import settings
from .models import Notification


def site_settings(request):
    """
    Provide common site settings to all templates.
    """
    context = {
        'site_name': 'FarmWise',
        'site_description': 'Agricultural Management Platform',
        'debug': settings.DEBUG,
        'environment': 'development' if settings.DEBUG else 'production',
        'version': '1.0.0',
    }
    
    # Add notification data for authenticated users
    if request.user.is_authenticated:
        unread_notifications = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        
        recent_notifications = Notification.objects.filter(
            user=request.user
        ).order_by('-created_at')[:5]
        
        context['unread_notifications'] = unread_notifications
        context['recent_notifications'] = recent_notifications
    else:
        context['unread_notifications'] = 0
        context['recent_notifications'] = []
    
    return context
