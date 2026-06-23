# core/iot/urls.py
# IoT Device API URL Configuration

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from .views import (
    IoTDeviceViewSet, SensorConfigurationViewSet, SensorTypeViewSet,
    SensorDataSubmissionViewSet, SensorDataViewSet,
    DeviceProvisioningViewSet
)

# Main router
router = DefaultRouter()
router.register(r'devices', IoTDeviceViewSet, basename='iot-device')
router.register(r'sensor-types', SensorTypeViewSet, basename='sensor-type')
router.register(r'data', SensorDataViewSet, basename='sensor-data')
router.register(r'provisioning', DeviceProvisioningViewSet, basename='device-provisioning')

# Nested router for device sensors
devices_router = routers.NestedDefaultRouter(router, 'devices', lookup='device')
devices_router.register(r'sensors', SensorConfigurationViewSet, basename='device-sensors')

# Data submission endpoints (special handling)
data_submission_patterns = [
    path('submit/bulk/', SensorDataSubmissionViewSet.as_view({
        'post': 'submit_bulk'
    }), name='submit-bulk-data'),
    path('submit/single/', SensorDataSubmissionViewSet.as_view({
        'post': 'submit_single'
    }), name='submit-single-data'),
]

urlpatterns = [
    path('', include(router.urls)),
    path('', include(devices_router.urls)),
    path('data/', include(data_submission_patterns)),
]
