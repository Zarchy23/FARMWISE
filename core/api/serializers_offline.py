# core/api/serializers_offline.py
# Serializers for offline functionality

from rest_framework import serializers
from core.models_offline import (
    OfflineCache, SyncQueue, OfflinePreference, OfflineSyncLog,
    CachedMarketPrice, CachedWeatherData, OfflineAnalytics
)


class OfflineCacheSerializer(serializers.ModelSerializer):
    """Serialize offline cache data"""
    cache_type_display = serializers.CharField(source='get_cache_type_display', read_only=True)
    
    class Meta:
        model = OfflineCache
        fields = ['id', 'cache_type', 'cache_type_display', 'key', 'data', 
                  'size_kb', 'created_at', 'updated_at', 'expires_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class SyncQueueSerializer(serializers.ModelSerializer):
    """Serialize sync queue items"""
    operation_type_display = serializers.CharField(source='get_operation_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = SyncQueue
        fields = ['id', 'operation_type', 'operation_type_display', 'resource_type',
                  'resource_id', 'payload', 'status', 'status_display', 'retry_count',
                  'error_message', 'created_at', 'last_attempted_at', 'completed_at']
        read_only_fields = ['id', 'created_at', 'last_attempted_at', 'completed_at']


class OfflinePreferenceSerializer(serializers.ModelSerializer):
    """Serialize offline preferences"""
    sync_mode_display = serializers.CharField(source='get_sync_mode_display', read_only=True)
    
    class Meta:
        model = OfflinePreference
        fields = ['enable_offline_mode', 'enable_data_caching', 'sync_mode', 
                  'sync_mode_display', 'sync_frequency_minutes', 'cache_size_mb',
                  'cache_expiry_hours', 'enable_voice_offline', 'enable_chat_offline',
                  'enable_market_data_offline', 'background_sync_enabled', 'sync_on_wifi_only']


class OfflineSyncLogSerializer(serializers.ModelSerializer):
    """Serialize sync logs"""
    result_display = serializers.CharField(source='get_result_display', read_only=True)
    
    class Meta:
        model = OfflineSyncLog
        fields = ['id', 'sync_type', 'result', 'result_display', 'records_synced',
                  'records_failed', 'data_transferred_kb', 'duration_seconds',
                  'sync_timestamp', 'notes']
        read_only_fields = ['id', 'sync_timestamp']


class CachedMarketPriceSerializer(serializers.ModelSerializer):
    """Serialize cached market prices"""
    
    class Meta:
        model = CachedMarketPrice
        fields = ['id', 'commodity_name', 'commodity_category', 'price_per_unit',
                  'unit', 'source', 'timestamp', 'cached_at', 'expires_at']
        read_only_fields = ['id', 'cached_at']


class CachedWeatherDataSerializer(serializers.ModelSerializer):
    """Serialize cached weather data"""
    
    class Meta:
        model = CachedWeatherData
        fields = ['id', 'farm', 'temperature_celsius', 'humidity_percent',
                  'rainfall_mm', 'wind_speed_kmh', 'condition', 'forecast_date',
                  'cached_at', 'expires_at']
        read_only_fields = ['id', 'cached_at']


class OfflineAnalyticsSerializer(serializers.ModelSerializer):
    """Serialize offline analytics"""
    
    class Meta:
        model = OfflineAnalytics
        fields = ['date', 'times_used_offline', 'total_offline_time_minutes',
                  'voice_commands_processed_offline', 'chat_messages_processed_offline',
                  'features_accessed', 'sync_errors_count', 'cache_hits', 'cache_misses']
        read_only_fields = ['date']
