# core/iot/views.py
# IoT Device Management REST API Endpoints

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound
from django.utils import timezone
from django.db.models import Q, F, Count
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from datetime import timedelta
import logging

from core.models_iot import (
    IoTDevice, SensorType, SensorConfiguration,
    SensorDataPoint, SensorDataBatch, DeviceCommand,
    DeviceHealth, DeviceMaintenanceLog, DeviceProvisioningToken
)
from core.models_analytics import DashboardMetric
from .serializers import (
    IoTDeviceListSerializer, IoTDeviceDetailSerializer,
    SensorTypeSerializer, SensorConfigurationSerializer,
    SensorDataPointSerializer, SensorDataBatchSerializer,
    DeviceCommandSerializer, DeviceHealthSerializer,
    DeviceMaintenanceLogSerializer, DeviceProvisioningTokenSerializer,
    BulkSensorDataSubmissionSerializer, QuickSensorDataSubmissionSerializer,
    DeviceRegistrationSerializer, DeviceConfigurationUpdateSerializer
)

logger = logging.getLogger(__name__)


# ============================================================
# PERMISSIONS
# ============================================================

class IsDeviceOwner(permissions.BasePermission):
    """Permission: user owns the device"""
    
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class IsDeviceOwnerOrReadOnly(permissions.BasePermission):
    """Permission: user owns device or read-only"""
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            # Allow read without ownership check
            return True
        return obj.user == request.user


class ApiKeyAuthentication(permissions.BasePermission):
    """Authenticate device via API key (for data submission)"""
    
    def has_permission(self, request, view):
        # This is checked in view methods
        return True


# ============================================================
# DEVICE MANAGEMENT VIEWSETS
# ============================================================

