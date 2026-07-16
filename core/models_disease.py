# core/models_disease.py
# Comprehensive disease diagnosis with symptom matching and treatment

from django.db import models
from django.conf import settings
from core.models import Farm, CropType
import json


class DiseaseCategory(models.Model):
    """Classification of diseases"""
    
    CATEGORY_TYPES = [
        ('fungal', 'Fungal'),
        ('bacterial', 'Bacterial'),
        ('viral', 'Viral'),
        ('parasitic', 'Parasitic'),
        ('nutritional', 'Nutritional'),
        ('physiological', 'Physiological'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    category_type = models.CharField(max_length=20, choices=CATEGORY_TYPES)
    description = models.TextField()
    icon = models.CharField(max_length=100, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Disease Categories'
        ordering = ['category_type', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_category_type_display()})"


class Disease(models.Model):
    """Disease profiles with severity levels"""
    
    SEVERITY_LEVELS = [
        ('mild', 'Mild'),
        ('moderate', 'Moderate'),
        ('severe', 'Severe'),
        ('critical', 'Critical'),
    ]
    
    category = models.ForeignKey(DiseaseCategory, on_delete=models.CASCADE, related_name='diseases')
    
    name = models.CharField(max_length=200)
    scientific_name = models.CharField(max_length=200, null=True, blank=True)
    
    description = models.TextField()
    cause = models.TextField(help_text="What causes this disease")
    transmission = models.TextField(help_text="How the disease spreads")
    
    affected_crops = models.ManyToManyField(CropType, related_name='diseases')
    
    initial_severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS, default='mild')
    progression_rate = models.IntegerField(default=5, help_text="Days to escalate severity")
    
    is_quarantine_required = models.BooleanField(default=False)
    quarantine_days = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('category', 'name')
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.category.category_type})"


