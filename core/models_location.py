# core/models_location.py
# GPS Mapping & Location Intelligence Models

from django.db import models
from django.conf import settings
from core.models import Farm


class FarmLocation(models.Model):
    """Farm location with spatial data"""
    farm = models.OneToOneField(Farm, on_delete=models.CASCADE, related_name='geo_location')
    
    # Location coordinates stored as JSON: {"lat": value, "lon": value}
    coordinates = models.JSONField(
        null=True, 
        blank=True,
        default=dict,
        help_text='Farm location coordinates as {"lat": latitude, "lon": longitude}'
    )
    
    # Address information
    address = models.CharField(max_length=255, blank=True)
    region = models.CharField(max_length=100, blank=True)
    district = models.CharField(max_length=100, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    altitude = models.FloatField(null=True, blank=True, help_text='Altitude in meters')
    
    # Farm characteristics
    total_area_hectares = models.FloatField(default=0.0)
    cultivated_area = models.FloatField(default=0.0)
    uncultivated_area = models.FloatField(default=0.0)
    
    # Geographic attributes
    soil_type = models.CharField(max_length=100, blank=True)
    water_source = models.CharField(max_length=100, blank=True)
    accessibility = models.CharField(max_length=100, blank=True)
    
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Farm Location'
    
    def __str__(self):
        return f"{self.farm.name} - {self.region}"


class FarmField(models.Model):
    """Individual fields within a farm"""
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='location_fields')
    name = models.CharField(max_length=200)
    field_type = models.CharField(
        max_length=50,
        choices=[
            ('arable', 'Arable Land'),
            ('pasture', 'Pasture'),
            ('orchard', 'Orchard'),
            ('plantation', 'Plantation'),
            ('other', 'Other')
        ],
        default='arable'
    )
    
    # Boundary stored as GeoJSON Feature Geometry
    boundary = models.JSONField(
        null=True,
        blank=True,
        default=dict,
        help_text='Field boundary as GeoJSON polygon coordinates'
    )
    
    # Area calculations
    area_hectares = models.FloatField(default=0.0)
    perimeter_km = models.FloatField(default=0.0)
    
    # Field characteristics
    soil_type = models.CharField(max_length=100, blank=True)
    soil_fertility = models.CharField(
        max_length=20,
        choices=[('poor', 'Poor'), ('fair', 'Fair'), ('good', 'Good'), ('excellent', 'Excellent')],
        default='good'
    )
    slope_percent = models.FloatField(default=0.0, help_text='Ground slope in percentage')
    drainage = models.CharField(
        max_length=20,
        choices=[('poor', 'Poor'), ('moderate', 'Moderate'), ('good', 'Good'), ('excellent', 'Excellent')],
        default='good'
    )
    
    # Current use
    current_crop = models.CharField(max_length=200, blank=True)
    crop_planted_date = models.DateField(null=True, blank=True)
    expected_harvest_date = models.DateField(null=True, blank=True)
    
    # Rotation tracking
    crop_history = models.JSONField(default=list, help_text='Historical crop rotation')
    
    status = models.CharField(
        max_length=20,
        choices=[('idle', 'Idle'), ('planted', 'Planted'), ('growing', 'Growing'), ('harvested', 'Harvested')],
        default='idle'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['farm', 'name']
    
    def __str__(self):
        return f"{self.farm.name} - {self.name}"


class FarmFieldZone(models.Model):
    """Sub-zones within a farm field for detailed management"""
    field = models.ForeignKey(FarmField, on_delete=models.CASCADE, related_name='zones')
    name = models.CharField(max_length=200)
    zone_type = models.CharField(
        max_length=50,
        choices=[
            ('irrigation', 'Irrigation Zone'),
            ('pest_prone', 'Pest-Prone Area'),
            ('low_yield', 'Low Yield Area'),
            ('high_yield', 'High Yield Area'),
            ('experimental', 'Experimental Zone'),
            ('other', 'Other')
        ]
    )
    
    # Boundary stored as GeoJSON
    boundary = models.JSONField(null=True, blank=True, default=dict)
    
    area_hectares = models.FloatField(default=0.0)
    severity_level = models.IntegerField(
        default=1,
        choices=[(i, f'Level {i}') for i in range(1, 6)],
        help_text='Severity or priority level (1-5)'
    )
    
    notes = models.TextField(blank=True)
    management_actions = models.JSONField(default=list)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.field.name} - {self.name}"


