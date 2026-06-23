# core/models_iot.py
# FARMWISE IoT Device Integration & Sensor Management
# Connects physical devices, sensors, and data collection

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid

User = get_user_model()


# ============================================================
# IOT DEVICES & CONNECTIVITY
# ============================================================

class IoTDevice(models.Model):
    """Physical IoT sensor device"""
    
    DEVICE_TYPES = [
        ('soil_sensor', 'Soil Moisture/NPK Sensor'),
        ('weather_station', 'Weather Station'),
        ('camera', 'Camera/Image Sensor'),
        ('water_meter', 'Water Meter'),
        ('temperature', 'Temperature Sensor'),
        ('humidity', 'Humidity Sensor'),
        ('ph_sensor', 'pH Sensor'),
        ('livestock_tracker', 'Livestock GPS Tracker'),
        ('trap_monitor', 'Pest Trap Monitor'),
        ('sprinkler_controller', 'Smart Sprinkler'),
        ('livestock_scale', 'Livestock Scale'),
        ('egg_counter', 'Egg Counter'),
        ('custom', 'Custom Device'),
    ]
    
    CONNECTION_TYPES = [
        ('wifi', 'WiFi (802.11)'),
        ('lora', 'LoRaWAN'),
        ('mqtt', 'MQTT Protocol'),
        ('cellular', 'Cellular (4G/5G)'),
        ('zigbee', 'Zigbee'),
        ('bluetooth', 'Bluetooth'),
        ('manual', 'Manual Data Entry'),
        ('api', 'HTTP/REST API'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('low_battery', 'Low Battery'),
        ('disconnected', 'Disconnected'),
        ('error', 'Error'),
        ('maintenance', 'Maintenance'),
    ]
    
    # Identification
    device_id = models.CharField(max_length=50, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Ownership
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='iot_devices')
    farm = models.ForeignKey('Farm', on_delete=models.CASCADE, related_name='iot_devices')
    field = models.ForeignKey('Field', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Device details
    device_type = models.CharField(max_length=30, choices=DEVICE_TYPES)
    manufacturer = models.CharField(max_length=100, blank=True)
    model = models.CharField(max_length=100, blank=True)
    serial_number = models.CharField(max_length=100, blank=True, unique=True, null=True)
    
    # Connectivity
    connection_type = models.CharField(max_length=20, choices=CONNECTION_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='inactive')
    
    # Security
    api_key = models.CharField(max_length=100, unique=True, db_index=True)
    api_secret = models.CharField(max_length=100, blank=True)  # For HMAC signing
    
    # Location
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    location_description = models.CharField(max_length=255, blank=True, help_text='e.g., "Field A - North"}')
    
    # Power
    battery_level = models.IntegerField(default=100, validators=[MinValueValidator(0), MaxValueValidator(100)])
    power_source = models.CharField(max_length=50, choices=[
        ('battery', 'Battery'),
        ('solar', 'Solar Panel'),
        ('ac_power', 'AC Power'),
        ('hybrid', 'Solar + Battery'),
    ], default='battery')
    
    # Configuration
    sampling_interval = models.IntegerField(default=300, help_text='Seconds between data points')
    transmission_interval = models.IntegerField(default=3600, help_text='Seconds between data uploads')
    
    # Status tracking
    last_data_received = models.DateTimeField(null=True, blank=True)
    last_seen = models.DateTimeField(null=True, blank=True)
    offline_alert_sent = models.BooleanField(default=False)
    
    # Metadata
    metadata = models.JSONField(default=dict, help_text='Additional device info')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'iot_devices'
        verbose_name_plural = 'IoT Devices'
        indexes = [
            models.Index(fields=['user', 'farm', 'device_type']),
            models.Index(fields=['status', 'last_seen']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.device_id}) @ {self.farm.name}"
    
    def is_online(self):
        """Check if device reported data recently"""
        if not self.last_seen:
            return False
        elapsed = timezone.now() - self.last_seen
        # Device online if seen within 2x transmission interval
        return elapsed.total_seconds() < (self.transmission_interval * 2)
    
    def battery_status(self):
        """Get battery status"""
        if self.battery_level > 75:
            return 'excellent'
        elif self.battery_level > 50:
            return 'good'
        elif self.battery_level > 25:
            return 'warning'
        else:
            return 'critical'


class SensorType(models.Model):
    """Definition of what a sensor measures"""
    
    CODE_CHOICES = [
        ('soil_moisture', 'Soil Moisture'),
        ('air_temperature', 'Air Temperature'),
        ('air_humidity', 'Air Humidity'),
        ('rainfall', 'Rainfall'),
        ('wind_speed', 'Wind Speed'),
        ('solar_radiation', 'Solar Radiation'),
        ('soil_temperature', 'Soil Temperature'),
        ('soil_ec', 'Soil Electrical Conductivity'),
        ('soil_ph', 'Soil pH'),
        ('nitrogen', 'Nitrogen (N)'),
        ('phosphorus', 'Phosphorus (P)'),
        ('potassium', 'Potassium (K)'),
        ('crop_height', 'Crop Height'),
        ('leaf_wetness', 'Leaf Wetness'),
        ('gps_latitude', 'GPS Latitude'),
        ('gps_longitude', 'GPS Longitude'),
        ('gps_altitude', 'GPS Altitude'),
        ('animal_location_lat', 'Animal Lat'),
        ('animal_location_lng', 'Animal Lng'),
        ('animal_temperature', 'Animal Body Temperature'),
        ('animal_heart_rate', 'Animal Heart Rate'),
        ('milk_flow', 'Milk Flow'),
        ('egg_count', 'Egg Count'),
        ('water_flow', 'Water Flow Rate'),
        ('pressure', 'Pressure'),
        ('signal_strength', 'Signal Strength (RSSI)'),
        ('device_voltage', 'Device Voltage'),
    ]
    
    code = models.CharField(max_length=30, unique=True, choices=CODE_CHOICES, db_index=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Measurement details
    unit = models.CharField(max_length=50, help_text='e.g., "%", "°C", "mm", "L"')
    min_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Recommended thresholds
    optimal_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    optimal_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    warning_below = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    warning_above = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Data type
    data_type = models.CharField(max_length=20, choices=[
        ('numeric', 'Numeric'),
        ('boolean', 'Boolean'),
        ('string', 'String'),
        ('json', 'JSON'),
    ], default='numeric')
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'iot_sensor_types'
        verbose_name_plural = 'Sensor Types'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.unit})"


class SensorConfiguration(models.Model):
    """Configuration for a specific sensor on a device"""
    
    device = models.ForeignKey(IoTDevice, on_delete=models.CASCADE, related_name='sensors')
    sensor_type = models.ForeignKey(SensorType, on_delete=models.CASCADE)
    
    # Channel mapping (e.g., "analog_0", "digital_1", "temperature_1")
    channel_name = models.CharField(max_length=50)
    
    # Calibration
    calibration_offset = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    calibration_multiplier = models.DecimalField(max_digits=10, decimal_places=4, default=1)
    last_calibrated = models.DateTimeField(null=True, blank=True)
    
    # Thresholds (can override sensor type defaults)
    warning_below = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    warning_above = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'iot_sensor_configs'
        verbose_name_plural = 'Sensor Configurations'
        unique_together = [['device', 'channel_name']]
    
    def __str__(self):
        return f"{self.device.name} - {self.sensor_type.name} ({self.channel_name})"
    
    def calibrate_reading(self, raw_value):
        """Apply calibration to raw sensor reading"""
        if raw_value is None:
            return None
        calibrated = (raw_value * self.calibration_multiplier) + self.calibration_offset
        return round(calibrated, 2)


# ============================================================
# SENSOR DATA INGESTION
# ============================================================

class SensorDataPoint(models.Model):
    """Individual sensor reading"""
    
    device = models.ForeignKey(IoTDevice, on_delete=models.CASCADE, related_name='data_points')
    sensor_config = models.ForeignKey(SensorConfiguration, on_delete=models.CASCADE, related_name='data_points')
    
    # Raw data from device
    raw_value = models.CharField(max_length=1000)  # Store as string for flexibility
    
    # Processed value
    value = models.DecimalField(max_digits=12, decimal_places=4)
    
    # Quality
    signal_strength = models.IntegerField(null=True, blank=True, help_text='RSSI for wireless')
    is_valid = models.BooleanField(default=True)
    
    # Timestamp (device time vs server time)
    device_timestamp = models.DateTimeField()
    server_timestamp = models.DateTimeField(auto_now_add=True)
    
    # Aggregated metrics linked (ref: analytics.DashboardMetric)
    # dashboard_metrics = models.ManyToManyField('analytics.DashboardMetric', blank=True)
    
    class Meta:
        db_table = 'iot_sensor_data'
        verbose_name_plural = 'Sensor Data Points'
        indexes = [
            models.Index(fields=['device', 'sensor_config', '-device_timestamp']),
            models.Index(fields=['device', '-server_timestamp']),
        ]
        ordering = ['-device_timestamp']
    
    def __str__(self):
        return f"{self.sensor_config.channel_name}: {self.value} @ {self.device_timestamp}"


class SensorDataBatch(models.Model):
    """Batch submission of multiple sensor readings"""
    
    STATUS_CHOICES = [
        ('received', 'Received'),
        ('processing', 'Processing'),
        ('processed', 'Processed'),
        ('failed', 'Failed'),
    ]
    
    device = models.ForeignKey(IoTDevice, on_delete=models.CASCADE, related_name='data_batches')
    
    # Batch info
    batch_size = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='received')
    
    # Data
    raw_data = models.JSONField()  # Original payload
    processed_data_points = models.IntegerField(default=0)
    errors = models.JSONField(default=list)
    
    received_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'iot_data_batches'
        verbose_name_plural = 'Data Batches'
        ordering = ['-received_at']