class Symptom(models.Model):
    """Disease symptoms for diagnosis"""
    
    SEVERITY_INDICATORS = [
        ('critical', 'Critical'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]
    
    BODY_PARTS = [
        ('leaf', 'Leaf'),
        ('stem', 'Stem'),
        ('root', 'Root'),
        ('fruit', 'Fruit'),
        ('flower', 'Flower'),
        ('entire_plant', 'Entire Plant'),
    ]
    
    disease = models.ForeignKey(Disease, on_delete=models.CASCADE, related_name='symptoms')
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    affected_body_part = models.CharField(max_length=20, choices=BODY_PARTS)
    
    appearance = models.TextField(help_text="Visual characteristics")
    color = models.CharField(max_length=50, null=True, blank=True, help_text="e.g., brown, yellow, black")
    texture = models.CharField(max_length=50, null=True, blank=True, help_text="e.g., powdery, slimy, necrotic")
    
    severity_indicator = models.CharField(max_length=20, choices=SEVERITY_INDICATORS)
    is_primary_symptom = models.BooleanField(default=False)
    
    keywords = models.JSONField(default=list, help_text="Keywords for matching")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('disease', 'name')
        ordering = ['disease', '-is_primary_symptom', 'name']
    
    def __str__(self):
        return f"{self.disease.name} - {self.name}"


class TreatmentOption(models.Model):
    """Treatment options for diseases"""
    
    TREATMENT_TYPES = [
        ('chemical', 'Chemical'),
        ('biological', 'Biological'),
        ('cultural', 'Cultural'),
        ('mechanical', 'Mechanical'),
        ('integrated', 'Integrated'),
    ]
    
    STAGES = [
        ('prevention', 'Prevention'),
        ('early', 'Early Stage'),
        ('moderate', 'Moderate Stage'),
        ('severe', 'Severe Stage'),
    ]
    
    disease = models.ForeignKey(Disease, on_delete=models.CASCADE, related_name='treatments')
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    treatment_type = models.CharField(max_length=20, choices=TREATMENT_TYPES)
    applicable_stage = models.CharField(max_length=20, choices=STAGES)
    
    active_ingredient = models.CharField(max_length=200, null=True, blank=True)
    dosage = models.CharField(max_length=200, help_text="e.g., 2g per liter")
    application_method = models.CharField(max_length=200, help_text="e.g., spray, drench, dust")
    
    frequency = models.CharField(max_length=200, help_text="Application frequency")
    duration_days = models.IntegerField(help_text="Duration of treatment")
    
    effectiveness_percent = models.IntegerField(default=80, help_text="Expected effectiveness %")
    cost_per_hectare = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    precautions = models.TextField(help_text="Safety precautions")
    re_entry_hours = models.IntegerField(default=24, help_text="Hours before safe re-entry")
    harvest_waiting_days = models.IntegerField(default=0, help_text="Days before harvest")
    
    is_organic_approved = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('disease', 'name')
        ordering = ['disease', 'applicable_stage', 'effectiveness_percent']
    
    def __str__(self):
        return f"{self.disease.name} - {self.name}"


class DiagnosisRecord(models.Model):
    """Diagnosis records for user farms"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cured', 'Cured'),
        ('monitoring', 'Monitoring'),
        ('unconfirmed', 'Unconfirmed'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='diagnosis_records')
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='diagnosis_records')
    crop = models.ForeignKey(CropType, on_delete=models.CASCADE, null=True, blank=True)
    
    disease = models.ForeignKey(Disease, on_delete=models.CASCADE, related_name='diagnosis_records')
    
    confidence_score = models.FloatField(default=0.0, help_text="Diagnosis confidence 0-100")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    detected_symptoms = models.JSONField(default=list, help_text="List of detected symptoms")
    severity_level = models.CharField(max_length=20, choices=Disease.SEVERITY_LEVELS)
    
    description = models.TextField(help_text="Description of observed symptoms")
    location_in_field = models.CharField(max_length=200, null=True, blank=True)
    
    suspected_cause = models.TextField(null=True, blank=True)
    environmental_factors = models.JSONField(default=dict, help_text="Temperature, humidity, etc.")
    
    # Treatment tracking
    recommended_treatment = models.ForeignKey(TreatmentOption, on_delete=models.SET_NULL, null=True, blank=True)
    treatment_started_at = models.DateTimeField(null=True, blank=True)
    treatment_status = models.CharField(max_length=50, null=True, blank=True)
    
    # Images
    image_url = models.URLField(null=True, blank=True)
    image_analysis_data = models.JSONField(default=dict, help_text="AI image analysis results")
    
    # Verification
    verified_by_expert = models.BooleanField(default=False)
    expert_notes = models.TextField(null=True, blank=True)
    
    detected_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-detected_at']
        indexes = [
            models.Index(fields=['user', 'farm', '-detected_at']),
            models.Index(fields=['status', 'disease']),
        ]
    
    def __str__(self):
        return f"{self.disease.name} - {self.farm.name} ({self.status})"


class DiagnosisHistory(models.Model):
    """History of diagnosis updates"""
    
    diagnosis = models.ForeignKey(DiagnosisRecord, on_delete=models.CASCADE, related_name='history')
    
    status_before = models.CharField(max_length=20)
    status_after = models.CharField(max_length=20)
    
    notes = models.TextField()
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    changed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-changed_at']
        verbose_name_plural = 'Diagnosis Histories'
    
    def __str__(self):
        return f"{self.diagnosis.disease.name} - {self.status_before} → {self.status_after}"


class DiseaseAlert(models.Model):
    """Alerts for disease outbreaks"""
    
    ALERT_TYPES = [
        ('high_risk', 'High Risk'),
        ('outbreak', 'Outbreak'),
        ('advisory', 'Advisory'),
        ('warning', 'Warning'),
    ]
    
    disease = models.ForeignKey(Disease, on_delete=models.CASCADE, related_name='alerts')
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    
    affected_regions = models.JSONField(default=list)
    affected_crops = models.ManyToManyField(CropType)
    
    recommended_actions = models.TextField()
    urgency_level = models.IntegerField(default=5, help_text="1-10 scale")
    
    issued_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    
    source = models.CharField(max_length=200, null=True, blank=True)
    
    class Meta:
        ordering = ['-issued_at']
    
    def __str__(self):
        return f"{self.disease.name} - {self.get_alert_type_display()}"


class DiseaseStatistics(models.Model):
    """Aggregated disease statistics"""
    
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='disease_statistics')
    crop = models.ForeignKey(CropType, on_delete=models.CASCADE, null=True, blank=True)
    
    date = models.DateField(auto_now_add=True)
    
    total_diseases_detected = models.IntegerField(default=0)
    confirmed_diseases = models.IntegerField(default=0)
    cured_diseases = models.IntegerField(default=0)
    
    most_common_disease = models.ForeignKey(Disease, on_delete=models.SET_NULL, null=True, blank=True)
    average_severity = models.FloatField(default=0.0)
    
    treatment_success_rate = models.FloatField(default=0.0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('farm', 'crop', 'date')
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.farm.name} - {self.date}"
