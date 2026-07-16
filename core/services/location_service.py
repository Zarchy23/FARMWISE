# core/services/location_service.py
# GPS Mapping and Location Intelligence Service

import logging
import math
from django.db.models import Avg, Sum, Q
from django.utils import timezone

from core.models_location import (
    FarmLocation, FarmField, FarmFieldZone, FarmGeofenceAlert,
    FarmLocationAnalytics, FarmCropRotationPlan, FarmProximityAnalysis
)

logger = logging.getLogger(__name__)


class LocationService:
    """Service for GPS mapping and location-based operations"""
    
    @staticmethod
    def create_farm_location(farm, latitude, longitude, altitude=None, address='', region='', district=''):
        """Create or update farm location with spatial data"""
        try:
            # Store coordinates as JSON
            coordinates = {'lat': latitude, 'lon': longitude}
            
            location, created = FarmLocation.objects.update_or_create(
                farm=farm,
                defaults={
                    'coordinates': coordinates,
                    'latitude': latitude,
                    'longitude': longitude,
                    'altitude': altitude,
                    'address': address,
                    'region': region,
                    'district': district,
                }
            )
            
            logger.info(f"Created/Updated location for farm {farm.name}")
            return location
        
        except Exception as e:
            logger.error(f"Error creating farm location: {str(e)}")
            raise
    
    @staticmethod
    def create_field(farm, name, field_type, boundary_coords, area_hectares, soil_type='', soil_fertility='good'):
        """Create a farm field with boundary polygon"""
        try:
            # Store boundary as GeoJSON coordinates
            # boundary_coords should be list of (lon, lat) tuples forming a closed polygon
            if len(boundary_coords) < 3:
                raise ValueError("Field boundary must have at least 3 points")
            
            # Store as GeoJSON polygon
            boundary_geojson = {
                "type": "Polygon",
                "coordinates": [boundary_coords]
            }
            
            field = FarmField.objects.create(
                farm=farm,
                name=name,
                field_type=field_type,
                boundary=boundary_geojson,
                area_hectares=area_hectares,
                soil_type=soil_type,
                soil_fertility=soil_fertility,
            )
            
            logger.info(f"Created field {field.name} in farm {farm.name}")
            return field
        
        except Exception as e:
            logger.error(f"Error creating field: {str(e)}")
            raise
    
    @staticmethod
    def create_field_zone(field, name, zone_type, boundary_coords, area_hectares, severity_level=1):
        """Create a sub-zone within a field"""
        try:
            # Store as GeoJSON
            boundary_geojson = {
                "type": "Polygon",
                "coordinates": [boundary_coords]
            }
            
            zone = FieldZone.objects.create(
                field=field,
                name=name,
                zone_type=zone_type,
                boundary=boundary_geojson,
                area_hectares=area_hectares,
                severity_level=severity_level,
            )
            
            logger.info(f"Created zone {zone.name} in field {field.name}")
            return zone
        
        except Exception as e:
            logger.error(f"Error creating field zone: {str(e)}")
            raise
    
    @staticmethod
    def create_geofence(farm, name, alert_type, boundary_coords, notify_on_entry=False, notify_on_exit=False):
        """Create a geofence boundary for alerts"""
        try:
            # Store as GeoJSON
            boundary_geojson = {
                "type": "Polygon",
                "coordinates": [boundary_coords]
            }
            
            geofence = GeofenceAlert.objects.create(
                farm=farm,
                name=name,
                alert_type=alert_type,
                boundary=boundary_geojson,
                notify_on_entry=notify_on_entry,
                notify_on_exit=notify_on_exit,
            )
            
            logger.info(f"Created geofence {geofence.name} for farm {farm.name}")
            return geofence
        
        except Exception as e:
            logger.error(f"Error creating geofence: {str(e)}")
            raise
    
    @staticmethod
    def find_nearby_resources(field, resource_type='water', radius_km=5):
        """Find nearby resources (water sources, markets, etc.) using distance queries"""
        try:
            # This would integrate with external data sources
            # For now, return a template structure
            
            if not field.boundary:
                return []
            
            # Extract center from boundary coordinates
            try:
                coords = field.boundary['coordinates'][0]
                # Calculate center point
                center_lon = sum(c[0] for c in coords) / len(coords)
                center_lat = sum(c[1] for c in coords) / len(coords)
            except (KeyError, IndexError, TypeError):
                return []
            
            # In a real implementation, query external resource database
            # For now, return template
            results = {
                'resource_type': resource_type,
                'radius_km': radius_km,
                'center': {'lat': center_lat, 'lon': center_lon},
                'nearby_resources': []
            }
            
            return results
        
        except Exception as e:
            logger.error(f"Error finding nearby resources: {str(e)}")
            return []
    
    @staticmethod
    def calculate_field_area_from_boundary(boundary):
        """Calculate area from polygon boundary (in hectares)"""
        try:
            if not boundary or not isinstance(boundary, dict):
                return 0.0
            
            # Extract coordinates from GeoJSON
            try:
                coords = boundary.get('coordinates', [[]])[0]
                if len(coords) < 3:
                    return 0.0
                
                # Use Shoelace formula for simple polygon area calculation
                area_sq_m = 0
                for i in range(len(coords) - 1):
                    x1, y1 = coords[i]
                    x2, y2 = coords[i + 1]
                    area_sq_m += (x2 - x1) * (y2 + y1)
                
                area_sq_m = abs(area_sq_m) / 2
                # Rough conversion (this is simplified; real calculation would use proper projection)
                # At equator: 1 degree ≈ 111 km
                area_sq_m = area_sq_m * (111000 * 111000)  # Convert degree^2 to approx m^2
                
                # Convert to hectares (1 hectare = 10,000 sq m)
                area_hectares = area_sq_m / 10000
                
                return round(max(0, area_hectares), 2)
            except (KeyError, IndexError, TypeError, ValueError):
                return 0.0
        
        except Exception as e:
            logger.error(f"Error calculating field area: {str(e)}")
            return 0.0
    
    @staticmethod
    def generate_crop_rotation_plan(field):
        """Generate crop rotation recommendations based on field history and soil"""
        try:
            current_crop = field.current_crop or 'Not specified'
            soil_type = field.soil_type or 'Unknown'
            
            # Define rotation plans based on crop history
            rotation_plans = {
                'maize': {
                    'year_1': 'Legumes (Beans/Peas)',
                    'year_2': 'Root Vegetables',
                    'year_3': 'Green Manure',
                    'year_4': 'Maize',
                    'type': 'legume_cereal',
                    'benefits': [
                        'Nitrogen fixation restores soil nitrogen',
                        'Breaks pest cycles',
                        'Improves soil structure',
                        'Reduces disease pressure'
                    ]
                },
                'wheat': {
                    'year_1': 'Legumes',
                    'year_2': 'Potatoes/Vegetables',
                    'year_3': 'Cereal (Barley)',
                    'year_4': 'Wheat',
                    'type': 'diverse',
                    'benefits': [
                        'Diverse crop types',
                        'Disease reduction',
                        'Improved soil fertility'
                    ]
                },
                'beans': {
                    'year_1': 'Cereal (Maize/Wheat)',
                    'year_2': 'Root Crops',
                    'year_3': 'Leafy Vegetables',
                    'year_4': 'Legumes',
                    'type': 'legume_cereal',
                    'benefits': [
                        'Allows nitrogen recovery',
                        'Varied crop types',
                        'Pest break'
                    ]
                }
            }
            
            plan_data = rotation_plans.get(current_crop.lower(), {
                'year_1': 'Legumes',
                'year_2': 'Root Crops',
                'year_3': 'Cereals',
                'year_4': 'Current Crop',
                'type': 'diverse',
                'benefits': ['Pest management', 'Soil improvement']
            })
            
            rotation_plan, created = CropRotationPlan.objects.update_or_create(
                field=field,
                defaults={
                    'current_crop': current_crop,
                    'current_season': 1,
                    'year_1_recommendation': plan_data['year_1'],
                    'year_2_recommendation': plan_data['year_2'],
                    'year_3_recommendation': plan_data['year_3'],
                    'year_4_recommendation': plan_data['year_4'],
                    'rotation_type': plan_data['type'],
                    'benefits': plan_data['benefits'],
                    'soil_improvement': f'Crop rotation improves soil for {current_crop}',
                    'pest_break_benefits': 'Alternating crops breaks pest and disease cycles'
                }
            )
            
            logger.info(f"Generated rotation plan for field {field.name}")
            return rotation_plan
        
        except Exception as e:
            logger.error(f"Error generating crop rotation plan: {str(e)}")
            return None
    
    @staticmethod
    def analyze_field_proximity(field):
        """Analyze field proximity to resources"""
        try:
            if not field.boundary:
                return None
            
            # Extract center from boundary
            try:
                coords = field.boundary['coordinates'][0]
                center_lon = sum(c[0] for c in coords) / len(coords)
                center_lat = sum(c[1] for c in coords) / len(coords)
            except (KeyError, IndexError, TypeError):
                return None
            
            # Calculate accessibility scores (in a real app, query actual resources)
            proximity = ProximityAnalysis.objects.create(
                field=field,
                distance_to_water_source_km=2.5,  # Example
                distance_to_market_km=15.0,       # Example
                distance_to_road_km=0.5,          # Example
                distance_to_nearest_farm_km=1.2,  # Example
                water_availability='moderate',
                market_accessibility='moderate',
                road_accessibility='high',
                recommendations=[
                    'Field is accessible - close to main road',
                    'Good water availability - consider drip irrigation',
                    'Market distance reasonable for daily supply'
                ]
            )
            
            logger.info(f"Analyzed proximity for field {field.name}")
            return proximity
        
        except Exception as e:
            logger.error(f"Error analyzing field proximity: {str(e)}")
            return None
    
    @staticmethod
    def calculate_location_analytics(farm):
        """Calculate location-based analytics for a farm"""
        try:
            fields = farm.fields.all()
            
            total_area = sum(f.area_hectares for f in fields)
            total_production = 0  # Would come from harvest data
            
            # Calculate average yield (example)
            avg_yield = total_production / total_area if total_area > 0 else 0
            
            analytics, created = LocationAnalytics.objects.update_or_create(
                farm=farm,
                date=timezone.now().date(),
                defaults={
                    'avg_yield_per_hectare': avg_yield,
                    'total_area_cultivated': total_area,
                    'total_production': total_production,
                    'crop_suggestions': [f.current_crop for f in fields if f.current_crop],
                    'recommendations': {
                        'irrigation': 'Monitor seasonal rainfall patterns',
                        'soil_health': 'Conduct soil testing for nutrient levels',
                        'pest_management': 'Implement integrated pest management'
                    }
                }
            )
            
            logger.info(f"Calculated analytics for farm {farm.name}")
            return analytics
        
        except Exception as e:
            logger.error(f"Error calculating location analytics: {str(e)}")
            return None
    
    @staticmethod
    def get_fields_by_region(region):
        """Get all farm fields in a specific region"""
        try:
            fields = FarmField.objects.filter(farm__location__region=region)
            return list(fields)
        except Exception as e:
            logger.error(f"Error getting fields by region: {str(e)}")
            return []
    
    @staticmethod
    def _point_in_polygon(latitude, longitude, polygon_coords):
        """Simple point-in-polygon algorithm"""
        x, y = longitude, latitude
        n = len(polygon_coords)
        inside = False
        
        p1x, p1y = polygon_coords[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon_coords[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside
    
    @staticmethod
    def check_point_in_geofence(latitude, longitude, geofence_id):
        """Check if a GPS point is within a geofence boundary"""
        try:
            geofence = GeofenceAlert.objects.get(id=geofence_id)
            
            if not geofence.boundary:
                return False
            
            # Extract polygon coordinates
            try:
                coords = geofence.boundary['coordinates'][0]
                is_inside = LocationService._point_in_polygon(latitude, longitude, coords)
                return is_inside
            except (KeyError, IndexError, TypeError):
                return False
        
        except Exception as e:
            logger.error(f"Error checking point in geofence: {str(e)}")
            return False
    
    @staticmethod
    def get_overlapping_fields(latitude, longitude, farm_id=None):
        """Find farm fields that contain a GPS point"""
        try:
            all_fields = FarmField.objects.all()
            
            if farm_id:
                all_fields = all_fields.filter(farm_id=farm_id)
            
            overlapping = []
            for field in all_fields:
                if not field.boundary:
                    continue
                
                try:
                    coords = field.boundary['coordinates'][0]
                    if LocationService._point_in_polygon(latitude, longitude, coords):
                        overlapping.append(field)
                except (KeyError, IndexError, TypeError):
                    continue
            
            return overlapping
        
        except Exception as e:
            logger.error(f"Error getting overlapping fields: {str(e)}")
            return []
