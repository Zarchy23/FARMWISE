# core/api/views_location.py
# GPS Mapping and Location API Views

from rest_framework import viewsets, status, views
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
import logging

from core.models_location import (
    FarmLocation, FarmField, FarmFieldZone, FarmGeofenceAlert,
    FarmLocationAnalytics, FarmCropRotationPlan, FarmProximityAnalysis
)
from core.api.serializers_location import (
    FarmLocationSerializer, FieldSerializer, FieldDetailSerializer, FarmFieldZoneSerializer,
    FarmGeofenceAlertSerializer, FarmCropRotationPlanSerializer, FarmProximityAnalysisSerializer,
    FarmLocationAnalyticsSerializer
)
from core.services.location_service import LocationService

logger = logging.getLogger(__name__)


class FarmLocationViewSet(viewsets.ModelViewSet):
    """Manage farm locations with GPS coordinates"""
    serializer_class = FarmLocationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter locations for user's farms"""
        return FarmLocation.objects.filter(farm__owner=self.request.user)
    
    @action(detail=False, methods=['post'])
    def create_location(self, request):
        """Create or update farm location with spatial data"""
        try:
            farm_id = request.data.get('farm_id')
            latitude = request.data.get('latitude')
            longitude = request.data.get('longitude')
            altitude = request.data.get('altitude')
            address = request.data.get('address', '')
            region = request.data.get('region', '')
            district = request.data.get('district', '')
            
            from core.models import Farm
            farm = Farm.objects.get(id=farm_id, owner=request.user)
            
            location = LocationService.create_farm_location(
                farm=farm,
                latitude=latitude,
                longitude=longitude,
                altitude=altitude,
                address=address,
                region=region,
                district=district
            )
            
            serializer = self.get_serializer(location)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            logger.error(f"Error creating farm location: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def by_region(self, request):
        """Get farm locations by region"""
        region = request.query_params.get('region')
        if not region:
            return Response({'error': 'region parameter required'}, status=status.HTTP_400_BAD_REQUEST)
        
        locations = self.get_queryset().filter(region=region)
        serializer = self.get_serializer(locations, many=True)
        return Response(serializer.data)


class FieldViewSet(viewsets.ModelViewSet):
    """Manage farm fields with boundaries"""
    permission_classes = [IsAuthenticated]
    filterset_fields = ['farm', 'field_type', 'status']
    search_fields = ['name', 'current_crop']
    
    def get_queryset(self):
        """Filter fields for user's farms"""
        return FarmField.objects.filter(farm__owner=self.request.user).select_related('farm')
    
    def get_serializer_class(self):
        """Use detail serializer for retrieve"""
        if self.action == 'retrieve':
            return FieldDetailSerializer
        return FieldSerializer
    
    @action(detail=False, methods=['post'])
    def create_with_boundary(self, request):
        """Create a field with boundary coordinates"""
        try:
            farm_id = request.data.get('farm_id')
            name = request.data.get('name')
            field_type = request.data.get('field_type', 'arable')
            boundary_coords = request.data.get('boundary_coords')  # List of [lon, lat] pairs
            area_hectares = request.data.get('area_hectares', 0.0)
            
            from core.models import Farm
            farm = Farm.objects.get(id=farm_id, owner=request.user)
            
            field = LocationService.create_field(
                farm=farm,
                name=name,
                field_type=field_type,
                boundary_coords=boundary_coords,
                area_hectares=area_hectares
            )
            
            serializer = self.get_serializer(field)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            logger.error(f"Error creating field: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def zones(self, request, pk=None):
        """Get all zones in a field"""
        field = self.get_object()
        zones = field.zones.all()
        
        serializer = FarmFieldZoneSerializer(zones, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def rotation_plan(self, request, pk=None):
        """Get crop rotation plan for field"""
        field = self.get_object()
        
        plan = LocationService.generate_crop_rotation_plan(field)
        
        if plan:
            serializer = FarmCropRotationPlanSerializer(plan)
            return Response(serializer.data)
        else:
            return Response({'error': 'Could not generate rotation plan'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def proximity_analysis(self, request, pk=None):
        """Get proximity analysis for field"""
        field = self.get_object()
        
        proximity = LocationService.analyze_field_proximity(field)
        
        if proximity:
            serializer = FarmProximityAnalysisSerializer(proximity)
            return Response(serializer.data)
        else:
            return Response({'error': 'Could not analyze proximity'}, status=status.HTTP_400_BAD_REQUEST)


class FarmFieldZoneViewSet(viewsets.ModelViewSet):
    """Manage field zones"""
    serializer_class = FarmFieldZoneSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['field', 'zone_type']
    
    def get_queryset(self):
        """Filter zones for user's farms"""
        return FarmFieldZone.objects.filter(field__farm__owner=self.request.user)
    
    @action(detail=False, methods=['post'])
    def create_zone(self, request):
        """Create a field zone"""
        try:
            field_id = request.data.get('field_id')
            name = request.data.get('name')
            zone_type = request.data.get('zone_type')
            boundary_coords = request.data.get('boundary_coords')
            area_hectares = request.data.get('area_hectares', 0.0)
            severity_level = request.data.get('severity_level', 1)
            
            field = FarmField.objects.get(id=field_id, farm__owner=request.user)
            
            zone = LocationService.create_field_zone(
                field=field,
                name=name,
                zone_type=zone_type,
                boundary_coords=boundary_coords,
                area_hectares=area_hectares,
                severity_level=severity_level
            )
            
            serializer = self.get_serializer(zone)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            logger.error(f"Error creating field zone: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class FarmGeofenceAlertViewSet(viewsets.ModelViewSet):
    """Manage geofence alerts"""
    serializer_class = FarmGeofenceAlertSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['farm', 'alert_type', 'is_active']
    
    def get_queryset(self):
        """Filter geofences for user's farms"""
        return FarmGeofenceAlert.objects.filter(farm__owner=self.request.user)
    
    @action(detail=False, methods=['post'])
    def create_geofence(self, request):
        """Create a geofence"""
        try:
            farm_id = request.data.get('farm_id')
            name = request.data.get('name')
            alert_type = request.data.get('alert_type')
            boundary_coords = request.data.get('boundary_coords')
            notify_on_entry = request.data.get('notify_on_entry', False)
            notify_on_exit = request.data.get('notify_on_exit', False)
            
            from core.models import Farm
            farm = Farm.objects.get(id=farm_id, owner=request.user)
            
            geofence = LocationService.create_geofence(
                farm=farm,
                name=name,
                alert_type=alert_type,
                boundary_coords=boundary_coords,
                notify_on_entry=notify_on_entry,
                notify_on_exit=notify_on_exit
            )
            
            serializer = self.get_serializer(geofence)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            logger.error(f"Error creating geofence: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def check_point(self, request, pk=None):
        """Check if GPS point is within geofence"""
        geofence = self.get_object()
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        
        is_inside = LocationService.check_point_in_geofence(latitude, longitude, geofence.id)
        
        return Response({
            'geofence_id': geofence.id,
            'geofence_name': geofence.name,
            'point': {'latitude': latitude, 'longitude': longitude},
            'is_inside': is_inside
        })


class FarmLocationAnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    """View location-based analytics"""
    serializer_class = FarmLocationAnalyticsSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['farm', 'date']
    ordering_fields = ['date', 'avg_yield_per_hectare']
    
    def get_queryset(self):
        """Filter analytics for user's farms"""
        return FarmLocationAnalytics.objects.filter(farm__owner=self.request.user).order_by('-date')
    
    @action(detail=False, methods=['post'])
    def calculate_for_farm(self, request):
        """Calculate analytics for a farm"""
        try:
            farm_id = request.data.get('farm_id')
            
            from core.models import Farm
            farm = Farm.objects.get(id=farm_id, owner=request.user)
            
            analytics = LocationService.calculate_location_analytics(farm)
            
            if analytics:
                serializer = self.get_serializer(analytics)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response({'error': 'Could not calculate analytics'}, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.error(f"Error calculating analytics: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class LocationDashboardView(views.APIView):
    """Dashboard for GPS mapping and location analytics"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get location dashboard data"""
        try:
            from core.models import Farm
            
            farms = Farm.objects.filter(owner=request.user)
            
            # Get all fields
            fields = FarmField.objects.filter(farm__in=farms)
            
            # Get all geofences
            geofences = FarmGeofenceAlert.objects.filter(farm__in=farms)
            
            # Get latest analytics
            analytics = FarmLocationAnalytics.objects.filter(farm__in=farms).order_by('-date')[:5]
            
            # Get crop rotation plans
            rotation_plans = FarmCropRotationPlan.objects.filter(field__in=fields)
            
            return Response({
                'farm_count': farms.count(),
                'field_count': fields.count(),
                'geofence_count': geofences.count(),
                'fields': FieldSerializer(fields[:10], many=True).data,
                'geofences': FarmGeofenceAlertSerializer(geofences[:5], many=True).data,
                'recent_analytics': FarmLocationAnalyticsSerializer(analytics, many=True).data,
                'rotation_plans': FarmCropRotationPlanSerializer(rotation_plans[:5], many=True).data,
                'summary': {
                    'total_cultivated_area': sum(f.area_hectares for f in fields),
                    'fields_with_rotation_plans': rotation_plans.count(),
                    'active_geofences': geofences.filter(is_active=True).count()
                }
            })
        
        except Exception as e:
            logger.error(f"Error loading location dashboard: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
