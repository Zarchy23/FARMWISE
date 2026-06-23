# core/iot/admin.py
# Django Admin Configuration for IoT Models

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count
from core.models_iot import (
    IoTDevice, SensorType, SensorConfiguration,
    SensorDataPoint, SensorDataBatch, DeviceCommand,
    DeviceHealth, DeviceMaintenanceLog, DeviceProvisioningToken
)


@admin.register(IoTDevice)
class IoTDeviceAdmin(admin.ModelAdmin):
    """Manage IoT devices"""
    
    list_display = (
        'device_id_link', 'name', 'device_type', 'farm', 'status_badge',
        'battery_badge', 'is_online_badge', 'last_seen', 'sensor_count'
    )
    list_filter = ('device_type', 'status', 'connection_type', 'power_source', 'farm')
    search_fields = ('device_id', 'name', 'serial_number', 'farm__name')
    readonly_fields = (
        'device_id', 'api_key', 'last_data_received', 'last_seen',
        'created_at', 'updated_at', 'info_display'
    )
    
    fieldsets = (
        ('Identification', {
            'fields': ('device_id', 'name', 'description')
        }),
        ('Ownership', {
            'fields': ('user', 'farm', 'field')
        }),
        ('Device Details', {
            'fields': ('device_type', 'manufacturer', 'model', 'serial_number')
        }),
        ('Connectivity', {
            'fields': ('connection_type', 'status', 'api_key', 'api_secret')
        }),
        ('Location', {
            'fields': ('latitude', 'longitude', 'location_description')
        }),
        ('Power', {
            'fields': ('battery_level', 'power_source')
        }),
        ('Configuration', {
            'fields': ('sampling_interval', 'transmission_interval')
        }),
        ('Status', {
            'fields': ('last_data_received', 'last_seen', 'offline_alert_sent'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('System', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_active', 'mark_inactive', 'reset_api_key', 'check_online_status']
    
    def device_id_link(self, obj):
        url = reverse('admin:iot_iotdevice_change', args=[obj.pk])
        return format_html('<a href="{}">{}</a>', url, obj.device_id)
    device_id_link.short_description = 'Device ID'
    
    def status_badge(self, obj):
        colors = {
            'active': '#28a745',
            'inactive': '#6c757d',
            'disconnected': '#ffc107',
            'error': '#dc3545',
            'low_battery': '#ff6b6b',
            'maintenance': '#0dcaf0',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def battery_badge(self, obj):
        colors = {
            'excellent': '#28a745',
            'good': '#17a2b8',
            'warning': '#ffc107',
            'critical': '#dc3545',
        }
        battery_status = obj.battery_status()
        color = colors.get(battery_status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}%</span>',
            color, obj.battery_level
        )
    battery_badge.short_description = 'Battery'
    
    def is_online_badge(self, obj):
        is_online = obj.is_online()
        color = '#28a745' if is_online else '#dc3545'
        text = '🟢 Online' if is_online else '🔴 Offline'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, text
        )
    is_online_badge.short_description = 'Online'
    
    def sensor_count(self, obj):
        count = obj.sensors.count()
        return format_html('<strong>{} sensor{}</strong>', count, 's' if count != 1 else '')
    sensor_count.short_description = 'Sensors'
    
    def info_display(self, obj):
        return format_html(
            '<div style="font-family: monospace; font-size: 12px; line-height: 1.6;">'
            '<strong>Device ID:</strong> {}<br/>'
            '<strong>API Key:</strong> {}<br/>'
            '<strong>Last Data:</strong> {}<br/>'
            '<strong>Sensors:</strong> {}<br/>'
            '</div>',
            obj.device_id,
            obj.api_key[:16] + '...',
            obj.last_data_received or 'Never',
            obj.sensors.count()
        )
    info_display.short_description = 'Device Information'
    
    def mark_active(self, request, queryset):
        updated = queryset.update(status='active')
        self.message_user(request, f'{updated} devices marked as active')
    mark_active.short_description = 'Mark selected as active'
    
    def mark_inactive(self, request, queryset):
        updated = queryset.update(status='inactive')
        self.message_user(request, f'{updated} devices marked as inactive')
    mark_inactive.short_description = 'Mark selected as inactive'
    
    def reset_api_key(self, request, queryset):
        import uuid
        for device in queryset:
            device.api_key = str(uuid.uuid4())
            device.save()
        self.message_user(request, f'API keys reset for {queryset.count()} devices')
    reset_api_key.short_description = 'Reset API keys'
    
    def check_online_status(self, request, queryset):
        for device in queryset:
            if device.is_online():
                status_text = 'Online ✓'
            else:
                status_text = 'Offline ✗'
        self.message_user(request, 'Online status checked')
    check_online_status.short_description = 'Check online status'


@admin.register(SensorType)
class SensorTypeAdmin(admin.ModelAdmin):
    """Manage sensor types"""
    
    list_display = ('code', 'name', 'unit', 'data_type', 'is_active')
    list_filter = ('data_type', 'is_active')
    search_fields = ('code', 'name')
    readonly_fields = ('code',)
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('code', 'name', 'description', 'data_type')
        }),
        ('Physical Properties', {
            'fields': ('unit', 'min_value', 'max_value')
        }),
        ('Thresholds', {
            'fields': ('optimal_min', 'optimal_max', 'warning_below', 'warning_above')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


@admin.register(SensorConfiguration)
class SensorConfigurationAdmin(admin.ModelAdmin):
    """Manage sensor configurations"""
    
    list_display = ('device', 'sensor_type', 'channel_name', 'is_active', 'calibration_multiplier')
    list_filter = ('is_active', 'sensor_type__code')
    search_fields = ('device__name', 'channel_name')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Sensor', {
            'fields': ('device', 'sensor_type', 'channel_name')
        }),
        ('Calibration', {
            'fields': ('calibration_offset', 'calibration_multiplier', 'last_calibrated')
        }),
        ('Thresholds', {
            'fields': ('warning_below', 'warning_above')
        }),
        ('Status', {
            'fields': ('is_active', 'created_at', 'updated_at')
        }),
    )


@admin.register(SensorDataPoint)
class SensorDataPointAdmin(admin.ModelAdmin):
    """View sensor data points"""
    
    list_display = ('device', 'channel_name', 'value_display', 'device_timestamp', 'is_valid')
    list_filter = ('is_valid', 'device', 'device_timestamp')
    search_fields = ('device__name', 'sensor_config__channel_name')
    readonly_fields = ('device', 'sensor_config', 'raw_value', 'value', 'server_timestamp')
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def channel_name(self, obj):
        return obj.sensor_config.channel_name
    channel_name.short_description = 'Channel'
    
    def value_display(self, obj):
        unit = obj.sensor_config.sensor_type.unit
        return f'{obj.value} {unit}'
    value_display.short_description = 'Value'


@admin.register(SensorDataBatch)
class SensorDataBatchAdmin(admin.ModelAdmin):
    """View data batch submissions"""
    
    list_display = ('device', 'batch_size', 'processed_data_points', 'status_badge', 'received_at')
    list_filter = ('status', 'received_at')
    search_fields = ('device__name',)
    readonly_fields = ('device', 'batch_size', 'raw_data', 'processed_data_points', 'errors', 'received_at', 'processed_at')
    
    def has_add_permission(self, request):
        return False
    
    def status_badge(self, obj):
        colors = {
            'received': '#0dcaf0',
            'processing': '#ffc107',
            'processed': '#28a745',
            'failed': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'


@admin.register(DeviceCommand)
class DeviceCommandAdmin(admin.ModelAdmin):
    """Manage device commands"""
    
    list_display = ('device', 'command_type', 'status_badge', 'created_at', 'executed_at')
    list_filter = ('status', 'command_type', 'created_at')
    search_fields = ('device__name', 'command_text')
    readonly_fields = ('created_at', 'sent_at', 'executed_at')
    
    actions = ['retry_failed_commands']
    
    def status_badge(self, obj):
        colors = {
            'pending': '#ffc107',
            'sent': '#0dcaf0',
            'acknowledged': '#17a2b8',
            'executed': '#28a745',
            'failed': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def retry_failed_commands(self, request, queryset):
        failed = queryset.filter(status='failed')
        failed.update(status='pending', retry_count=0)
        self.message_user(request, f'{failed.count()} commands queued for retry')
    retry_failed_commands.short_description = 'Retry failed commands'


@admin.register(DeviceHealth)
class DeviceHealthAdmin(admin.ModelAdmin):
    """View device health metrics"""
    
    list_display = ('device', 'uptime_percentage', 'failure_rate', 'consecutive_failures', 'avg_signal_strength')
    list_filter = ('updated_at',)
    search_fields = ('device__name',)
    readonly_fields = ('device', 'updated_at')
    
    def has_add_permission(self, request):
        return False
    
    def failure_rate(self, obj):
        if obj.total_readings == 0:
            return '0%'
        rate = (obj.failed_readings / obj.total_readings) * 100
        return f'{rate:.1f}%'
    failure_rate.short_description = 'Failure Rate'


@admin.register(DeviceMaintenanceLog)
class DeviceMaintenanceLogAdmin(admin.ModelAdmin):
    """View maintenance history"""
    
    list_display = ('device', 'maintenance_type', 'performed_by', 'performed_at')
    list_filter = ('maintenance_type', 'performed_at')
    search_fields = ('device__name', 'performed_by', 'notes')
    readonly_fields = ('created_at', 'performed_at')


@admin.register(DeviceProvisioningToken)
class DeviceProvisioningTokenAdmin(admin.ModelAdmin):
    """Manage provisioning tokens"""
    
    list_display = ('token_display', 'user', 'device_name', 'is_used', 'expires_at')
    list_filter = ('is_used', 'created_at')
    search_fields = ('token', 'device_name')
    readonly_fields = ('token', 'created_at', 'used_at', 'created_device')
    
    def token_display(self, obj):
        return obj.token[:16] + '...' if len(obj.token) > 16 else obj.token
    token_display.short_description = 'Token'
