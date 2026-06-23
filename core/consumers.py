# core/consumers.py
# FARMWISE Real-Time WebSocket Consumers
# Handles WebSocket connections for real-time dashboard, alerts, and notifications

import json
import logging
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from decimal import Decimal

logger = logging.getLogger(__name__)


# ============================================================
# DASHBOARD CONSUMER - Real-Time Metrics & Updates
# ============================================================

class DashboardConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time dashboard updates.
    
    Broadcast: dashboard_updates -> sends metrics, weather, alerts, notifications
    """
    
    async def connect(self):
        """Accept WebSocket connection and join dashboard group"""
        self.user = self.scope['user']
        self.farm_id = self.scope['url_route']['kwargs'].get('farm_id')
        
        # Validate user is authenticated
        if self.user.is_anonymous:
            await self.close(code=4001)
            return
        
        # Create channel name for this user's dashboard
        self.dashboard_group_name = f'dashboard_{self.user.id}_{self.farm_id}'
        
        # Join the group
        await self.channel_layer.group_add(
            self.dashboard_group_name,
            self.channel_name
        )
        
        logger.info(f"User {self.user.username} connected to dashboard for farm {self.farm_id}")
        await self.accept()
        
        # Send initial dashboard data
        await self.send_initial_data()
    
    async def disconnect(self, close_code):
        """Remove user from dashboard group on disconnect"""
        if hasattr(self, 'dashboard_group_name'):
            await self.channel_layer.group_discard(
                self.dashboard_group_name,
                self.channel_name
            )
            logger.info(f"User {self.user.username} disconnected from dashboard")
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'request_metrics':
                await self.send_metrics_update()
            elif message_type == 'request_alerts':
                await self.send_alerts_update()
            elif message_type == 'request_weather':
                await self.send_weather_update()
            elif message_type == 'request_notifications':
                await self.send_notifications_update()
            elif message_type == 'mark_notification_read':
                await self.mark_notification_as_read(data.get('notification_id'))
            elif message_type == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received: {text_data}")
        except Exception as e:
            logger.error(f"Error in WebSocket receive: {str(e)}")
    
    # ========================================
    # Send Methods (to WebSocket)
    # ========================================
    
    async def send_initial_data(self):
        """Send all initial dashboard data to client"""
        metrics = await self.get_latest_metrics()
        alerts = await self.get_active_alerts()
        notifications = await self.get_unread_notifications()
        weather = await self.get_weather_forecast()
        
        await self.send(text_data=json.dumps({
            'type': 'initial_data',
            'metrics': metrics,
            'alerts': alerts,
            'notifications': notifications,
            'weather': weather,
        }))
    
    async def send_metrics_update(self):
        """Send latest metrics to client"""
        metrics = await self.get_latest_metrics()
        await self.send(text_data=json.dumps({
            'type': 'metrics_update',
            'data': metrics,
        }))
    
    async def send_alerts_update(self):
        """Send active alerts to client"""
        alerts = await self.get_active_alerts()
        await self.send(text_data=json.dumps({
            'type': 'alerts_update',
            'data': alerts,
        }))
    
    async def send_weather_update(self):
        """Send weather forecast to client"""
        weather = await self.get_weather_forecast()
        await self.send(text_data=json.dumps({
            'type': 'weather_update',
            'data': weather,
        }))
    
    async def send_notifications_update(self):
        """Send unread notifications to client"""
        notifications = await self.get_unread_notifications()
        await self.send(text_data=json.dumps({
            'type': 'notifications_update',
            'data': notifications,
        }))
    
    async def send_performance_update(self):
        """Broadcast method - send performance score updates"""
        performance = await self.get_farm_performance()
        await self.send(text_data=json.dumps({
            'type': 'performance_update',
            'data': performance,
        }))
    
    async def send_alert_notification(self, event):
        """Broadcast method - send new alert to dashboard"""
        await self.send(text_data=json.dumps({
            'type': 'new_alert',
            'data': event.get('data'),
        }))
    
    async def send_metric_update(self, event):
        """Broadcast method - send real-time metric update"""
        await self.send(text_data=json.dumps({
            'type': 'metric_stream',
            'data': event.get('data'),
        }))
    
    # ========================================
    # Database Query Methods
    # ========================================
    
    @database_sync_to_async
    def get_latest_metrics(self):
        """Fetch latest metrics for the farm"""
        from core.models_analytics import DashboardMetric
        
        metrics = DashboardMetric.objects.filter(
            user=self.user,
            farm_id=self.farm_id
        ).order_by('-timestamp')[:20]
        
        data = []
        for metric in metrics:
            data.append({
                'id': metric.id,
                'type': metric.metric_type,
                'value': float(metric.value),
                'unit': metric.unit,
                'severity': metric.severity,
                'timestamp': metric.timestamp.isoformat(),
            })
        
        return data
    
    @database_sync_to_async
    def get_active_alerts(self):
        """Fetch active (unresolved) alerts"""
        from core.models_analytics import AlertTrigger
        
        alerts = AlertTrigger.objects.filter(
            user=self.user,
            farm_id=self.farm_id,
            is_resolved=False
        ).order_by('-importance', '-created_at')[:10]
        
        data = []
        for alert in alerts:
            data.append({
                'id': alert.id,
                'type': alert.alert_type,
                'importance': alert.importance,
                'title': alert.title,
                'description': alert.description,
                'recommendations': alert.recommended_actions,
                'created_at': alert.created_at.isoformat(),
            })
        
        return data
    
    @database_sync_to_async
    def get_unread_notifications(self):
        """Fetch unread notifications"""
        from core.models_analytics import NotificationQueue
        
        notifications = NotificationQueue.objects.filter(
            user=self.user,
            is_read=False,
            is_sent=True
        ).order_by('-created_at')[:20]
        
        data = []
        for notif in notifications:
            data.append({
                'id': notif.id,
                'type': notif.notification_type,
                'title': notif.title,
                'message': notif.message,
                'severity': notif.severity,
                'icon': notif.icon,
                'created_at': notif.created_at.isoformat(),
            })
        
        return data
    
    @database_sync_to_async
    def get_weather_forecast(self):
        """Fetch weather forecast for farm location"""
        from core.models import Farm
        from core.services.weather_service import WeatherService
        
        try:
            farm = Farm.objects.get(id=self.farm_id, user=self.user)
            
            # Use existing weather service
            weather_service = WeatherService()
            weather_data = weather_service.get_forecast(
                latitude=farm.location_latitude,
                longitude=farm.location_longitude
            )
            
            if weather_data:
                return weather_data
            else:
                # Fallback to basic data if service fails
                return {
                    'location': f"{farm.location_latitude}, {farm.location_longitude}",
                    'current': {
                        'temperature': 25,
                        'humidity': 65,
                        'condition': 'Partly Cloudy',
                    },
                    'forecast': [
                        {'day': 'Tomorrow', 'high': 28, 'low': 20, 'rainfall': 10},
                        {'day': 'Day 2', 'high': 26, 'low': 19, 'rainfall': 5},
                    ]
                }
        except Farm.DoesNotExist:
            return {}
        except Exception as e:
            logger.error(f"Error fetching weather forecast: {e}")
            return {}
    
    @database_sync_to_async
    def get_farm_performance(self):
        """Fetch current farm performance score"""
        from core.models_analytics import FarmPerformanceScore
        
        latest = FarmPerformanceScore.objects.filter(
            user=self.user,
            farm_id=self.farm_id
        ).order_by('-created_at').first()
        
        if latest:
            return {
                'health_score': latest.health_score,
                'rating': latest.get_rating(),
                'trend': latest.score_trend,
                'components': {
                    'soil_health': latest.soil_health,
                    'water_efficiency': latest.water_efficiency,
                    'pest_disease_control': latest.pest_disease_control,
                    'yield_performance': latest.yield_performance,
                    'cost_efficiency': latest.cost_efficiency,
                    'sustainability': latest.sustainability,
                }
            }
        
        return {}
    
    @database_sync_to_async
    def mark_notification_as_read(self, notification_id):
        """Mark notification as read"""
        from core.models_analytics import NotificationQueue
        
        try:
            notif = NotificationQueue.objects.get(
                id=notification_id,
                user=self.user
            )
            notif.is_read = True
            notif.read_at = timezone.now()
            notif.save()
        except NotificationQueue.DoesNotExist:
            pass


# ============================================================
# ALERT STREAM CONSUMER - Real-Time Alert Broadcasting
# ============================================================

class AlertStreamConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time alert streaming.
    Connects farmers to a stream of farm alerts.
    
    Alert Stream format: alert_stream_{user_id}
    """
    
    async def connect(self):
        """Accept connection and join alert stream"""
        self.user = self.scope['user']
        
        if self.user.is_anonymous:
            await self.close(code=4001)
            return
        
        self.alert_stream_group = f'alert_stream_{self.user.id}'
        
        await self.channel_layer.group_add(
            self.alert_stream_group,
            self.channel_name
        )
        
        logger.info(f"User {self.user.username} joined alert stream")
        await self.accept()
    
    async def disconnect(self, close_code):
        """Leave alert stream group"""
        if hasattr(self, 'alert_stream_group'):
            await self.channel_layer.group_discard(
                self.alert_stream_group,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Handle incoming messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'acknowledge':
                # Client acknowledges alert received
                alert_id = data.get('alert_id')
                await self.acknowledge_alert(alert_id)
                
        except json.JSONDecodeError:
            pass
    
    async def alert_notification(self, event):
        """Receive alert from other parts of system"""
        await self.send(text_data=json.dumps({
            'type': 'alert',
            'data': event.get('data'),
        }))
    
    @database_sync_to_async
    def acknowledge_alert(self, alert_id):
        """Mark alert as acknowledged/read"""
        from core.models_analytics import AlertTrigger
        
        try:
            alert = AlertTrigger.objects.get(id=alert_id, user=self.user)
            # Add acknowledgment tracking if needed
        except AlertTrigger.DoesNotExist:
            pass


# ============================================================
# NOTIFICATION CONSUMER - Real-Time Notifications
# ============================================================

class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time notifications.
    Connects users to receive instant notifications.
    """
    
    async def connect(self):
        """Accept connection for notifications"""
        self.user = self.scope['user']
        
        if self.user.is_anonymous:
            await self.close(code=4001)
            return
        
        self.notification_group = f'notifications_{self.user.id}'
        
        await self.channel_layer.group_add(
            self.notification_group,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        """Leave notification group"""
        if hasattr(self, 'notification_group'):
            await self.channel_layer.group_discard(
                self.notification_group,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Handle incoming messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))
            elif message_type == 'mark_read':
                await self.mark_read(data.get('notification_id'))
                
        except Exception as e:
            logger.error(f"Notification consumer error: {str(e)}")
    
    async def send_notification(self, event):
        """Receive notification from system"""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'data': event.get('data'),
        }))
    
    @database_sync_to_async
    def mark_read(self, notification_id):
        """Mark notification as read"""
        from core.models_analytics import NotificationQueue
        
        try:
            notif = NotificationQueue.objects.get(
                id=notification_id,
                user=self.user
            )
            notif.is_read = True
            notif.read_at = timezone.now()
            notif.save()
        except NotificationQueue.DoesNotExist:
            pass


# ============================================================
# HELPER FUNCTIONS FOR BROADCASTING
# ============================================================

async def broadcast_alert_to_user(user_id, farm_id, alert_data):
    """
    Broadcast alert to all connected dashboard consumers for a user
    """
    from channels.layers import get_channel_layer
    
    channel_layer = get_channel_layer()
    dashboard_group = f'dashboard_{user_id}_{farm_id}'
    
    await channel_layer.group_send(
        dashboard_group,
        {
            'type': 'send_alert_notification',
            'data': alert_data,
        }
    )


async def broadcast_metric_update(user_id, farm_id, metric_data):
    """
    Broadcast real-time metric update to all connected dashboards
    """
    from channels.layers import get_channel_layer
    
    channel_layer = get_channel_layer()
    dashboard_group = f'dashboard_{user_id}_{farm_id}'
    
    await channel_layer.group_send(
        dashboard_group,
        {
            'type': 'send_metric_update',
            'data': metric_data,
        }
    )


async def broadcast_notification_to_user(user_id, notification_data):
    """
    Broadcast notification to user's notification consumer
    """
    from channels.layers import get_channel_layer
    
    channel_layer = get_channel_layer()
    notification_group = f'notifications_{user_id}'
    
    await channel_layer.group_send(
        notification_group,
        {
            'type': 'send_notification',
            'data': notification_data,
        }
    )
