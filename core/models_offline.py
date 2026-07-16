# core/models_offline.py
# Offline AI capabilities with caching and sync

from django.db import models
from django.conf import settings
from core.models import Farm
import json


class OfflineCache(models.Model):
    """Cache for offline-accessible data"""
    
    CACHE_TYPES = [
        ('commodity', 'Commodity Data'),
        ('weather', 'Weather Data'),
        ('market_price', 'Market Prices'),
        ('chat_response', 'Chat Responses'),
        ('farm_data', 'Farm Data'),
        ('crop_advice', 'Crop Advice'),
        ('pest_guide', 'Pest Identification'),
        ('location_data', 'Location Data'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='offline_caches')
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, null=True, blank=True)
    cache_type = models.CharField(max_length=20, choices=CACHE_TYPES)
    
    key = models.CharField(max_length=500, unique=True)  # Unique cache key
    data = models.JSONField()  # Cached JSON data
    size_kb = models.IntegerField(default=0)  # Size in kilobytes
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()  # Cache expiration time
    
    class Meta:
        unique_together = ('user', 'key', 'cache_type')
        indexes = [
            models.Index(fields=['user', 'cache_type']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_cache_type_display()} ({self.size_kb}KB)"
    
    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at
    
    def get_cached_data(self):
        """Safely retrieve cached data"""
        if self.is_expired():
            self.delete()
            return None
        return self.data


class SyncQueue(models.Model):
    """Queue for syncing offline changes with server"""
    
    SYNC_STATUS = [
        ('pending', 'Pending'),
        ('syncing', 'Syncing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('conflict', 'Conflict'),
    ]
    
    OPERATION_TYPES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('voice_command', 'Voice Command'),
        ('chat_message', 'Chat Message'),
        ('price_alert', 'Price Alert'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sync_queues')
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, null=True, blank=True)
    
    operation_type = models.CharField(max_length=20, choices=OPERATION_TYPES)
    resource_type = models.CharField(max_length=50)  # e.g., 'market_price', 'voice_command'
    resource_id = models.CharField(max_length=100, null=True, blank=True)
    
    payload = models.JSONField()  # Data to sync
    status = models.CharField(max_length=20, choices=SYNC_STATUS, default='pending')
    retry_count = models.IntegerField(default=0)
    
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_attempted_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_operation_type_display()} ({self.get_status_display()})"


class OfflinePreference(models.Model):
    """User preferences for offline functionality"""
    
    SYNC_MODES = [
        ('auto', 'Automatic'),
        ('manual', 'Manual'),
        ('scheduled', 'Scheduled'),
    ]
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='offline_preference')
    
    enable_offline_mode = models.BooleanField(default=True)
    enable_data_caching = models.BooleanField(default=True)
    sync_mode = models.CharField(max_length=20, choices=SYNC_MODES, default='auto')
    sync_frequency_minutes = models.IntegerField(default=30)  # Auto-sync every N minutes
    
    cache_size_mb = models.IntegerField(default=50)  # Max cache size in MB
    cache_expiry_hours = models.IntegerField(default=24)  # Cache expiry in hours
    
    enable_voice_offline = models.BooleanField(default=True)
    enable_chat_offline = models.BooleanField(default=True)
    enable_market_data_offline = models.BooleanField(default=True)
    
    background_sync_enabled = models.BooleanField(default=True)
    sync_on_wifi_only = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Offline Preference'
        verbose_name_plural = 'Offline Preferences'
    
    def __str__(self):
        return f"{self.user.username} - Offline Settings"


class OfflineSyncLog(models.Model):
    """Log of all sync operations"""
    
    SYNC_RESULT = [
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('partial', 'Partial'),
        ('offline', 'Offline'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sync_logs')
    
    sync_type = models.CharField(max_length=50)  # 'upload', 'download', 'bidirectional'
    result = models.CharField(max_length=20, choices=SYNC_RESULT)
    
    records_synced = models.IntegerField(default=0)
    records_failed = models.IntegerField(default=0)
    data_transferred_kb = models.IntegerField(default=0)
    
    duration_seconds = models.FloatField()
    sync_timestamp = models.DateTimeField(auto_now_add=True)
    
    notes = models.TextField(null=True, blank=True)
    
    class Meta:
        ordering = ['-sync_timestamp']
        indexes = [
            models.Index(fields=['user', 'sync_timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.sync_type} ({self.result})"


class CachedMarketPrice(models.Model):
    """Cached market price data for offline access"""
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cached_prices')
    
    commodity_name = models.CharField(max_length=100)
    commodity_category = models.CharField(max_length=50)
    
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20)
    source = models.CharField(max_length=50)
    
    timestamp = models.DateTimeField()
    cached_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'commodity_name']),
        ]
    
    def __str__(self):
        return f"{self.commodity_name} - {self.price_per_unit}{self.unit}"


class CachedWeatherData(models.Model):
    """Cached weather data for offline access"""
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cached_weather')
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, null=True, blank=True)
    
    temperature_celsius = models.FloatField()
    humidity_percent = models.FloatField()
    rainfall_mm = models.FloatField()
    wind_speed_kmh = models.FloatField()
    condition = models.CharField(max_length=50)  # 'sunny', 'rainy', 'cloudy', etc.
    
    forecast_date = models.DateField()
    cached_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        ordering = ['-forecast_date']
        indexes = [
            models.Index(fields=['user', 'forecast_date']),
        ]
    
    def __str__(self):
        return f"Weather {self.forecast_date} - {self.temperature_celsius}°C"


class OfflineAnalytics(models.Model):
    """Track offline usage analytics"""
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='offline_analytics')
    
    date = models.DateField(auto_now_add=True)
    
    times_used_offline = models.IntegerField(default=0)  # Number of offline sessions
    total_offline_time_minutes = models.IntegerField(default=0)  # Total offline usage time
    
    voice_commands_processed_offline = models.IntegerField(default=0)
    chat_messages_processed_offline = models.IntegerField(default=0)
    features_accessed = models.JSONField(default=list)  # List of accessed features
    
    sync_errors_count = models.IntegerField(default=0)
    cache_hits = models.IntegerField(default=0)
    cache_misses = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-date']
        unique_together = ('user', 'date')
        indexes = [
            models.Index(fields=['user', 'date']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.date}"
