# core/api/serializers_location.py
# DRF Serializers for GPS Mapping and Location API

from rest_framework import serializers
from core.models_location import (
    FarmLocation, FarmField, FarmFieldZone, FarmGeofenceAlert,
    FarmLocationAnalytics, FarmCropRotationPlan, FarmProximityAnalysis
)


class FarmLocationSerializer(serializers.ModelSerializer):
    farm_name = serializers.CharField(source='farm.name', read_only=True)
    
    class Meta:
        model = FarmLocation
        fields = [
            'id', 'farm', 'farm_name', 'address', 'region', 'district',
            'latitude', 'longitude', 'altitude', 'total_area_hectares',
            'cultivated_area', 'soil_type', 'water_source', 'verified', 'created_at'
        ]


class FarmFieldZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = FarmFieldZone
        fields = [
            'id', 'field', 'name', 'zone_type', 'area_hectares',
            'severity_level', 'notes', 'management_actions', 'created_at'
        ]


class FieldDetailSerializer(serializers.ModelSerializer):
    zones = FarmFieldZoneSerializer(many=True, read_only=True, source='zones')
    farm_name = serializers.CharField(source='farm.name', read_only=True)
    
    class Meta:
        model = FarmField
        fields = [
            'id', 'farm', 'farm_name', 'name', 'field_type', 'area_hectares',
            'perimeter_km', 'soil_type', 'soil_fertility', 'slope_percent',
            'drainage', 'current_crop', 'crop_planted_date', 'expected_harvest_date',
            'crop_history', 'status', 'zones', 'created_at', 'updated_at'
        ]


class FieldSerializer(serializers.ModelSerializer):
    farm_name = serializers.CharField(source='farm.name', read_only=True)
    
    class Meta:
        model = FarmField
        fields = [
            'id', 'farm', 'farm_name', 'name', 'field_type', 'area_hectares',
            'soil_type', 'soil_fertility', 'current_crop', 'status', 'created_at'
        ]


class FarmGeofenceAlertSerializer(serializers.ModelSerializer):
    farm_name = serializers.CharField(source='farm.name', read_only=True)
    
    class Meta:
        model = FarmGeofenceAlert
        fields = [
            'id', 'farm', 'farm_name', 'name', 'description', 'alert_type',
            'is_active', 'notify_on_entry', 'notify_on_exit', 'created_at'
        ]


class FarmCropRotationPlanSerializer(serializers.ModelSerializer):
    field_name = serializers.CharField(source='field.name', read_only=True)
    
    class Meta:
        model = FarmCropRotationPlan
        fields = [
            'id', 'field', 'field_name', 'current_crop', 'current_season',
            'year_1_recommendation', 'year_2_recommendation', 'year_3_recommendation',
            'year_4_recommendation', 'rotation_type', 'benefits',
            'soil_improvement', 'pest_break_benefits', 'last_reviewed'
        ]


class FarmProximityAnalysisSerializer(serializers.ModelSerializer):
    field_name = serializers.CharField(source='field.name', read_only=True)
    
    class Meta:
        model = FarmProximityAnalysis
        fields = [
            'id', 'field', 'field_name', 'distance_to_water_source_km',
            'distance_to_market_km', 'distance_to_road_km', 'distance_to_nearest_farm_km',
            'water_availability', 'market_accessibility', 'road_accessibility',
            'recommendations', 'last_analyzed'
        ]


class FarmLocationAnalyticsSerializer(serializers.ModelSerializer):
    farm_name = serializers.CharField(source='farm.name', read_only=True)
    
    class Meta:
        model = FarmLocationAnalytics
        fields = [
            'id', 'farm', 'farm_name', 'date', 'avg_yield_per_hectare',
            'total_area_cultivated', 'total_production', 'regional_avg_yield',
            'regional_rank', 'recommendations', 'crop_suggestions', 'irrigation_needs',
            'soil_improvement_actions', 'last_updated'
        ]
