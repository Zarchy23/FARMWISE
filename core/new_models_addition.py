# ============================================================
# ADD THIS TO END OF core/models.py
# ============================================================

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import datetime

# Note: Farm, Field, Crop, Livestock, Equipment are defined in core/models.py
# Use string references for ForeignKeys to avoid circular imports

# ============================================================
# FEATURE 1: COMPREHENSIVE REPORTING SYSTEM
# ============================================================

class Report(models.Model):
    """Base report model for all report types"""
    
    REPORT_TYPES = [
        # Crop Reports
        ('crop_yield', 'Crop Yield Report'),
        ('planting', 'Planting Report'),
        ('harvest', 'Harvest Report'),
        ('input_usage', 'Input Usage Report'),
        ('crop_health', 'Crop Health Report'),
        ('season_comparison', 'Season Comparison'),
        ('crop_profitability', 'Crop Profitability Report'),
        
        # Livestock Reports
        ('livestock_inventory', 'Animal Inventory'),
        ('livestock_health', 'Livestock Health Report'),
        ('production', 'Production Report'),
        ('breeding', 'Breeding Report'),
        ('mortality', 'Mortality Report'),
        ('veterinary', 'Veterinary Report'),
        ('feed_consumption', 'Feed Consumption Report'),
        
        # Equipment
        ('equipment_inventory', 'Equipment Inventory'),
        ('rental_history', 'Rental Report'),
        ('maintenance', 'Maintenance Report'),
        ('equipment_utilization', 'Equipment Utilization'),
        
        # Financial
        ('profit_loss', 'Profit & Loss'),
        ('cash_flow', 'Cash Flow Report'),
        ('transactions', 'Transaction History'),
        ('budget_actual', 'Budget vs Actual'),
        ('tax', 'Tax Report'),
        
        # Labor
        ('hours', 'Hours Report'),
        ('payroll', 'Payroll Report'),
        ('attendance', 'Attendance Report'),
        ('productivity', 'Productivity Report'),
        
        # Marketplace
        ('sales', 'Sales Report'),
        ('inventory', 'Inventory Report'),
        ('orders', 'Order Report'),
        ('customers', 'Customer Report'),
        
        # Pest & Disease
        ('pest_incidence', 'Pest Incidence Report'),
        ('treatment', 'Treatment Report'),
        ('outbreak', 'Outbreak Report'),
        
        # Insurance
        ('insurance_policies', 'Policy Report'),
        ('claims', 'Claims Report'),
        ('risk_assessment', 'Risk Assessment'),
        
        # Weather
        ('weather_log', 'Weather Log'),
        ('weather_alerts', 'Alert History'),
        ('weather_impact', 'Weather Impact Report'),
        
        # Compliance
        ('audit_trail', 'Audit Trail'),
        ('certification', 'Certification Report'),
        ('regulatory', 'Regulatory Compliance'),
    ]
    
    EXPORT_FORMATS = [
        ('pdf', 'PDF'),
        ('csv', 'CSV'),
        ('excel', 'Excel'),
        ('json', 'JSON'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('generating', 'Generating'),
        ('ready', 'Ready'),
        ('error', 'Error'),
    ]
    
    farm = models.ForeignKey('Farm', on_delete=models.CASCADE, related_name='reports')
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Date range
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Filters
    filters = models.JSONField(default=dict, help_text='Applied filters (field, crop, animal, etc)')
    
    # Export settings
    export_format = models.CharField(max_length=10, choices=EXPORT_FORMATS, default='pdf')
    include_charts = models.BooleanField(default=True)
    include_summary = models.BooleanField(default=True)
    include_raw_data = models.BooleanField(default=False)
    
    # Generated report
    file_path = models.FileField(upload_to='reports/', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    
    # Scheduling
    is_scheduled = models.BooleanField(default=False)
    schedule_frequency = models.CharField(max_length=20, choices=[
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ], blank=True)
    schedule_day_of_week = models.IntegerField(null=True, blank=True, help_text='0=Monday, 6=Sunday')
    schedule_day_of_month = models.IntegerField(null=True, blank=True)
    schedule_email_recipients = models.JSONField(default=list, help_text='Email addresses to send report to')
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='reports_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_generated = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'reports'
        indexes = [
            models.Index(fields=['farm', 'report_type']),
            models.Index(fields=['created_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.farm.name} - {self.get_report_type_display()}"


# ============================================================
# FEATURE 2: DOSING PROGRAM (Medication Management)
# ============================================================

class Medication(models.Model):
    """Medication/drug inventory"""
    
    farm = models.ForeignKey('Farm', on_delete=models.CASCADE, related_name='medications')
    name = models.CharField(max_length=255)
    generic_name = models.CharField(max_length=255)
    dosage_form = models.CharField(max_length=100)
    strength = models.CharField(max_length=100, help_text='e.g., 10,000 IU/ml')
    
    # Inventory
    quantity_in_stock = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=50, help_text='e.g., doses, ml, tablets, vials')
    reorder_level = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Expiry and storage
    batch_number = models.CharField(max_length=100, blank=True)
    expiry_date = models.DateField()
    storage_location = models.CharField(max_length=255, blank=True)
    storage_temp_min = models.IntegerField(null=True, blank=True, help_text='Min temp in Celsius')
    storage_temp_max = models.IntegerField(null=True, blank=True, help_text='Max temp in Celsius')
    
    # Withdrawal period
    meat_withdrawal_days = models.IntegerField(default=0, help_text='Days before meat can be sold')
    milk_withdrawal_days = models.IntegerField(default=0, help_text='Days before milk can be sold')
    egg_withdrawal_days = models.IntegerField(default=0, help_text='Days before eggs can be sold')
    
    # Cost
    cost_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    supplier = models.CharField(max_length=255, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'medications'
        indexes = [
            models.Index(fields=['farm', 'name']),
            models.Index(fields=['expiry_date']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.strength})"


class DosagePrescrip(models.Model):
    """Prescription/dosing protocol"""
    
    farm = models.ForeignKey('Farm', on_delete=models.CASCADE, related_name='prescriptions')
    medication = models.ForeignKey(Medication, on_delete=models.PROTECT, related_name='prescriptions')
    
    # Prescription details
    prescribed_by = models.CharField(max_length=255, help_text='Veterinarian name')
    prescription_date = models.DateField()
    expiry_date = models.DateField()
    prescription_number = models.CharField(max_length=50, unique=True)
    
    # Dosage info
    dosage_per_kg = models.CharField(max_length=100, help_text='e.g., 10,000 IU/kg')
    route = models.CharField(max_length=100, choices=[
        ('oral', 'Oral'),
        ('intramuscular', 'Intramuscular'),
        ('intravenous', 'Intravenous'),
        ('subcutaneous', 'Subcutaneous'),
        ('topical', 'Topical'),
        ('intramammary', 'Intramammary'),
    ])
    frequency = models.CharField(max_length=100, help_text='e.g., Every 24 hours')
    duration_days = models.IntegerField()
    
    # Refills
    refills_allowed = models.IntegerField(default=0)
    refills_used = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'dosage_prescriptions'
    
    def __str__(self):
        return f"Rx #{self.prescription_number} - {self.medication.name}"


class TreatmentRecord(models.Model):
    """Individual treatment/medication administration record"""
    
    farm = models.ForeignKey('Farm', on_delete=models.CASCADE, related_name='treatments')
    livestock = models.ForeignKey('Livestock', on_delete=models.SET_NULL, null=True, related_name='treatments')
    medication = models.ForeignKey(Medication, on_delete=models.PROTECT)
    prescription = models.ForeignKey(DosagePrescrip, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Treatment details
    treatment_date = models.DateTimeField()
    condition_diagnosed = models.CharField(max_length=255)
    condition_description = models.TextField()
    
    # Dosage given
    actual_dose_given = models.CharField(max_length=100)
    dose_unit = models.CharField(max_length=50)
    route_used = models.CharField(max_length=100)
    
    # Administration
    administered_by = models.CharField(max_length=255, help_text='Veterinarian/technician name')
    next_dose_due = models.DateTimeField(null=True, blank=True)
    treatment_end_date = models.DateField(null=True, blank=True)
    
    # Withdrawal status
    meat_withdrawal_until = models.DateField(null=True, blank=True)
    milk_withdrawal_until = models.DateField(null=True, blank=True)
    egg_withdrawal_until = models.DateField(null=True, blank=True)
    
    # Follow-up
    follow_up_scheduled = models.DateTimeField(null=True, blank=True)
    follow_up_completed = models.BooleanField(default=False)
    treatment_outcome = models.CharField(max_length=20, choices=[
        ('recovered', 'Recovered'),
        ('improving', 'Improving'),
        ('no_change', 'No Change'),
        ('worsened', 'Worsened'),
        ('pending', 'Pending'),
    ], blank=True)
    
    # Attachments
    notes = models.TextField(blank=True)
    attachments = models.JSONField(default=list, help_text='File paths to attachments')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'treatment_records'
        indexes = [
            models.Index(fields=['farm', 'treatment_date']),
            models.Index(fields=['livestock']),
        ]
    
    def __str__(self):
        return f"Treatment - {self.livestock.name if self.livestock else 'Unknown'} ({self.treatment_date})"


class WithdrawalPeriod(models.Model):
    """Tracks animals in withdrawal periods"""
    
    farm = models.ForeignKey('Farm', on_delete=models.CASCADE, related_name='withdrawal_periods')
    livestock = models.ForeignKey('Livestock', on_delete=models.CASCADE, related_name='withdrawals')
    treatment_record = models.ForeignKey(TreatmentRecord, on_delete=models.CASCADE)
    medication = models.ForeignKey(Medication, on_delete=models.PROTECT)
    
    # Withdrawal details
    product_type = models.CharField(max_length=20, choices=[
        ('meat', 'Meat'),
        ('milk', 'Milk'),
        ('eggs', 'Eggs'),
        ('all', 'All Products'),
    ])
    withdrawal_until = models.DateField()
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'withdrawal_periods'
        indexes = [
            models.Index(fields=['farm', 'product_type']),
            models.Index(fields=['withdrawal_until']),
        ]
    
    def __str__(self):
        return f"{self.livestock.name} - {self.get_product_type_display()} withdrawal"


# ============================================================
# FEATURE 3: BREEDING FEATURE (Complete Reproduction Management)
# ============================================================

class BreedingRecord(models.Model):
    """Records breeding/insemination events"""
    
    BREEDING_METHODS = [
        ('natural', 'Natural Service'),
        ('ai', 'Artificial Insemination'),
        ('embryo', 'Embryo Transfer'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Confirmation'),
        ('confirmed', 'Confirmed'),
        ('failed', 'Failed'),
        ('unknown', 'Unknown Status'),
    ]
    
    farm = models.ForeignKey('Farm', on_delete=models.CASCADE, related_name='breeding_records')
    dam = models.ForeignKey('Livestock', on_delete=models.CASCADE, related_name='breed_as_dam')
    sire = models.ForeignKey('Livestock', on_delete=models.SET_NULL, null=True, blank=True, related_name='breed_as_sire')
    
    # Breeding details
    breeding_date = models.DateField()
    breeding_method = models.CharField(max_length=20, choices=BREEDING_METHODS)
    location = models.CharField(max_length=255, blank=True)
    
    # For AI
    ai_technician = models.CharField(max_length=255, blank=True)
    semen_batch_number = models.CharField(max_length=100, blank=True)
    
    # Pregnancy tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    pregnancy_checked_date = models.DateField(null=True, blank=True)
    is_pregnant = models.BooleanField(null=True, blank=True)
    expected_calving_date = models.DateField(null=True, blank=True)
    gestation_period_days = models.IntegerField(default=285, help_text='Expected gestation period')
    
    # Cost
    breeding_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Notes
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'breeding_records'
        indexes = [
            models.Index(fields=['farm', 'breeding_date']),
            models.Index(fields=['dam']),
            models.Index(fields=['expected_calving_date']),
        ]
    
    def __str__(self):
        return f"{self.dam.name} - Bred on {self.breeding_date}"


class HeatDetection(models.Model):
    """Heat/estrous detection records"""
    
    farm = models.ForeignKey('Farm', on_delete=models.CASCADE, related_name='heat_detections')
    livestock = models.ForeignKey('Livestock', on_delete=models.CASCADE, related_name='heat_records')
    
    # Heat details
    detection_date = models.DateField()
    detection_time = models.TimeField()
    detected_by = models.CharField(max_length=255, blank=True)
    
    # Signs observed
    signs_observed = models.JSONField(default=list, help_text='List of heat signs observed')
    confidence_level = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # Breeding window
    optimal_breeding_start = models.DateTimeField()
    optimal_breeding_end = models.DateTimeField()
    
    # Cycle info
    days_since_last_heat = models.IntegerField(null=True, blank=True)
    expected_next_heat = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'heat_detections'
        indexes = [
            models.Index(fields=['livestock', 'detection_date']),
        ]
    
    def __str__(self):
        return f"{self.livestock.name} - Heat on {self.detection_date}"


class PregnancyRecord(models.Model):
    """Pregnancy tracking"""
    
    TRIMESTER_CHOICES = [
        ('first', 'First Trimester'),
        ('second', 'Second Trimester'),
        ('third', 'Third Trimester'),
    ]
    
    farm = models.ForeignKey('Farm', on_delete=models.CASCADE, related_name='pregnancies')
    breeding_record = models.OneToOneField(BreedingRecord, on_delete=models.CASCADE, related_name='pregnancy')
    dam = models.ForeignKey('Livestock', on_delete=models.CASCADE, related_name='pregnancies_as_dam')
    
    # Confirmation
    pregnancy_confirmed_date = models.DateField()
    confirmation_method = models.CharField(max_length=100, help_text='e.g., Ultrasound, Blood test')
    
    # Expected due date
    expected_due_date = models.DateField()
    
    # Health monitoring
    health_status = models.CharField(max_length=50, choices=[
        ('normal', 'Normal'),
        ('at_risk', 'At Risk'),
        ('complications', 'Complications'),
    ], default='normal')
    current_trimester = models.CharField(max_length=20, choices=TRIMESTER_CHOICES, blank=True)
    
    # Monitoring dates
    first_check_date = models.DateField(null=True, blank=True)
    second_check_date = models.DateField(null=True, blank=True)
    third_check_date = models.DateField(null=True, blank=True)
    next_check_date = models.DateField(null=True, blank=True)
    
    # Notes
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'pregnancy_records'
        indexes = [
            models.Index(fields=['expected_due_date']),
        ]
    
    def __str__(self):
        return f"{self.dam.name} - Due {self.expected_due_date}"


class CalvingRecord(models.Model):
    """Birth/calving records"""
    
    BIRTH_EASE_CHOICES = [
        ('normal', 'Normal'),
        ('assisted', 'Assisted'),
        ('difficult', 'Difficult/Dystocia'),
    ]
    
    farm = models.ForeignKey('Farm', on_delete=models.CASCADE, related_name='calvings')
    pregnancy_record = models.OneToOneField(PregnancyRecord, on_delete=models.CASCADE, related_name='calving')
    dam = models.ForeignKey('Livestock', on_delete=models.CASCADE, related_name='calvings_as_dam')
    
    # Calving details
    calving_date = models.DateField()
    calving_time = models.TimeField()
    birth_ease = models.CharField(max_length=20, choices=BIRTH_EASE_CHOICES)
    assisted_by = models.CharField(max_length=255, blank=True)
    
    # Offspring created via signal
    offspring_count = models.IntegerField(default=1)
    offspring = models.OneToOneField('Livestock', on_delete=models.SET_NULL, null=True, blank=True, related_name='origin_calving')
    
    # Complications
    complications = models.TextField(blank=True)
    complications_managed = models.BooleanField(default=False)
    
    # Colostrum management
    colostrum_fed = models.BooleanField(default=False)
    colostrum_fed_time = models.TimeField(null=True, blank=True)
    colostrum_amount_liters = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Health
    dam_health_status = models.CharField(max_length=50, choices=[
        ('healthy', 'Healthy'),
        ('recovering', 'Recovering'),
        ('complications', 'Complications'),
    ], default='healthy')
    
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'calving_records'
        indexes = [
            models.Index(fields=['calving_date']),
        ]
    
    def __str__(self):
        return f"{self.dam.name} - Calved on {self.calving_date}"


class BreedingAnalytics(models.Model):
    """Breeding performance analytics and summaries"""
    
    farm = models.ForeignKey('Farm', on_delete=models.CASCADE, related_name='breeding_analytics')
    
    # Performance metrics
    conception_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text='Percentage')
    services_per_conception = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    average_calving_interval_days = models.IntegerField(default=0)
    
    #Sire performance
    top_sires = models.JSONField(default=list, help_text='List of best performing sires')
    
    # Date range
    start_date = models.DateField()
    end_date = models.DateField()
    
    calculated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'breeding_analytics'
    
    def __str__(self):
        return f"{self.farm.name} - Breeding Analytics"


# ============================================================
# FEATURE 4: REMINDER SYSTEM  
# ============================================================

class Reminder(models.Model):
    """Smart reminders for all farm activities"""
    
    REMINDER_TYPES = [
        # Crops
        ('planting_window', 'Planting Window'),
        ('fertilizer_application', 'Fertilizer Application'),
        ('irrigation', 'Irrigation'),
        ('pest_inspection', 'Pest Inspection'),
        ('harvest_maturity', 'Harvest Maturity'),
        
        # Livestock
        ('vaccination_due', 'Vaccination Due'),
        ('deworming_due', 'Deworming Due'),
        ('heat_detection', 'Heat Detection'),
        ('pregnancy_check', 'Pregnancy Check'),
        ('calving_alert', 'Calving Alert'),
        ('weaning_reminder', 'Weaning Reminder'),
        ('hoof_trim', 'Hoof Trimming'),
        ('treatment_followup', 'Treatment Follow-up'),
        
        # Equipment
        ('service_due', 'Service Due'),
        ('rental_return', 'Rental Return'),
        ('insurance_renewal', 'Insurance Renewal'),
        ('inspection_due', 'Inspection Due'),
        
        # Financial
        ('invoice_due', 'Invoice Due'),
        ('subscription_renewal', 'Subscription Renewal'),
        ('tax_filing', 'Tax Filing'),
        ('payroll_day', 'Payroll Day'),
        
        # Marketplace
        ('listing_expiring', 'Listing Expiring'),
        ('order_to_ship', 'Order to Ship'),
        ('delivery_confirmation', 'Delivery Confirmation'),
        
        # Health & Safety
        ('first_aid_check', 'First Aid Kit Check'),
        ('fire_extinguisher', 'Fire Extinguisher Check'),
        ('safety_training', 'Safety Training Renewal'),
        
        # Other
        ('custom', 'Custom Reminder'),
    ]
    
    PRIORITY_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]
    
    NOTIFICATION_CHANNELS = [
        ('push', 'Push Notification'),
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('in_app', 'In-App'),
    ]
    
    farm = models.ForeignKey('Farm', on_delete=models.CASCADE, related_name='reminders')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reminders')
    
    # Reminder definition
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    reminder_type = models.CharField(max_length=50, choices=REMINDER_TYPES)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    
    # Related objects
    field = models.ForeignKey('Field', on_delete=models.SET_NULL, null=True, blank=True)
    crop = models.ForeignKey('Crop', on_delete=models.SET_NULL, null=True, blank=True)
    livestock = models.ForeignKey('Livestock', on_delete=models.SET_NULL, null=True, blank=True)
    equipment = models.ForeignKey('Equipment', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Schedule
    due_date = models.DateField()
    due_time = models.TimeField(default='08:00')
    
    # Recurrence
    is_recurring = models.BooleanField(default=False)
    recurrence_pattern = models.CharField(max_length=50, choices=[
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ], blank=True)
    recurrence_end_date = models.DateField(null=True, blank=True)
    
    # Notification
    notification_channels = models.JSONField(default=list)
    days_before_alert = models.IntegerField(default=1, help_text='Send alert N days before due date')
    
    # Status
    is_active = models.BooleanField(default=True)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_snoozed = models.BooleanField(default=False)
    snoozed_until = models.DateTimeField(null=True, blank=True)
    
    # Auto-task creation
    auto_create_task = models.BooleanField(default=False)
    task = models.OneToOneField('Task', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Notes
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'reminders'
        indexes = [
            models.Index(fields=['farm', 'due_date']),
            models.Index(fields=['user']),
            models.Index(fields=['is_completed']),
        ]
    
    def __str__(self):
        return f"{self.title} - Due {self.due_date}"


class ReminderHistory(models.Model):
    """Track reminder delivery and completion"""
    
    reminder = models.ForeignKey(Reminder, on_delete=models.CASCADE, related_name='history')
    
    # Delivery
    notification_date = models.DateTimeField(auto_now_add=True)
    notification_channel = models.CharField(max_length=50)
    was_delivered = models.BooleanField(default=False)
    delivery_status = models.CharField(max_length=100, blank=True)
    
    # User interaction
    was_viewed = models.BooleanField(default=False)
    was_actioned = models.BooleanField(default=False)
    action_date = models.DateTimeField(null=True, blank=True)
    
    # Outcome
    completion_status = models.CharField(max_length=100, blank=True)
    
    class Meta:
        db_table = 'reminder_history'
    
    def __str__(self):
        return f"Reminder '{self.reminder.title}' - {self.notification_date}"


# ============================================================
# FEATURE 5: WATER MANAGEMENT SYSTEM
# ============================================================

class WaterSource(models.Model):
    """Water sources on the farm"""
    
    SOURCE_TYPES = [
        ('well', 'Well'),
        ('river', 'River'),
        ('dam', 'Dam/Pond'),
        ('tank', 'Tank/Cistern'),
        ('borehole', 'Borehole'),
        ('spring', 'Spring'),
        ('municipal', 'Municipal Supply'),
    ]
    
    farm = models.ForeignKey('Farm', on_delete=models.CASCADE, related_name='water_sources')
    
    name = models.CharField(max_length=255)
    source_type = models.CharField(max_length=50, choices=SOURCE_TYPES)
    
    # Capacity
    total_capacity_liters = models.BigIntegerField()
    current_level_liters = models.BigIntegerField()
    
    # Location
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    
    # Quality parameters
    ph_level = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    salinity_ppm = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    turbidity = models.CharField(max_length=50, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    last_tested = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'water_sources'
    
    def __str__(self):
        return f"{self.name} ({self.get_source_type_display()})"


class WaterUsageLog(models.Model):
    """Daily water usage tracking"""
    
    farm = models.ForeignKey('Farm', on_delete=models.CASCADE, related_name='water_usage')
    source = models.ForeignKey(WaterSource, on_delete=models.CASCADE, related_name='usage_logs')
    
    # Usage details
    usage_date = models.DateField()
    usage_type = models.CharField(max_length=50, choices=[
        ('irrigation', 'Irrigation'),
        ('livestock', 'Livestock'),
        ('domestic', 'Domestic'),
        ('cleaning', 'Cleaning'),
        ('other', 'Other'),
    ])
    
    liters_used = models.BigIntegerField()
    
    # Field/purpose
    field = models.ForeignKey('Field', on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(blank=True)
    
    # Cost
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'water_usage_logs'
        indexes = [
            models.Index(fields=['farm', 'usage_date']),
        ]
    
    def __str__(self):
        return f"{self.farm.name} - {self.liters_used}L on {self.usage_date}"


class WaterQualityTest(models.Model):
    """Water quality test results"""
    
    farm = models.ForeignKey('Farm', on_delete=models.CASCADE, related_name='water_quality_tests')
    source = models.ForeignKey(WaterSource, on_delete=models.CASCADE, related_name='quality_tests')
    
    # Test details
    test_date = models.DateField()
    test_time = models.TimeField()
    tested_by = models.CharField(max_length=255)
    
    # Parameters
    ph_level = models.DecimalField(max_digits=5, decimal_places=2)
    ec_ms_cm = models.DecimalField(max_digits=10, decimal_places=2)
    salinity_ppm = models.DecimalField(max_digits=10, decimal_places=2)
    turbidity_ntu = models.DecimalField(max_digits=10, decimal_places=2)
    hardness_ppm = models.DecimalField(max_digits=10, decimal_places=2)
    nitrate_ppm = models.DecimalField(max_digits=10, decimal_places=2)
    bacteria_level = models.CharField(max_length=255, blank=True)
    
    # Assessment
    is_safe = models.BooleanField(default=True)
    issues_found = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    
    # Lab info
    lab_name = models.CharField(max_length=255, blank=True)
    lab_report_reference = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'water_quality_tests'
    
    def __str__(self):
        return f"{self.source.name} - Quality Test {self.test_date}"


# ============================================================
# FEATURE 6: SOIL HEALTH MONITORING
# ============================================================

class SoilTest(models.Model):
    """Soil test results and analysis"""
    
    farm = models.ForeignKey('Farm', on_delete=models.CASCADE, related_name='soil_tests')
    field = models.ForeignKey('Field', on_delete=models.CASCADE, related_name='soil_tests')
    
    # Test details
    test_date = models.DateField()
    test_location_lat = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    test_location_lng = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    
    # Soil properties
    ph_level = models.DecimalField(max_digits=5, decimal_places=2)
    nitrogen_ppm = models.DecimalField(max_digits=10, decimal_places=2)
    phosphorus_ppm = models.DecimalField(max_digits=10, decimal_places=2)
    potassium_ppm = models.DecimalField(max_digits=10, decimal_places=2)
    organic_matter_percent = models.DecimalField(max_digits=5, decimal_places=2)
    calcium_ppm = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    magnesium_ppm = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sulfur_ppm = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Micronutrients
    iron_ppm = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    zinc_ppm = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    copper_ppm = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    manganese_ppm = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    boron_ppm = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Recommendations
    recommendations = models.JSONField(default=list, help_text='List of amendment recommendations')
    nutrient_requirements = models.JSONField(default=dict, help_text='Required nutrients and amounts')
    
    # Lab info
    lab_name = models.CharField(max_length=255)
    lab_report_reference = models.CharField(max_length=100)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'soil_tests'
        indexes = [
            models.Index(fields=['field', 'test_date']),
        ]
    
    def __str__(self):
        return f"{self.field.name} - Soil Test {self.test_date}"


class SoilAmendment(models.Model):
    """Soil amendments applied"""
    
    farm = models.ForeignKey('Farm', on_delete=models.CASCADE, related_name='soil_amendments')
    field = models.ForeignKey('Field', on_delete=models.CASCADE, related_name='amendments')
    
    # Amendment details
    amendment_date = models.DateField()
    amendment_type = models.CharField(max_length=100, help_text='e.g., Lime, Gypsum, Compost')
    product_name = models.CharField(max_length=255)
    quantity_kg = models.DecimalField(max_digits=10, decimal_places=2)
    application_rate_per_hectare = models.DecimalField(max_digits=10, decimal_places=2)
    
    #Cost
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Application method
    application_method = models.CharField(max_length=100, help_text='e.g., Broadcast, Banded')
    applied_by = models.CharField(max_length=255)
    
    # Expected outcome
    target_nutrient = models.CharField(max_length=100, blank=True)
    expected_ph_change = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Follow-up
    soil_test_after_date = models.DateField(null=True, blank=True)
    
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'soil_amendments'
    
    def __str__(self):
        return f"{self.field.name} - {self.amendment_type} ({self.amendment_date})"


class SoilHealthScore(models.Model):
    """Overall soil health assessment"""
    
    farm = models.ForeignKey('Farm', on_delete=models.CASCADE, related_name='soil_health_scores')
    field = models.ForeignKey('Field', on_delete=models.CASCADE, related_name='health_scores')
    
    # Scoring date
    assessment_date = models.DateField()
    
    # Scores (0-100)
    physical_health_score = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    chemical_health_score = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    biological_health_score = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    overall_health_score = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # Trend
    previous_score = models.IntegerField(null=True, blank=True)
    score_trend = models.CharField(max_length=20, choices=[
        ('improving', 'Improving'),
        ('stable', 'Stable'),
        ('declining', 'Declining'),
    ])
    
    # Recommendations
    recommendations = models.TextField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'soil_health_scores'
    
    def __str__(self):
        return f"{self.field.name} - Health Score {self.overall_health_score} ({self.assessment_date})"


# ============================================================
# FEATURE 7: TASK MANAGEMENT
# ============================================================

class Task(models.Model):
    """Farm tasks/activities to be completed"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]
    
    farm = models.ForeignKey('Farm', on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=255)
    description = models.TextField()
    
    # Assignment
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks')
    assigned_role = models.CharField(max_length=100, blank=True, help_text='Role if not assigned to specific user')
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='tasks_created')
    
    # Dates
    due_date = models.DateField()
    due_time = models.TimeField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    completed_date = models.DateField(null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    
    # Related
    field = models.ForeignKey('Field', on_delete=models.SET_NULL, null=True, blank=True)
    crop = models.ForeignKey('Crop', on_delete=models.SET_NULL, null=True, blank=True)
    livestock = models.ForeignKey('Livestock', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Attachments & verification
    attachments = models.JSONField(default=list)
    completion_photos = models.JSONField(default=list)
    completion_notes = models.TextField(blank=True)
    
    # Recurring
    is_template = models.BooleanField(default=False)
    parent_template = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tasks'
        indexes = [
            models.Index(fields=['farm', 'due_date']),
            models.Index(fields=['assigned_to', 'status']),
        ]
    
    def __str__(self):
        return f"{self.title} - Due {self.due_date}"


class TaskComment(models.Model):
    """Comments on tasks for collaboration"""
    
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    content = models.TextField()
    attachments = models.JSONField(default=list)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'task_comments'
        indexes = [
            models.Index(fields=['task', 'created_at']),
        ]
    
    def __str__(self):
        return f"Comment on {self.task.title}"


# ============================================================
# FEATURE 8: DOCUMENT MANAGEMENT
# ============================================================

class Document(models.Model):
    """Centralized document repository"""
    
    DOCUMENT_CATEGORIES = [
        ('contract', 'Contract/Agreement'),
        ('certificate', 'Certificate'),
        ('license', 'License'),
        ('receipt', 'Receipt'),
        ('invoice', 'Invoice'),
        ('report', 'Report'),
        ('form', 'Form'),
        ('photo', 'Photo'),
        ('video', 'Video'),
        ('other', 'Other'),
    ]
    
    farm = models.ForeignKey('Farm', on_delete=models.CASCADE, related_name='documents')
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, choices=DOCUMENT_CATEGORIES)
    
    # File
    file = models.FileField(upload_to='documents/%Y/%m/%d/')
    file_size = models.BigIntegerField()  # in bytes
    file_type = models.CharField(max_length=50)
    
    # Important dates
    document_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    renewal_date = models.DateField(null=True, blank=True)
    
    # Version control
    version_number = models.IntegerField(default=1)
    previous_version = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Sharing
    is_shared = models.BooleanField(default=False)
    shared_with_users = models.ManyToManyField(User, blank=True, related_name='shared_documents')
    shared_with_roles = models.JSONField(default=list)
    
    # Status
    is_active = models.BooleanField(default=True)
    requires_signature = models.BooleanField(default=False)
    is_signed = models.BooleanField(default=False)
    
    # Metadata
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Tagging
    tags = models.JSONField(default=list)
    
    class Meta:
        db_table = 'documents'
        indexes = [
            models.Index(fields=['farm', 'category']),
            models.Index(fields=['expiry_date']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.get_category_display()})"


# ============================================================
# FEATURE 9: SUPPLY CHAIN TRACEABILITY
# ============================================================

class ProductBatch(models.Model):
    """Production batch tracking for traceability"""
    
    farm = models.ForeignKey('Farm', on_delete=models.CASCADE, related_name='product_batches')
    
    # Batch identification
    batch_id = models.CharField(max_length=100, unique=True)
    product_type = models.CharField(max_length=100, help_text='e.g., Maize, Tomatoes, Milk, Eggs')
    
    # Source
    field = models.ForeignKey('Field', on_delete=models.SET_NULL, null=True, blank=True)
    livestock = models.ForeignKey('Livestock', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Quantity
    total_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_unit = models.CharField(max_length=50)
    
    # Dates
    production_start_date = models.DateField()
    production_end_date = models.DateField(null=True, blank=True)
    manufacture_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    
    # Quality
    grade = models.CharField(max_length=20, choices=[
        ('a', 'Grade A'),
        ('b', 'Grade B'),
        ('c', 'Grade C'),
    ])
    quality_notes = models.TextField(blank=True)
    
    # Certifications
    certifications = models.JSONField(default=list)
    
    # Processing
    processing_notes = models.TextField(blank=True)
    packaged_date = models.DateField(null=True, blank=True)
    package_count = models.IntegerField(null=True, blank=True)
    
    # QR Code
    qr_code = models.CharField(max_length=255, unique=True)
    qr_code_image = models.ImageField(upload_to='qr_codes/', null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=50, choices=[
        ('produced', 'Produced'),
        ('packaged', 'Packaged'),
        ('in_storage', 'In Storage'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('sold', 'Sold'),
    ])
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'product_batches'
        indexes = [
            models.Index(fields=['batch_id']),
            models.Index(fields=['qr_code']),
        ]
    
    def __str__(self):
        return f"Batch {self.batch_id} - {self.product_type}"


class BatchTraceEntry(models.Model):
    """Event log for batch traceability"""
    
    batch = models.ForeignKey(ProductBatch, on_delete=models.CASCADE, related_name='trace_events')
    
    # Event
    event_type = models.CharField(max_length=100, help_text='e.g., Planted, Harvested, Packaged, Shipped')
    event_date = models.DateTimeField()
    location = models.CharField(max_length=255, blank=True)
    
    # Handler
    handled_by = models.CharField(max_length=255)
    handler_role = models.CharField(max_length=100)
    
    # Details
    description = models.TextField()
    quantity_change = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    quality_check = models.CharField(max_length=255, blank=True)
    
    # Next handler
    transferred_to = models.CharField(max_length=255, blank=True)
    transferred_to_organization = models.CharField(max_length=255, blank=True)
    
    attachments = models.JSONField(default=list)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'batch_trace_entries'
        ordering = ['event_date']
    
    def __str__(self):
        return f"{self.batch.batch_id} - {self.event_type}"


# ============================================================
# FEATURE 10: FARMER NETWORK & KNOWLEDGE SHARING
# Continue in next part...
# ============================================================
