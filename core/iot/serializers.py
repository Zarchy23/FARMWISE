# core/iot/serializers.py
# DRF Serializers for IoT Device API

from rest_framework import serializers
from django.core.validators import MinValueValidator, MaxValueValidator
from core.models_iot import (
    IoTDevice, SensorType, SensorConfiguration,
    SensorDataPoint, SensorDataBatch, DeviceCommand,
    DeviceHealth, DeviceMaintenanceLog, DeviceProvisioningToken
)


class SensorTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SensorType
        fields = [
            'id', 'code', 'name', 'description', 'unit',
            'min_value', 'max_value', 'optimal_min', 'optimal_max',
            'warning_below', 'warning_above', 'data_type'
        ]
        read_only_fields = ['id']


class SensorConfigurationSerializer(serializers.ModelSerializer):
    sensor_type_detail = SensorTypeSerializer(source='sensor_type', read_only=True)
    
    class Meta:
        model = SensorConfiguration
        fields = [
            'id', 'device', 'sensor_type', 'sensor_type_detail',
            'channel_name', 'calibration_offset', 'calibration_multiplier',
            'last_calibrated', 'warning_below', 'warning_above', 'is_active'
        ]
        read_only_fields = ['id']


class DeviceHealthSerializer(serializers.ModelSerializer):
    uptime_status = serializers.SerializerMethodField()
    
    class Meta:
        model = DeviceHealth
        fields = [
            'id', 'total_readings', 'successful_readings', 'failed_readings',
            'uptime_percentage', 'consecutive_failures', 'avg_signal_strength',
            'last_error', 'last_error_time', 'uptime_status'
        ]
        read_only_fields = ['id']
    
    def get_uptime_status(self, obj):
        """Get human-readable uptime status"""
        if obj.uptime_percentage >= 95:
            return 'excellent'
        elif obj.uptime_percentage >= 85:
            return 'good'
        elif obj.uptime_percentage >= 70:
            return 'acceptable'
        else:
            return 'poor'


class IoTDeviceListSerializer(serializers.ModelSerializer):
    """Simplified device serializer for list views"""
    
    battery_status = serializers.SerializerMethodField()
    is_online = serializers.SerializerMethodField()
    health = DeviceHealthSerializer(read_only=True)
    
    class Meta:
        model = IoTDevice
        fields = [
            'id', 'device_id', 'name', 'device_type', 'connection_type',
            'status', 'battery_level', 'battery_status', 'is_online',
            'last_seen', 'health', 'farm', 'field'
        ]
        read_only_fields = ['id', 'device_id', 'last_seen', 'health']
    
    def get_battery_status(self, obj):
        return obj.battery_status()
    
    def get_is_online(self, obj):
        return obj.is_online()


class IoTDeviceDetailSerializer(serializers.ModelSerializer):
    """Full device serializer with all details"""
    
    sensors = SensorConfigurationSerializer(many=True, read_only=True)
    battery_status = serializers.SerializerMethodField()
    is_online = serializers.SerializerMethodField()
    health = DeviceHealthSerializer(read_only=True)
    
    class Meta:
        model = IoTDevice
        fields = [
            'id', 'device_id', 'name', 'description', 'user', 'farm', 'field',
            'device_type', 'manufacturer', 'model', 'serial_number',
            'connection_type', 'status', 'api_key', 'latitude', 'longitude',
            'location_description', 'battery_level', 'battery_status',
            'power_source', 'sampling_interval', 'transmission_interval',
            'last_data_received', 'last_seen', 'is_online', 'is_online',
            'metadata', 'sensors', 'health', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'device_id', 'api_key', 'last_data_received',
            'last_seen', 'sensors', 'health', 'created_at', 'updated_at'
        ]


