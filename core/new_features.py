# ==============================================================
# ESSENTIAL NEW FEATURES - Carefully Designed to Integrate
# with Existing FarmWise Models (Animal, Farm, Field, Crop, etc)
# ==============================================================
# (Add the following models to the end of core/models.py)

from django.db import models
from django.contrib.auth.models import User

# ============================================================
# FEATURE 1: COMPREHENSIVE REPORTING SYSTEM
# ============================================================

class Report(models.Model):
    """Base report model for all report types"""
    
    REPORT_TYPES = [
        ('crop_yield', 'Crop Yield Report'),
        ('livestock_health', 'Livestock Health Report'),
        ('financial', 'Financial Report'),
        ('field_summary', 'Field Summary'),
        ('production', 'Production Report'),
        ('custom', 'Custom Report'),
    ]
    
    farm = models.ForeignKey('Farm', on_delete=models.CASCADE, related_name='features_reports')
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES)
    title = models.CharField(max_length=255)
    
    # Date range
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Export settings
    export_format = models.CharField(max_length=10, choices=[
        ('pdf', 'PDF'),
        ('csv', 'CSV'),
        ('json', 'JSON'),
    ], default='pdf')
    
    file_path = models.FileField(upload_to='reports/', null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('ready', 'Ready'),
    ], default='pending')
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'feature_reports'
        indexes = [
            models.Index(fields=['farm', 'report_type']),
        ]
    
    def __str__(self):
        return f"{self.farm.name} - {self.get_report_type_display()}"


# ============================================================
# FEATURE 2: TASK MANAGEMENT
# ============================================================

class Task(models.Model):
    """Farm tasks and activities"""
    
    farm = models.ForeignKey('Farm', on_delete=models.CASCADE, related_name='feature_tasks')
    title = models.CharField(max_length=255)
    description = models.TextField()
    
    # Assignment
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='tasks_created_by_me')
    
    # Timeline
    due_date = models.DateField()
    completed_date = models.DateField(null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ], default='pending')
    
    priority = models.CharField(max_length=20, choices=[
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ], default='medium')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'feature_tasks'
        indexes = [
            models.Index(fields=['farm', 'due_date']),
        ]
    
    def __str__(self):
        return f"{self.title} - Due {self.due_date}"


# ============================================================
# FEATURE 3: DOCUMENT MANAGEMENT
# ============================================================

class Document(models.Model):
    """Document repository"""
    
    farm = models.ForeignKey('Farm', on_delete=models.CASCADE, related_name='feature_documents')
    
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    file = models.FileField(upload_to='documents/')
    
    # Important dates
    document_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    
    # Sharing
    is_shared = models.BooleanField(default=False)
    shared_with_users = models.ManyToManyField(User, blank=True)
    
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'feature_documents'
        indexes = [
            models.Index(fields=['farm', 'expiry_date']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.category})"


# ============================================================
# FEATURE 4: WATER MANAGEMENT
# ============================================================

class WaterSource(models.Model):
    """Water sources on farm"""
    
    farm = models.ForeignKey('Farm', on_delete=models.CASCADE, related_name='water_sources')
    name = models.CharField(max_length=255)
    source_type = models.CharField(max_length=50, choices=[
        ('well', 'Well'),
        ('river', 'River'),
        ('dam', 'Dam'),
        ('tank', 'Tank'),
    ])
    
    total_capacity_liters = models.BigIntegerField()
    current_level_liters = models.BigIntegerField()
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'feature_water_sources'
    
    def __str__(self):
        return f"{self.name} ({self.get_source_type_display()})"


