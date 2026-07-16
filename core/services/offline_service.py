# core/services/offline_service.py
# Offline AI service for caching, syncing, and offline operations

from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User
import logging
import json
from decimal import Decimal

from core.models_offline import (
    OfflineCache, SyncQueue, OfflinePreference, OfflineSyncLog,
    CachedMarketPrice, CachedWeatherData, OfflineAnalytics
)

logger = logging.getLogger(__name__)


class OfflineService:
    """Service for offline AI operations and data caching"""
    
    # Cache key prefixes
    CACHE_PREFIX_COMMODITY = 'commodity:'
    CACHE_PREFIX_MARKET = 'market_price:'
    CACHE_PREFIX_WEATHER = 'weather:'
    CACHE_PREFIX_CHAT = 'chat_response:'
    CACHE_PREFIX_FARM = 'farm_data:'
    CACHE_PREFIX_CROP = 'crop_advice:'
    CACHE_PREFIX_PEST = 'pest_guide:'
    
    @staticmethod
    def get_or_create_preference(user: User) -> OfflinePreference:
        """Get or create offline preference for user"""
        pref, created = OfflinePreference.objects.get_or_create(user=user)
        return pref
    
    @staticmethod
    def cache_data(user: User, cache_type: str, key: str, data: dict, 
                   expires_hours: int = None, farm=None) -> OfflineCache:
        """Cache data for offline access"""
        try:
            pref = OfflineService.get_or_create_preference(user)
            
            if expires_hours is None:
                expires_hours = pref.cache_expiry_hours
            
            expires_at = timezone.now() + timedelta(hours=expires_hours)
            
            # Calculate data size
            data_json = json.dumps(data)
            size_kb = len(data_json.encode('utf-8')) / 1024
            
            # Check cache size limits
            current_cache_size = OfflineCache.objects.filter(
                user=user,
                cache_type=cache_type
            ).aggregate(total_size=sum('size_kb'))['total_size'] or 0
            
            if current_cache_size + size_kb > pref.cache_size_mb * 1024:
                # Delete oldest entries to make space
                old_entries = OfflineCache.objects.filter(
                    user=user,
                    cache_type=cache_type
                ).order_by('updated_at')[:5]
                old_entries.delete()
            
            cache, created = OfflineCache.objects.update_or_create(
                user=user,
                key=key,
                cache_type=cache_type,
                defaults={
                    'farm': farm,
                    'data': data,
                    'size_kb': int(size_kb),
                    'expires_at': expires_at
                }
            )
            
            logger.info(f"Cached {cache_type} for {user.username}: {key}")
            return cache
        
        except Exception as e:
            logger.error(f"Error caching data: {str(e)}")
            raise
    
    @staticmethod
    def get_cached_data(user: User, cache_type: str, key: str) -> dict or None:
        """Retrieve cached data"""
        try:
            cache = OfflineCache.objects.filter(
                user=user,
                cache_type=cache_type,
                key=key
            ).first()
            
            if cache:
                if cache.is_expired():
                    cache.delete()
                    return None
                return cache.data
            
            return None
        
        except Exception as e:
            logger.error(f"Error retrieving cached data: {str(e)}")
            return None
    
    @staticmethod
    def get_user_cache(user: User, cache_type: str = None) -> list:
        """Get all cached data for user"""
        queryset = OfflineCache.objects.filter(user=user)
        
        if cache_type:
            queryset = queryset.filter(cache_type=cache_type)
        
        # Filter expired entries
        valid_cache = []
        for cache in queryset:
            if not cache.is_expired():
                valid_cache.append(cache)
            else:
                cache.delete()
        
        return valid_cache
    
    @staticmethod
    def queue_operation(user: User, operation_type: str, resource_type: str,
                       payload: dict, farm=None, resource_id: str = None) -> SyncQueue:
        """Queue an operation for syncing"""
        try:
            sync_item = SyncQueue.objects.create(
                user=user,
                farm=farm,
                operation_type=operation_type,
                resource_type=resource_type,
                resource_id=resource_id,
                payload=payload,
                status='pending'
            )
            
            logger.info(f"Queued {operation_type} for {user.username}: {resource_type}")
            return sync_item
        
        except Exception as e:
            logger.error(f"Error queueing operation: {str(e)}")
            raise
    
    @staticmethod
    def get_pending_syncs(user: User) -> list:
        """Get pending sync operations"""
        return SyncQueue.objects.filter(
            user=user,
            status__in=['pending', 'failed']
        ).order_by('created_at')
    
    @staticmethod
    def process_sync_queue(user: User) -> dict:
        """Process and sync queued operations"""
        try:
            pending_syncs = OfflineService.get_pending_syncs(user)
            
            start_time = timezone.now()
            synced_count = 0
            failed_count = 0
            
            for sync_item in pending_syncs:
                try:
                    sync_item.status = 'syncing'
                    sync_item.last_attempted_at = timezone.now()
                    sync_item.save()
                    
                    # Process based on operation type
                    success = OfflineService._execute_sync_operation(sync_item)
                    
                    if success:
                        sync_item.status = 'completed'
                        sync_item.completed_at = timezone.now()
                        synced_count += 1
                    else:
                        sync_item.status = 'failed'
                        sync_item.retry_count += 1
                        failed_count += 1
                    
                    sync_item.save()
                
                except Exception as e:
                    logger.error(f"Error syncing item {sync_item.id}: {str(e)}")
                    sync_item.status = 'failed'
                    sync_item.error_message = str(e)
                    sync_item.retry_count += 1
                    sync_item.save()
                    failed_count += 1
            
            # Log sync result
            duration = (timezone.now() - start_time).total_seconds()
            
            OfflineSyncLog.objects.create(
                user=user,
                sync_type='upload',
                result='success' if failed_count == 0 else 'partial',
                records_synced=synced_count,
                records_failed=failed_count,
                duration_seconds=duration
            )
            
            return {
                'synced': synced_count,
                'failed': failed_count,
                'duration': duration
            }
        
        except Exception as e:
            logger.error(f"Error processing sync queue: {str(e)}")
            return {'error': str(e)}
    
    @staticmethod
    def _execute_sync_operation(sync_item: SyncQueue) -> bool:
        """Execute a single sync operation"""
        # Override this in subclasses for specific operations
        return True
    
    @staticmethod
    def cache_market_prices(user: User, prices: list) -> int:
        """Cache market price data"""
        cached_count = 0
        try:
            expires_at = timezone.now() + timedelta(hours=24)
            
            for price_data in prices:
                CachedMarketPrice.objects.update_or_create(
                    user=user,
                    commodity_name=price_data.get('commodity_name'),
                    defaults={
                        'commodity_category': price_data.get('category', 'General'),
                        'price_per_unit': Decimal(str(price_data.get('price', 0))),
                        'unit': price_data.get('unit', 'kg'),
                        'source': price_data.get('source', 'API'),
                        'timestamp': timezone.now(),
                        'expires_at': expires_at
                    }
                )
                cached_count += 1
            
            logger.info(f"Cached {cached_count} market prices for {user.username}")
            return cached_count
        
        except Exception as e:
            logger.error(f"Error caching market prices: {str(e)}")
            return 0
    
    @staticmethod
    def get_cached_market_prices(user: User, commodity: str = None) -> list:
        """Get cached market prices"""
        queryset = CachedMarketPrice.objects.filter(
            user=user,
            expires_at__gt=timezone.now()
        )
        
        if commodity:
            queryset = queryset.filter(commodity_name__icontains=commodity)
        
        return list(queryset.values())
    
    @staticmethod
    def cache_weather_data(user: User, weather_data: dict, farm=None) -> CachedWeatherData:
        """Cache weather data"""
        try:
            expires_at = timezone.now() + timedelta(hours=12)
            
            weather, created = CachedWeatherData.objects.update_or_create(
                user=user,
                farm=farm,
                forecast_date=weather_data.get('date'),
                defaults={
                    'temperature_celsius': float(weather_data.get('temperature', 0)),
                    'humidity_percent': float(weather_data.get('humidity', 0)),
                    'rainfall_mm': float(weather_data.get('rainfall', 0)),
                    'wind_speed_kmh': float(weather_data.get('wind_speed', 0)),
                    'condition': weather_data.get('condition', 'Unknown'),
                    'expires_at': expires_at
                }
            )
            
            logger.info(f"Cached weather data for {user.username}")
            return weather
        
        except Exception as e:
            logger.error(f"Error caching weather data: {str(e)}")
            raise
    
    @staticmethod
    def get_cached_weather(user: User, farm=None, days: int = 7) -> list:
        """Get cached weather data"""
        queryset = CachedWeatherData.objects.filter(
            user=user,
            expires_at__gt=timezone.now()
        )
        
        if farm:
            queryset = queryset.filter(farm=farm)
        
        queryset = queryset.order_by('forecast_date')[:days]
        
        return list(queryset.values())
    
    @staticmethod
    def get_offline_analytics(user: User) -> dict:
        """Get offline usage analytics"""
        today = timezone.now().date()
        
        analytics, created = OfflineAnalytics.objects.get_or_create(
            user=user,
            date=today
        )
        
        cache_hit_rate = 0
        total_cache_accesses = analytics.cache_hits + analytics.cache_misses
        if total_cache_accesses > 0:
            cache_hit_rate = (analytics.cache_hits / total_cache_accesses) * 100
        
        return {
            'offline_sessions': analytics.times_used_offline,
            'total_offline_time_minutes': analytics.total_offline_time_minutes,
            'voice_commands_offline': analytics.voice_commands_processed_offline,
            'chat_messages_offline': analytics.chat_messages_processed_offline,
            'cache_hit_rate': cache_hit_rate,
            'sync_errors': analytics.sync_errors_count,
            'features_accessed': analytics.features_accessed
        }
    
    @staticmethod
    def record_offline_session(user: User, feature: str, duration_minutes: int) -> None:
        """Record offline usage"""
        today = timezone.now().date()
        
        analytics, created = OfflineAnalytics.objects.get_or_create(
            user=user,
            date=today
        )
        
        analytics.times_used_offline += 1
        analytics.total_offline_time_minutes += duration_minutes
        
        features = analytics.features_accessed
        if feature not in features:
            features.append(feature)
        
        analytics.features_accessed = features
        analytics.save()
    
    @staticmethod
    def clear_expired_cache(user: User = None) -> int:
        """Clear expired cache entries"""
        if user:
            queryset = OfflineCache.objects.filter(user=user)
        else:
            queryset = OfflineCache.objects.all()
        
        expired_count = 0
        for cache in queryset:
            if cache.is_expired():
                cache.delete()
                expired_count += 1
        
        logger.info(f"Cleared {expired_count} expired cache entries")
        return expired_count
    
    @staticmethod
    def get_cache_statistics(user: User) -> dict:
        """Get cache statistics for user"""
        caches = OfflineCache.objects.filter(user=user)
        
        total_size_kb = sum(cache.size_kb for cache in caches)
        count_by_type = {}
        
        for cache_type, _ in OfflineCache.CACHE_TYPES:
            count_by_type[cache_type] = caches.filter(cache_type=cache_type).count()
        
        return {
            'total_cached_items': caches.count(),
            'total_cache_size_kb': total_size_kb,
            'total_cache_size_mb': round(total_size_kb / 1024, 2),
            'cache_by_type': count_by_type,
            'pending_syncs': SyncQueue.objects.filter(
                user=user,
                status__in=['pending', 'failed']
            ).count()
        }