class FarmGeofenceAlert(models.Model):
    """Geofence boundaries for location-based alerts"""
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='farm_geofences')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Boundary stored as GeoJSON polygon
    boundary = models.JSONField(
        default=dict,
        help_text='Geofence boundary as GeoJSON polygon coordinates'
    )
    
    alert_type = models.CharField(
        max_length=50,
        choices=[
            ('perimeter', 'Perimeter Alert'),
            ('equipment', 'Equipment Zone'),
            ('livestock', 'Livestock Zone'),
            ('restricted', 'Restricted Area'),
            ('other', 'Other')
        ]
    )
    
    is_active = models.BooleanField(default=True)
    notify_on_entry = models.BooleanField(default=False)
    notify_on_exit = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.farm.name} - {self.name}"


class FarmCropRotationPlan(models.Model):
    """Crop rotation recommendations by field location"""
    field = models.OneToOneField(FarmField, on_delete=models.CASCADE, related_name='rotation_plan')
    
    current_crop = models.CharField(max_length=200)
    current_season = models.IntegerField()
    
    year_1_recommendation = models.CharField(max_length=200, default='Legumes')
    year_2_recommendation = models.CharField(max_length=200, default='Root Crops')
    year_3_recommendation = models.CharField(max_length=200, default='Cereals')
    year_4_recommendation = models.CharField(max_length=200, default='Current Crop')
    
    rotation_type = models.CharField(
        max_length=50,
        choices=[
            ('legume_cereal', 'Legume-Cereal'),
            ('diverse', 'Diverse'),
            ('simple', 'Simple Two-Crop'),
            ('intensive', 'Intensive Multi-Crop')
        ],
        default='diverse'
    )
    
    benefits = models.JSONField(default=list, help_text='Key benefits of this rotation')
    soil_improvement = models.TextField(blank=True)
    pest_break_benefits = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.field.name} - Rotation Plan"


class FarmLocationAnalytics(models.Model):
    """Analyze location-based analytics for a farm"""
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='location_analytics')
    date = models.DateField(auto_now_add=True)
    
    avg_yield_per_hectare = models.FloatField(default=0.0)
    total_area_cultivated = models.FloatField(default=0.0)
    total_production = models.FloatField(default=0.0)
    
    crop_suggestions = models.JSONField(default=list)
    recommendations = models.JSONField(default=dict)
    seasonal_trends = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.farm.name} - Analytics {self.date}"


class FarmProximityAnalysis(models.Model):
    """Analyze proximity of fields to resources"""
    field = models.ForeignKey(FarmField, on_delete=models.CASCADE, related_name='proximity_analyses')
    
    # Distances to key resources
    distance_to_water_source_km = models.FloatField(default=0.0)
    distance_to_market_km = models.FloatField(default=0.0)
    distance_to_road_km = models.FloatField(default=0.0)
    distance_to_nearest_farm_km = models.FloatField(default=0.0)
    
    # Accessibility scores
    water_availability = models.CharField(
        max_length=20,
        choices=[('poor', 'Poor'), ('moderate', 'Moderate'), ('good', 'Good'), ('excellent', 'Excellent')],
        default='moderate'
    )
    market_accessibility = models.CharField(
        max_length=20,
        choices=[('poor', 'Poor'), ('moderate', 'Moderate'), ('good', 'Good'), ('excellent', 'Excellent')],
        default='moderate'
    )
    road_accessibility = models.CharField(
        max_length=20,
        choices=[('poor', 'Poor'), ('moderate', 'Moderate'), ('good', 'Good'), ('excellent', 'Excellent')],
        default='moderate'
    )
    
    recommendations = models.JSONField(default=list)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.field.name} - Proximity Analysis"