class SensorDataPointSerializer(serializers.ModelSerializer):
    sensor_info = serializers.SerializerMethodField()
    
    class Meta:
        model = SensorDataPoint
        fields = [
            'id', 'device', 'sensor_config', 'sensor_info',
            'raw_value', 'value', 'signal_strength', 'is_valid',
            'device_timestamp', 'server_timestamp'
        ]
        read_only_fields = ['id', 'server_timestamp']
    
    def get_sensor_info(self, obj):
        return {
            'channel_name': obj.sensor_config.channel_name,
            'sensor_name': obj.sensor_config.sensor_type.name,
            'unit': obj.sensor_config.sensor_type.unit,
        }


class SensorDataBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = SensorDataBatch
        fields = [
            'id', 'device', 'batch_size', 'status',
            'raw_data', 'processed_data_points', 'errors',
            'received_at', 'processed_at'
        ]
        read_only_fields = ['id', 'status', 'processed_data_points', 'errors', 'processed_at']


class DeviceCommandSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceCommand
        fields = [
            'id', 'device', 'command_type', 'command_text',
            'parameters', 'status', 'retry_count', 'max_retries',
            'sent_at', 'executed_at', 'result', 'created_at', 'expires_at'
        ]
        read_only_fields = [
            'id', 'status', 'retry_count', 'sent_at',
            'executed_at', 'result', 'created_at'
        ]


class DeviceMaintenanceLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceMaintenanceLog
        fields = [
            'id', 'device', 'maintenance_type', 'performed_by',
            'notes', 'before_battery', 'after_battery',
            'performed_at', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class DeviceProvisioningTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceProvisioningToken
        fields = [
            'token', 'device_type', 'device_name', 'is_used',
            'created_at', 'expires_at', 'used_at'
        ]
        read_only_fields = ['token', 'is_used', 'created_at', 'expires_at', 'used_at']


# ============================================================
# DATA SUBMISSION SERIALIZERS
# ============================================================

class BulkSensorDataSubmissionSerializer(serializers.Serializer):
    """Schema for bulk sensor data submission from devices"""
    
    api_key = serializers.CharField(max_length=100, write_only=True)
    timestamp = serializers.DateTimeField()  # Device clock time
    data_points = serializers.ListField(
        child=serializers.DictField(),
        help_text='Array of {channel: "ch1", value: 45.3}'
    )
    battery_level = serializers.IntegerField(
        required=False,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    signal_strength = serializers.IntegerField(required=False)
    metadata = serializers.JSONField(required=False, default=dict)


class QuickSensorDataSubmissionSerializer(serializers.Serializer):
    """Quick single-reading submission"""
    
    api_key = serializers.CharField(max_length=100, write_only=True)
    channel = serializers.CharField(max_length=50)
    value = serializers.DecimalField(max_digits=12, decimal_places=4)
    timestamp = serializers.DateTimeField()
    battery_level = serializers.IntegerField(required=False)
    signal_strength = serializers.IntegerField(required=False)


class DeviceRegistrationSerializer(serializers.Serializer):
    """Register new device with provisioning token"""
    
    provisioning_token = serializers.CharField(max_length=100)
    device_name = serializers.CharField(max_length=255)
    device_type = serializers.ChoiceField(choices=IoTDevice.DEVICE_TYPES)
    connection_type = serializers.ChoiceField(choices=IoTDevice.CONNECTION_TYPES)
    manufacturer = serializers.CharField(required=False, allow_blank=True)
    model = serializers.CharField(required=False, allow_blank=True)
    serial_number = serializers.CharField(required=False, allow_blank=True)
    latitude = serializers.DecimalField(required=False, max_digits=10, decimal_places=7)
    longitude = serializers.DecimalField(required=False, max_digits=10, decimal_places=7)
    location_description = serializers.CharField(required=False, allow_blank=True)


class DeviceConfigurationUpdateSerializer(serializers.Serializer):
    """Update device configuration"""
    
    sampling_interval = serializers.IntegerField(required=False)
    transmission_interval = serializers.IntegerField(required=False)
    latitude = serializers.DecimalField(required=False, max_digits=10, decimal_places=7)
    longitude = serializers.DecimalField(required=False, max_digits=10, decimal_places=7)
    location_description = serializers.CharField(required=False, allow_blank=True)
    metadata = serializers.JSONField(required=False)