class IoTDeviceViewSet(viewsets.ModelViewSet):
    """Manage IoT devices"""
    
    permission_classes = [permissions.IsAuthenticated, IsDeviceOwner]
    filterset_fields = ['device_type', 'connection_type', 'status', 'farm']
    search_fields = ['name', 'device_id', 'serial_number']
    ordering_fields = ['created_at', 'last_seen', 'battery_level']
    ordering = ['-last_seen']
    
    def get_queryset(self):
        """Filter to user's devices"""
        return IoTDevice.objects.filter(
            user=self.request.user
        ).select_related('farm', 'field', 'health').prefetch_related('sensors')
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return IoTDeviceDetailSerializer
        return IoTDeviceListSerializer
    
    def perform_create(self, serializer):
        """Create new device"""
        device = serializer.save(user=self.request.user)
        # Create health record
        DeviceHealth.objects.get_or_create(device=device)
        logger.info(f"Device created: {device.device_id} for user {self.request.user}")
    
    @action(detail=True, methods=['post'])
    def set_status(self, request, pk=None):
        """Update device status"""
        device = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in dict(IoTDevice.STATUS_CHOICES):
            raise ValidationError({'status': 'Invalid status'})
        
        device.status = new_status
        device.save()
        return Response({'status': device.status})
    
    @action(detail=True, methods=['post'])
    def update_location(self, request, pk=None):
        """Update device location"""
        device = self.get_object()
        serializer = DeviceConfigurationUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        if 'latitude' in serializer.validated_data:
            device.latitude = serializer.validated_data['latitude']
        if 'longitude' in serializer.validated_data:
            device.longitude = serializer.validated_data['longitude']
        if 'location_description' in serializer.validated_data:
            device.location_description = serializer.validated_data['location_description']
        
        device.save()
        return Response(IoTDeviceDetailSerializer(device).data)
    
    @action(detail=True, methods=['get'])
    def latest_data(self, request, pk=None):
        """Get latest sensor readings"""
        device = self.get_object()
        limit = request.query_params.get('limit', 100)
        
        readings = SensorDataPoint.objects.filter(
            device=device
        ).select_related('sensor_config__sensor_type').order_by('-device_timestamp')[:int(limit)]
        
        serializer = SensorDataPointSerializer(readings, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def commands(self, request, pk=None):
        """Get pending commands for device"""
        device = self.get_object()
        pending = DeviceCommand.objects.filter(
            device=device,
            status__in=['pending', 'sent']
        ).order_by('-created_at')
        
        serializer = DeviceCommandSerializer(pending, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def send_command(self, request, pk=None):
        """Send command to device"""
        device = self.get_object()
        
        serializer = DeviceCommandSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        command = serializer.save(
            device=device,
            user=request.user,
            expires_at=timezone.now() + timedelta(hours=24)
        )
        
        logger.info(f"Command created for {device.device_id}: {command.command_type}")
        return Response(DeviceCommandSerializer(command).data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def record_maintenance(self, request, pk=None):
        """Record maintenance performed on device"""
        device = self.get_object()
        
        serializer = DeviceMaintenanceLogSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        log = serializer.save(device=device)
        
        # Update battery if provided
        if log.after_battery is not None:
            device.battery_level = log.after_battery
            device.save()
        
        return Response(DeviceMaintenanceLogSerializer(log).data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def health(self, request, pk=None):
        """Get device health metrics"""
        device = self.get_object()
        health = DeviceHealth.objects.get(device=device)
        serializer = DeviceHealthSerializer(health)
        return Response(serializer.data)


class SensorConfigurationViewSet(viewsets.ModelViewSet):
    """Manage device sensors"""
    
    permission_classes = [permissions.IsAuthenticated, IsDeviceOwner]
    serializer_class = SensorConfigurationSerializer
    
    def get_queryset(self):
        device_id = self.kwargs.get('device_pk')
        return SensorConfiguration.objects.filter(
            device__user=self.request.user,
            device_id=device_id
        ).select_related('sensor_type')
    
    def perform_create(self, serializer):
        device_id = self.kwargs.get('device_pk')
        device = IoTDevice.objects.get(id=device_id, user=self.request.user)
        serializer.save(device=device)
    
    @action(detail=True, methods=['post'])
    def calibrate(self, request, pk=None, device_pk=None):
        """Calibrate sensor"""
        sensor = self.get_object()
        
        offset = request.data.get('offset', 0)
        multiplier = request.data.get('multiplier', 1)
        
        sensor.calibration_offset = offset
        sensor.calibration_multiplier = multiplier
        sensor.last_calibrated = timezone.now()
        sensor.save()
        
        return Response(SensorConfigurationSerializer(sensor).data)


class SensorTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """List available sensor types"""
    
    permission_classes = [permissions.IsAuthenticated]
    queryset = SensorType.objects.filter(is_active=True)
    serializer_class = SensorTypeSerializer
    filterset_fields = ['code', 'data_type']
    search_fields = ['name', 'unit']
    ordering_fields = ['name']
    ordering = ['name']


# ============================================================
# DATA SUBMISSION ENDPOINTS
# ============================================================

class SensorDataSubmissionViewSet(viewsets.ViewSet):
    """Handle sensor data ingestion"""
    
    permission_classes = [ApiKeyAuthentication]
    
    def authenticate_device(self, api_key):
        """Authenticate device via API key"""
        try:
            device = IoTDevice.objects.get(api_key=api_key)
            return device
        except IoTDevice.DoesNotExist:
            raise PermissionDenied("Invalid API key")
    
    @action(detail=False, methods=['post'])
    def submit_bulk(self, request):
        """Bulk data submission: multiple readings in one request"""
        serializer = BulkSensorDataSubmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Authenticate
        device = self.authenticate_device(serializer.validated_data['api_key'])
        
        timestamp = serializer.validated_data['timestamp']
        data_points_list = serializer.validated_data['data_points']
        
        with transaction.atomic():
            batch = SensorDataBatch.objects.create(
                device=device,
                batch_size=len(data_points_list),
                raw_data=serializer.validated_data,
                status='processing'
            )
            
            created_readings = []
            errors = []
            
            for point_data in data_points_list:
                try:
                    channel = point_data.get('channel')
                    raw_value = point_data.get('value')
                    
                    # Find sensor configuration
                    sensor_config = SensorConfiguration.objects.get(
                        device=device,
                        channel_name=channel,
                        is_active=True
                    )
                    
                    # Calibrate value
                    calibrated_value = sensor_config.calibrate_reading(raw_value)
                    
                    # Create data point
                    data_point = SensorDataPoint.objects.create(
                        device=device,
                        sensor_config=sensor_config,
                        raw_value=str(raw_value),
                        value=calibrated_value,
                        device_timestamp=timestamp,
                        signal_strength=point_data.get('signal_strength'),
                        is_valid=True
                    )
                    
                    created_readings.append(data_point)
                    
                    # Link to analytics metric if applicable
                    self._create_analytics_metric(device, sensor_config, calibrated_value, timestamp)
                    
                except Exception as e:
                    errors.append({
                        'channel': point_data.get('channel'),
                        'error': str(e)
                    })
                    logger.error(f"Error processing data point: {e}")
            
            # Update batch
            batch.processed_data_points = len(created_readings)
            batch.errors = errors
            batch.status = 'processed' if not errors else 'failed'
            batch.processed_at = timezone.now()
            batch.save()
            
            # Update device metadata
            device.last_data_received = timezone.now()
            device.last_seen = timezone.now()
            if 'battery_level' in serializer.validated_data:
                device.battery_level = serializer.validated_data['battery_level']
            device.offline_alert_sent = False
            device.save()
            
            # Update health
            health = DeviceHealth.objects.get(device=device)
            health.total_readings += len(created_readings)
            health.successful_readings += len(created_readings)
            health.consecutive_failures = 0
            if 'signal_strength' in serializer.validated_data:
                health.avg_signal_strength = serializer.validated_data['signal_strength']
            health.save()
        
        return Response({
            'batch_id': batch.id,
            'total_submitted': len(data_points_list),
            'successfully_processed': len(created_readings),
            'errors': errors
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def submit_single(self, request):
        """Single data point submission"""
        serializer = QuickSensorDataSubmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        device = self.authenticate_device(serializer.validated_data['api_key'])
        
        # Find sensor configuration
        try:
            sensor_config = SensorConfiguration.objects.get(
                device=device,
                channel_name=serializer.validated_data['channel'],
                is_active=True
            )
        except SensorConfiguration.DoesNotExist:
            raise ValidationError({'channel': 'Sensor not configured'})
        
        # Calibrate
        calibrated_value = sensor_config.calibrate_reading(
            serializer.validated_data['value']
        )
        
        # Create data point
        data_point = SensorDataPoint.objects.create(
            device=device,
            sensor_config=sensor_config,
            raw_value=str(serializer.validated_data['value']),
            value=calibrated_value,
            device_timestamp=serializer.validated_data['timestamp'],
            signal_strength=serializer.validated_data.get('signal_strength'),
            is_valid=True
        )
        
        # Link to analytics
        self._create_analytics_metric(
            device,
            sensor_config,
            calibrated_value,
            serializer.validated_data['timestamp']
        )
        
        # Update device
        device.last_data_received = timezone.now()
        device.last_seen = timezone.now()
        if 'battery_level' in serializer.validated_data:
            device.battery_level = serializer.validated_data['battery_level']
        device.save()
        
        return Response(
            SensorDataPointSerializer(data_point).data,
            status=status.HTTP_201_CREATED
        )
    
    def _create_analytics_metric(self, device, sensor_config, value, timestamp):
        """Map sensor data to analytics dashboard metric"""
        
        sensor_to_metric_map = {
            'soil_moisture': 'soil_moisture',
            'air_temperature': 'temperature',
            'air_humidity': 'humidity',
            'rainfall': 'rainfall',
            'soil_temperature': 'soil_temperature',
            'soil_ph': 'ph',
            'nitrogen': 'nitrogen',
            'crop_height': 'crop_health',
            'water_flow': 'water_usage',
            'pest_count': 'pest_count',
        }
        
        metric_type = sensor_to_metric_map.get(sensor_config.sensor_type.code)
        if not metric_type:
            return
        
        # Create or update dashboard metric
        metric, created = DashboardMetric.objects.get_or_create(
            farm=device.farm,
            metric_type=metric_type,
            defaults={'value': float(value), 'source': 'iot_device'}
        )
        
        if not created:
            metric.value = float(value)
            metric.save()


class SensorDataViewSet(viewsets.ReadOnlyModelViewSet):
    """Query historical sensor data"""
    
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SensorDataPointSerializer
    filterset_fields = ['device', 'sensor_config', 'is_valid']
    search_fields = ['sensor_config__channel_name']
    ordering_fields = ['device_timestamp', 'server_timestamp']
    ordering = ['-device_timestamp']
    
    def get_queryset(self):
        """Filter to user's devices"""
        return SensorDataPoint.objects.filter(
            device__user=self.request.user
        ).select_related('device', 'sensor_config__sensor_type')


# ============================================================
# DEVICE PROVISIONING
# ============================================================

class DeviceProvisioningViewSet(viewsets.ViewSet):
    """Device provisioning and onboarding"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def create_token(self, request):
        """Create provisioning token for new device"""
        
        farm_id = request.data.get('farm')
        device_type = request.data.get('device_type')
        device_name = request.data.get('device_name')
        
        if not all([farm_id, device_type, device_name]):
            raise ValidationError({
                'farm': 'Farm ID required',
                'device_type': 'Device type required',
                'device_name': 'Device name required'
            })
        
        token_obj = DeviceProvisioningToken.objects.create(
            token=str(uuid.uuid4()),
            user=request.user,
            farm_id=farm_id,
            device_type=device_type,
            device_name=device_name,
            expires_at=timezone.now() + timedelta(hours=24)
        )
        
        serializer = DeviceProvisioningTokenSerializer(token_obj)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    @method_decorator(csrf_exempt)
    def register_device(self, request):
        """Register new device using provisioning token"""
        
        serializer = DeviceRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Validate token
        try:
            prov_token = DeviceProvisioningToken.objects.get(
                token=serializer.validated_data['provisioning_token'],
                is_used=False,
                expires_at__gt=timezone.now()
            )
        except DeviceProvisioningToken.DoesNotExist:
            raise ValidationError({'token': 'Invalid or expired provisioning token'})
        
        # Create device
        with transaction.atomic():
            import uuid
            device = IoTDevice.objects.create(
                device_id=f"DEV-{prov_token.farm.id}-{uuid.uuid4().hex[:8].upper()}",
                name=serializer.validated_data['device_name'],
                user=prov_token.user,
                farm=prov_token.farm,
                device_type=prov_token.device_type,
                connection_type=serializer.validated_data.get('connection_type'),
                manufacturer=serializer.validated_data.get('manufacturer', ''),
                model=serializer.validated_data.get('model', ''),
                serial_number=serializer.validated_data.get('serial_number'),
                latitude=serializer.validated_data.get('latitude'),
                longitude=serializer.validated_data.get('longitude'),
                location_description=serializer.validated_data.get('location_description', ''),
                api_key=str(uuid.uuid4()),
                status='active'
            )
            
            # Create health record
            DeviceHealth.objects.create(device=device)
            
            # Mark token as used
            prov_token.is_used = True
            prov_token.created_device = device
            prov_token.used_at = timezone.now()
            prov_token.save()
        
        logger.info(f"Device provisioned: {device.device_id}")
        return Response(
            IoTDeviceDetailSerializer(device).data,
            status=status.HTTP_201_CREATED
        )