class WaterUsageLog(models.Model):
    """Water usage tracking"""
    
    farm = models.ForeignKey('Farm', on_delete=models.CASCADE, related_name='water_logs')
    source = models.ForeignKey(WaterSource, on_delete=models.CASCADE)
    
    usage_date = models.DateField()
    usage_type = models.CharField(max_length=50, choices=[
        ('irrigation', 'Irrigation'),
        ('livestock', 'Livestock'),
        ('domestic', 'Domestic'),
    ])
    
    liters_used = models.BigIntegerField()
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    field = models.ForeignKey('Field', on_delete=models.SET_NULL, null=True, blank=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'feature_water_logs'
        indexes = [
            models.Index(fields=['farm', 'usage_date']),
        ]
    
    def __str__(self):
        return f"{self.farm.name} - {self.liters_used}L on {self.usage_date}"


# ============================================================
# FEATURE 5: SOIL HEALTH
# ============================================================

class SoilTest(models.Model):
    """Soil test results"""
    
    farm = models.ForeignKey('Farm', on_delete=models.CASCADE, related_name='soil_tests')
    field = models.ForeignKey('Field', on_delete=models.CASCADE, related_name='soil_tests')
    
    test_date = models.DateField()
    
    # NPK values
    nitrogen_ppm = models.DecimalField(max_digits=10, decimal_places=2)
    phosphorus_ppm = models.DecimalField(max_digits=10, decimal_places=2)
    potassium_ppm = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Other properties
    ph_level = models.DecimalField(max_digits=5, decimal_places=2)
    organic_matter_percent = models.DecimalField(max_digits=5, decimal_places=2)
    
    # Lab info
    lab_name = models.CharField(max_length=255, blank=True)
    recommendations = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'feature_soil_tests'
        indexes = [
            models.Index(fields=['field', 'test_date']),
        ]
    
    def __str__(self):
        return f"{self.field.name} - Soil Test {self.test_date}"


# ============================================================
# FEATURE 6: WEATHER ALERTS
# ============================================================

class WeatherAlert(models.Model):
    """Severe weather alerts"""
    
    farm = models.ForeignKey('Farm', on_delete=models.CASCADE, related_name='weather_alerts')
    
    alert_type = models.CharField(max_length=50, choices=[
        ('frost', 'Frost'),
        ('heat', 'Excessive Heat'),
        ('drought', 'Drought'),
        ('flood', 'Flood'),
        ('wind', 'High Wind'),
        ('storm', 'Storm'),
    ])
    
    severity = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ])
    
    alert_issued_at = models.DateTimeField()
    alert_expires_at = models.DateTimeField()
    
    description = models.TextField()
    recommended_actions = models.TextField(blank=True)
    
    is_acknowledged = models.BooleanField(default=False)
    acknowledged_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'feature_weather_alerts'
        indexes = [
            models.Index(fields=['farm', 'alert_issued_at']),
        ]
    
    def __str__(self):
        return f"{self.get_alert_type_display()} - {self.farm.name}"


# ============================================================
# FEATURE 7: REMINDERS
# ============================================================

class Reminder(models.Model):
    """Smart reminders for farm activities"""
    
    farm = models.ForeignKey('Farm', on_delete=models.CASCADE, related_name='feature_reminders')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='farm_reminders')
    
    title = models.CharField(max_length=255)
    reminder_type = models.CharField(max_length=100)
    
    due_date = models.DateField()
    is_recurring = models.BooleanField(default=False)
    
    is_active = models.BooleanField(default=True)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'feature_reminders'
        indexes = [
            models.Index(fields=['farm', 'due_date']),
        ]
    
    def __str__(self):
        return f"{self.title} - Due {self.due_date}"


# ============================================================
# FEATURE 8: TRACEABILITY
# ============================================================

class ProductBatch(models.Model):
    """Production batch tracking"""
    
    farm = models.ForeignKey('Farm', on_delete=models.CASCADE, related_name='product_batches')
    
    batch_id = models.CharField(max_length=100, unique=True)
    product_type = models.CharField(max_length=100)
    
    field = models.ForeignKey('Field', on_delete=models.SET_NULL, null=True, blank=True)
    
    production_start_date = models.DateField()
    production_end_date = models.DateField(null=True, blank=True)
    
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_unit = models.CharField(max_length=50)
    
    grade = models.CharField(max_length=20, choices=[
        ('a', 'Grade A'),
        ('b', 'Grade B'),
        ('c', 'Grade C'),
    ], default='a')
    
    status = models.CharField(max_length=50, choices=[
        ('produced', 'Produced'),
        ('packaged', 'Packaged'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
    ], default='produced')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'feature_product_batches'
        indexes = [
            models.Index(fields=['batch_id']),
        ]
    
    def __str__(self):
        return f"Batch {self.batch_id} - {self.product_type}"


# ============================================================
# FEATURE 9: CARBON FOOTPRINT (Simplified)
# ============================================================

class CarbonFootprintReport(models.Model):
    """Carbon footprint tracking"""
    
    farm = models.ForeignKey('Farm', on_delete=models.CASCADE, related_name='carbon_reports')
    
    report_period = models.CharField(max_length=20, choices=[
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ])
    year = models.IntegerField()
    month = models.IntegerField(null=True, blank=True)
    
    total_emissions_kg_co2e = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Breakdown
    fuel_emissions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    electricity_emissions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fertilizer_emissions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    is_carbon_neutral = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'feature_carbon_reports'
        unique_together = [['farm', 'year', 'month']]
    
    def __str__(self):
        return f"{self.farm.name} - Carbon Report {self.year}"
