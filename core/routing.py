# core/routing.py
# WebSocket URL routing for Django Channels

from django.urls import re_path
from core.consumers import (
    DashboardConsumer,
    AlertStreamConsumer,
    NotificationConsumer,
)

# WebSocket URL patterns for channels
websocket_urlpatterns = [
    # Real-time dashboard - ws://domain/ws/dashboard/farm_id/
    re_path(
        r'ws/dashboard/(?P<farm_id>\w+)/$',
        DashboardConsumer.as_asgi(),
        name='dashboard-ws'
    ),
    
    # Alert stream - ws://domain/ws/alerts/
    re_path(
        r'ws/alerts/$',
        AlertStreamConsumer.as_asgi(),
        name='alerts-ws'
    ),
    
    # Notifications stream - ws://domain/ws/notifications/
    re_path(
        r'ws/notifications/$',
        NotificationConsumer.as_asgi(),
        name='notifications-ws'
    ),
]
