# core/api/serializers_disease.py
# Disease diagnosis serializers

from rest_framework import serializers
from core.models_disease import (
    DiseaseCategory, Disease, Symptom, TreatmentOption,
    DiagnosisRecord, DiagnosisHistory, DiseaseAlert, DiseaseStatistics
)


class DiseaseCategorySerializer(serializers.ModelSerializer):
    """Serialize disease categories"""
    category_type_display = serializers.CharField(source='get_category_type_display', read_only=True)
    
    class Meta:
        model = DiseaseCategory
        fields = ['id', 'name', 'category_type', 'category_type_display', 'description', 'icon']


class SymptomSerializer(serializers.ModelSerializer):
    """Serialize disease symptoms"""
    body_part_display = serializers.CharField(source='get_affected_body_part_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_indicator_display', read_only=True)
    
    class Meta:
        model = Symptom
        fields = ['id', 'name', 'description', 'affected_body_part', 'body_part_display',
                  'appearance', 'color', 'texture', 'severity_indicator', 'severity_display',
                  'is_primary_symptom', 'keywords']


class TreatmentOptionSerializer(serializers.ModelSerializer):
    """Serialize treatment options"""
    type_display = serializers.CharField(source='get_treatment_type_display', read_only=True)
    stage_display = serializers.CharField(source='get_applicable_stage_display', read_only=True)
    
    class Meta:
        model = TreatmentOption
        fields = ['id', 'name', 'description', 'treatment_type', 'type_display',
                  'applicable_stage', 'stage_display', 'active_ingredient', 'dosage',
                  'application_method', 'frequency', 'duration_days', 'effectiveness_percent',
                  'cost_per_hectare', 'precautions', 're_entry_hours', 'harvest_waiting_days',
                  'is_organic_approved']


class DiseaseSerializer(serializers.ModelSerializer):
    """Serialize diseases"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_type = serializers.CharField(source='category.category_type', read_only=True)
    severity_display = serializers.CharField(source='get_initial_severity_display', read_only=True)
    symptoms = SymptomSerializer(many=True, read_only=True)
    treatments = TreatmentOptionSerializer(many=True, read_only=True)
    affected_crops = serializers.StringRelatedField(many=True, read_only=True)
    
    class Meta:
        model = Disease
        fields = ['id', 'name', 'scientific_name', 'category', 'category_name', 'category_type',
                  'description', 'cause', 'transmission', 'initial_severity', 'severity_display',
                  'progression_rate', 'is_quarantine_required', 'quarantine_days',
                  'affected_crops', 'symptoms', 'treatments']


class DiagnosisHistorySerializer(serializers.ModelSerializer):
    """Serialize diagnosis history"""
    status_before_display = serializers.SerializerMethodField()
    status_after_display = serializers.SerializerMethodField()
    
    class Meta:
        model = DiagnosisHistory
        fields = ['id', 'status_before', 'status_before_display', 'status_after',
                  'status_after_display', 'notes', 'changed_by', 'changed_at']
        read_only_fields = ['id', 'changed_at']
    
    def get_status_before_display(self, obj):
        return dict(DiagnosisRecord.STATUS_CHOICES).get(obj.status_before, obj.status_before)
    
    def get_status_after_display(self, obj):
        return dict(DiagnosisRecord.STATUS_CHOICES).get(obj.status_after, obj.status_after)


class DiagnosisRecordSerializer(serializers.ModelSerializer):
    """Serialize diagnosis records"""
    disease_name = serializers.CharField(source='disease.name', read_only=True)
    farm_name = serializers.CharField(source='farm.name', read_only=True)
    crop_name = serializers.CharField(source='crop.name', read_only=True, allow_null=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_level_display', read_only=True)
    treatment_name = serializers.CharField(source='recommended_treatment.name', read_only=True, allow_null=True)
    history = DiagnosisHistorySerializer(many=True, read_only=True)
    
    class Meta:
        model = DiagnosisRecord
        fields = ['id', 'disease', 'disease_name', 'farm', 'farm_name', 'crop', 'crop_name',
                  'confidence_score', 'status', 'status_display', 'detected_symptoms',
                  'severity_level', 'severity_display', 'description', 'location_in_field',
                  'suspected_cause', 'environmental_factors', 'recommended_treatment',
                  'treatment_name', 'treatment_started_at', 'treatment_status',
                  'image_url', 'image_analysis_data', 'verified_by_expert',
                  'expert_notes', 'detected_at', 'updated_at', 'resolved_at', 'history']
        read_only_fields = ['id', 'detected_at', 'updated_at', 'history']


class DiagnosisDetailSerializer(serializers.ModelSerializer):
    """Detailed diagnosis with treatment plan"""
    disease = DiseaseSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_level_display', read_only=True)
    recommended_treatment = TreatmentOptionSerializer(read_only=True)
    history = DiagnosisHistorySerializer(many=True, read_only=True)
    
    class Meta:
        model = DiagnosisRecord
        fields = ['id', 'disease', 'farm', 'crop', 'confidence_score', 'status',
                  'status_display', 'detected_symptoms', 'severity_level', 'severity_display',
                  'description', 'location_in_field', 'suspected_cause',
                  'environmental_factors', 'recommended_treatment', 'image_url',
                  'image_analysis_data', 'verified_by_expert', 'expert_notes',
                  'detected_at', 'updated_at', 'resolved_at', 'history']
        read_only_fields = ['id', 'detected_at', 'updated_at', 'history']


class DiseaseAlertSerializer(serializers.ModelSerializer):
    """Serialize disease alerts"""
    disease_name = serializers.CharField(source='disease.name', read_only=True)
    type_display = serializers.CharField(source='get_alert_type_display', read_only=True)
    affected_crops = serializers.StringRelatedField(many=True, read_only=True)
    
    class Meta:
        model = DiseaseAlert
        fields = ['id', 'disease', 'disease_name', 'title', 'description', 'alert_type',
                  'type_display', 'affected_regions', 'affected_crops', 'recommended_actions',
                  'urgency_level', 'issued_at', 'expires_at', 'is_active']


class DiseaseStatisticsSerializer(serializers.ModelSerializer):
    """Serialize disease statistics"""
    most_common_disease_name = serializers.CharField(source='most_common_disease.name', read_only=True, allow_null=True)
    farm_name = serializers.CharField(source='farm.name', read_only=True)
    crop_name = serializers.CharField(source='crop.name', read_only=True, allow_null=True)
    
    class Meta:
        model = DiseaseStatistics
        fields = ['id', 'farm', 'farm_name', 'crop', 'crop_name', 'date',
                  'total_diseases_detected', 'confirmed_diseases', 'cured_diseases',
                  'most_common_disease', 'most_common_disease_name', 'average_severity',
                  'treatment_success_rate']