# ============================================================
# DEVICE COMMANDS & CONTROL
# ============================================================

class DeviceCommand(models.Model):
    """Command to send to a device"""
    
    COMMAND_TYPES = [
        ('configure', 'Configuration Update'),
        ('calibrate', 'Calibration'),
        ('restart', 'Restart Device'),
        ('update_firmware', 'Firmware Update'),
        ('set_interval', 'Set Sampling Interval'),
        ('control_sprinkler', 'Control Sprinkler'),
        ('control_light', 'Control Light'),
        ('alert_threshold', 'Update Alert Threshold'),
        ('custom', 'Custom Command'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('acknowledged', 'Acknowledged'),
        ('executed', 'Executed'),
        ('failed', 'Failed'),
    ]
    
    device = models.ForeignKey(IoTDevice, on_delete=models.CASCADE, related_name='commands')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    command_type = models.CharField(max_length=30, choices=COMMAND_TYPES)
    command_text = models.TextField()  # Actual command payload
    
    parameters = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    retry_count = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    max_retries = models.IntegerField(default=3)
    
    # Execution
    sent_at = models.DateTimeField(null=True, blank=True)
    executed_at = models.DateTimeField(null=True, blank=True)
    result = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()  # When command expires if not executed
    
    class Meta:
        db_table = 'iot_device_commands'
        verbose_name_plural = 'Device Commands'
        indexes = [
            models.Index(fields=['device', 'status', 'created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.device.name}: {self.command_type} ({self.status})"


# ============================================================
# DEVICE HEALTH & MAINTENANCE
# ============================================================

class DeviceHealth(models.Model):
    """Track device health metrics over time"""
    
    device = models.OneToOneField(IoTDevice, on_delete=models.CASCADE, related_name='health')
    
    # Status counters
    total_readings = models.BigIntegerField(default=0)
    successful_readings = models.BigIntegerField(default=0)
    failed_readings = models.BigIntegerField(default=0)
    
    # Uptime
    uptime_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    consecutive_failures = models.IntegerField(default=0)
    
    # Signal quality
    avg_signal_strength = models.IntegerField(null=True, blank=True)
    
    # Last errors
    last_error = models.CharField(max_length=500, blank=True)
    last_error_time = models.DateTimeField(null=True, blank=True)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'iot_device_health'
        verbose_name_plural = 'Device Health'


class DeviceMaintenanceLog(models.Model):
    """maintenance and service history"""
    
    MAINTENANCE_TYPES = [
        ('battery_replacement', 'Battery Replacement'),
        ('calibration', 'Calibration'),
        ('cleaning', 'Cleaning'),
        ('repair', 'Repair'),
        ('firmware_update', 'Firmware Update'),
        ('relocation', 'Relocation'),
        ('inspection', 'Inspection'),
    ]
    
    device = models.ForeignKey(IoTDevice, on_delete=models.CASCADE, related_name='maintenance_logs')
    
    maintenance_type = models.CharField(max_length=30, choices=MAINTENANCE_TYPES)
    performed_by = models.CharField(max_length=255)
    notes = models.TextField()
    
    before_battery = models.IntegerField(null=True, blank=True)
    after_battery = models.IntegerField(null=True, blank=True)
    
    performed_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'iot_maintenance_logs'
        verbose_name_plural = 'Maintenance Logs'
        ordering = ['-performed_at']


# ============================================================
# DEVICE PROVISIONING & AUTHENTICATION
# ============================================================

class DeviceProvisioningToken(models.Model):
    """One-time token for device provisioning"""
    
    token = models.CharField(max_length=100, unique=True, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    farm = models.ForeignKey('Farm', on_delete=models.CASCADE)
    
    device_type = models.CharField(max_length=30, choices=IoTDevice.DEVICE_TYPES)
    device_name = models.CharField(max_length=255)
    
    is_used = models.BooleanField(default=False)
    created_device = models.OneToOneField(
        IoTDevice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='provisioning_token'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()  # 24-hour expiry
    used_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'iot_provisioning_tokens'
        verbose_name_plural = 'Provisioning Tokens'
        ordering = ['-created_at']
