# core/api/views_offline.py
# Offline AI Views

from rest_framework import viewsets, status, views
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
import logging

from core.models_offline import (
    OfflineCache, SyncQueue, OfflinePreference, OfflineSyncLog,
    CachedMarketPrice, CachedWeatherData, OfflineAnalytics
)
from core.api.serializers_offline import (
    OfflineCacheSerializer, SyncQueueSerializer, OfflinePreferenceSerializer,
    OfflineSyncLogSerializer, CachedMarketPriceSerializer, CachedWeatherDataSerializer,
    OfflineAnalyticsSerializer
)
from core.services.offline_service import OfflineService

logger = logging.getLogger(__name__)


class OfflineCacheViewSet(viewsets.ReadOnlyModelViewSet):
    """Manage offline cache"""
    serializer_class = OfflineCacheSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['cache_type']
    
    def get_queryset(self):
        """Filter cache for current user"""
        return OfflineCache.objects.filter(user=self.request.user).order_by('-updated_at')
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get cache statistics"""
        stats = OfflineService.get_cache_statistics(request.user)
        return Response(stats)
    
    @action(detail=False, methods=['post'])
    def clear_expired(self, request):
        """Clear expired cache entries"""
        cleared_count = OfflineService.clear_expired_cache(request.user)
        return Response({
            'cleared': cleared_count,
            'message': f'Cleared {cleared_count} expired entries'
        })
    
    @action(detail=False, methods=['post'])
    def clear_all(self, request):
        """Clear all cache for user"""
        count = OfflineCache.objects.filter(user=request.user).delete()[0]
        return Response({
            'cleared': count,
            'message': f'Cleared all {count} cache entries'
        })
    
    @action(detail=True, methods=['delete'])
    def delete_cache(self, request, pk=None):
        """Delete specific cache entry"""
        cache = self.get_object()
        cache.delete()
        return Response({'deleted': True}, status=status.HTTP_204_NO_CONTENT)


class SyncQueueViewSet(viewsets.ReadOnlyModelViewSet):
    """Manage sync queue"""
    serializer_class = SyncQueueSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status', 'operation_type']
    ordering_fields = ['created_at', 'status']
    
    def get_queryset(self):
        """Filter sync queue for current user"""
        return SyncQueue.objects.filter(user=self.request.user).order_by('-created_at')
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get pending sync operations"""
        pending = OfflineService.get_pending_syncs(request.user)
        serializer = self.get_serializer(pending, many=True)
        return Response({
            'pending_count': len(pending),
            'operations': serializer.data
        })
    
    @action(detail=False, methods=['post'])
    def sync_now(self, request):
        """Process sync queue immediately"""
        try:
            result = OfflineService.process_sync_queue(request.user)
            return Response({
                'success': True,
                'synced': result.get('synced', 0),
                'failed': result.get('failed', 0),
                'duration_seconds': result.get('duration', 0)
            })
        
        except Exception as e:
            logger.error(f"Error syncing: {str(e)}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        """Retry a failed sync operation"""
        sync_item = self.get_object()
        
        if sync_item.status != 'failed':
            return Response({
                'error': 'Can only retry failed operations'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        sync_item.status = 'pending'
        sync_item.retry_count += 1
        sync_item.error_message = None
        sync_item.save()
        
        serializer = self.get_serializer(sync_item)
        return Response(serializer.data)


class OfflinePreferenceView(views.APIView):
    """Manage offline preferences"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get offline preferences"""
        pref = OfflineService.get_or_create_preference(request.user)
        serializer = OfflinePreferenceSerializer(pref)
        return Response(serializer.data)
    
    def put(self, request):
        """Update offline preferences"""
        pref = OfflineService.get_or_create_preference(request.user)
        serializer = OfflinePreferenceSerializer(pref, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OfflineSyncLogViewSet(viewsets.ReadOnlyModelViewSet):
    """View sync logs"""
    serializer_class = OfflineSyncLogSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['result', 'sync_type']
    ordering_fields = ['sync_timestamp']
    
    def get_queryset(self):
        """Filter sync logs for current user"""
        return OfflineSyncLog.objects.filter(user=self.request.user).order_by('-sync_timestamp')


class CachedMarketPriceViewSet(viewsets.ReadOnlyModelViewSet):
    """View cached market prices"""
    serializer_class = CachedMarketPriceSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['commodity_category']
    search_fields = ['commodity_name']
    
    def get_queryset(self):
        """Filter cached prices for current user"""
        return CachedMarketPrice.objects.filter(
            user=self.request.user
        ).order_by('-timestamp')
    
    @action(detail=False, methods=['get'])
    def by_commodity(self, request):
        """Get cached prices for a specific commodity"""
        commodity = request.query_params.get('commodity')
        if not commodity:
            return Response({
                'error': 'commodity parameter required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        prices = OfflineService.get_cached_market_prices(request.user, commodity)
        return Response(prices)


class CachedWeatherViewSet(viewsets.ReadOnlyModelViewSet):
    """View cached weather data"""
    serializer_class = CachedWeatherDataSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['farm']
    ordering_fields = ['forecast_date']
    
    def get_queryset(self):
        """Filter cached weather for current user"""
        return CachedWeatherData.objects.filter(
            user=self.request.user
        ).order_by('forecast_date')
    
    @action(detail=False, methods=['get'])
    def forecast(self, request):
        """Get weather forecast from cache"""
        farm_id = request.query_params.get('farm_id')
        days = int(request.query_params.get('days', 7))
        
        from core.models import Farm
        farm = None
        if farm_id:
            farm = Farm.objects.filter(id=farm_id, owner=request.user).first()
        
        weather = OfflineService.get_cached_weather(request.user, farm, days)
        return Response(weather)


class OfflineAnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    """View offline usage analytics"""
    serializer_class = OfflineAnalyticsSerializer
    permission_classes = [IsAuthenticated]
    ordering_fields = ['date']
    
    def get_queryset(self):
        """Filter analytics for current user"""
        return OfflineAnalytics.objects.filter(user=self.request.user).order_by('-date')
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get today's analytics"""
        from django.utils import timezone
        today = timezone.now().date()
        
        analytics, created = OfflineAnalytics.objects.get_or_create(
            user=request.user,
            date=today
        )
        
        serializer = self.get_serializer(analytics)
        return Response(serializer.data)


class OfflineDashboardView(views.APIView):
    """Offline functionality dashboard"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get offline dashboard data"""
        try:
            pref = OfflineService.get_or_create_preference(request.user)
            cache_stats = OfflineService.get_cache_statistics(request.user)
            offline_analytics = OfflineService.get_offline_analytics(request.user)
            pending_syncs = OfflineService.get_pending_syncs(request.user)
            
            # Get recent sync logs
            sync_logs = OfflineSyncLog.objects.filter(
                user=request.user
            ).order_by('-sync_timestamp')[:5]
            
            return Response({
                'offline_enabled': pref.enable_offline_mode,
                'sync_mode': pref.get_sync_mode_display(),
                'cache_statistics': cache_stats,
                'analytics': offline_analytics,
                'pending_syncs_count': pending_syncs.count(),
                'recent_syncs': OfflineSyncLogSerializer(sync_logs, many=True).data,
                'cache_features': {
                    'voice': pref.enable_voice_offline,
                    'chat': pref.enable_chat_offline,
                    'market_data': pref.enable_market_data_offline
                },
                'background_sync': pref.background_sync_enabled,
                'sync_on_wifi_only': pref.sync_on_wifi_only
            })
        
        except Exception as e:
            logger.error(f"Error loading offline dashboard: {str(e)}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
