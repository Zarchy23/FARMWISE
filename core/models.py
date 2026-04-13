# core/models.py
# FARMWISE - Complete Agriculture Management System
# Production Ready Code

from django.db import models
from django.contrib.auth.models import AbstractUser
# from django.contrib.gis.db import models as gis_models  # Enable after PostGIS setup
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal
import uuid
import os
from datetime import datetime

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def product_image_upload_path(instance, filename):
    """
    Generate organized upload path for product images.
    Structure: marketplace/products/{year}/{month}/{seller_id}/{product_id}/{filename}
    """
    # Get extension
    ext = os.path.splitext(filename)[1].lower()
    
    # Create clean filename: product_id_timestamp.ext
    clean_filename = f"product_{instance.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
    
    # Organize by year/month/seller/product
    path = datetime.now().strftime('marketplace/products/%Y/%m/')
    path += f"seller_{instance.seller.id}/product_{instance.id}/"
    
    return path + clean_filename

# ============================================================
# SECTION 1: USER & ACCOUNT MANAGEMENT
# ============================================================

class User(AbstractUser):
    """Extended user model for all system users"""
    
    USER_TYPES = [
        ('farmer', 'Smallholder Farmer'),
        ('large_farmer', 'Large Scale Farmer'),
        ('cooperative_admin', 'Cooperative Administrator'),
        ('agronomist', 'Agronomist/Extension Officer'),
        ('equipment_owner', 'Equipment Owner'),
        ('insurance_agent', 'Insurance Agent'),
        ('market_trader', 'Market Trader'),
        ('veterinarian', 'Veterinarian'),
        ('lab_technician', 'Soil Lab Technician'),
        ('supermarket', 'Supermarket/Agricultural Shop'),
        ('admin', 'System Administrator'),
    ]
    
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='farmer')
    phone_number = models.CharField(
        max_length=20, 
        unique=True,
        validators=[RegexValidator(
            regex=r'^[0-9+\-\s()]{9,}$',
            message='Enter a valid phone number (e.g., +254712345678 or 0712345678)'
        )]
    )
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    preferred_language = models.CharField(max_length=10, default='en')
    accepts_sms = models.BooleanField(default=True)
    accepts_email = models.BooleanField(default=True)
    farm_name = models.CharField(max_length=255, blank=True)
    location_lat = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    location_lng = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    id_number = models.CharField(max_length=50, blank=True)
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    last_active = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # RBAC Fields
    assigned_farms = models.ManyToManyField(
        'Farm', 
        blank=True, 
        related_name='assigned_to_users',
        help_text='For agronomists/veterinarians: farms they are assigned to'
    )
    cooperative_member = models.ForeignKey(
        'Cooperative',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='members',
        help_text='For farmers: the cooperative they belong to'
    )
    permissions = models.JSONField(
        default=dict,
        blank=True,
        help_text='Custom permission overrides (JSON format)'
    )
    is_active_member = models.BooleanField(
        default=True,
        help_text='For cooperative members: whether they are active in the cooperative'
    )
    
    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['user_type']),
            models.Index(fields=['phone_number']),
            models.Index(fields=['is_verified']),
            models.Index(fields=['cooperative_member']),
        ]
    
    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_user_type_display()})"
    
    @property
    def is_farmer(self):
        return self.user_type in ['farmer', 'large_farmer']
    
    @property
    def is_cooperative_admin(self):
        return self.user_type == 'cooperative_admin'
    
    @property
    def is_agronomist(self):
        return self.user_type == 'agronomist'
    
    @property
    def is_veterinarian(self):
        return self.user_type == 'veterinarian'
    
    @property
    def location(self):
        if self.location_lat and self.location_lng:
            return f"{self.location_lat}, {self.location_lng}"
        return None
    
    def get_assigned_farm_ids(self):
        """Get list of farm IDs assigned to this user"""
        return list(self.assigned_farms.values_list('id', flat=True))
    
    def get_cooperative_members(self):
        """If user is coop admin, get all members"""
        if self.user_type == 'cooperative_admin':
            return User.objects.filter(cooperative_member=self.cooperatives.first())
        return User.objects.none()
    
    def has_custom_permission(self, module: str, action: str) -> bool:
        """Check if user has custom permission override"""
        if self.permissions and module in self.permissions:
            return action in self.permissions[module]
        return False


class AuditLog(models.Model):
    """Track all user actions for compliance"""
    
    ACTIONS = [
        ('create', 'Create'),
        ('read', 'Read'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('export', 'Export'),
        ('activity', 'Activity'),
    ]
    
    SEVERITY_LEVELS = [
        ('critical', 'Critical'),
        ('high', 'High'),
        ('normal', 'Normal'),
        ('low', 'Low'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    action = models.CharField(max_length=20, choices=ACTIONS)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100)
    details = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    is_activity = models.BooleanField(default=False, help_text='Whether this is a timeline activity')
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS, default='normal')
    farm = models.ForeignKey('Farm', on_delete=models.SET_NULL, null=True, blank=True, related_name='activities')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'audit_logs'
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['model_name', 'object_id']),
            models.Index(fields=['farm', 'created_at']),
            models.Index(fields=['severity', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user} - {self.action} - {self.model_name} at {self.created_at}"


# ============================================================
# SECTION 1.5: VALIDATION & ACTIVITY LOGGING
# ============================================================

class ValidationRule(models.Model):
    """Manage validation rules for data entry"""
    
    CATEGORIES = [
        ('format', 'Format'),
        ('range', 'Range'),
        ('business_logic', 'Business Logic'),
        ('relationship', 'Relationship'),
        ('duplicate', 'Duplicate'),
    ]
    
    field_name = models.CharField(max_length=255)
    category = models.CharField(max_length=50, choices=CATEGORIES)
    rule_code = models.CharField(max_length=100, unique=True)
    message = models.TextField()
    rule_config = models.JSONField(default=dict, blank=True, help_text='Configuration for the rule')
    is_active = models.BooleanField(default=True)
    applies_to_models = models.JSONField(default=list, blank=True, help_text='List of model names this rule applies to')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'validation_rules'
    
    def __str__(self):
        return f"{self.rule_code} - {self.get_category_display()}"


class ValidationLog(models.Model):
    """Log all validation failures for audit trail"""
    
    SOURCES = [
        ('form', 'Web Form'),
        ('api', 'API'),
        ('import', 'Bulk Import'),
        ('mobile', 'Mobile'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='validation_logs')
    field_name = models.CharField(max_length=255)
    rule_code = models.CharField(max_length=100)
    provided_value = models.TextField(blank=True)
    expected_format = models.CharField(max_length=255, blank=True)
    form_or_api = models.CharField(max_length=20, choices=SOURCES)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'validation_logs'
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['rule_code']),
        ]
    
    def __str__(self):
        return f"{self.user} - {self.rule_code} - {self.created_at}"


class UserHistory(models.Model):
    """Track user field value history for auto-completion learning"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='field_history')
    field_name = models.CharField(max_length=255)
    field_value = models.TextField()
    usage_count = models.IntegerField(default=1)
    success_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    last_used = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_history'
        indexes = [
            models.Index(fields=['user', 'field_name']),
            models.Index(fields=['user', 'last_used']),
        ]
    
    def __str__(self):
        return f"{self.user} - {self.field_name} - {self.field_value}"


class FarmHistory(models.Model):
    """Track farm-level field value history for auto-completion learning"""
    
    farm = models.ForeignKey('Farm', on_delete=models.CASCADE, related_name='field_history')
    field_name = models.CharField(max_length=255)
    field_value = models.TextField()
    usage_count = models.IntegerField(default=1)
    success_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    last_used = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'farm_history'
        indexes = [
            models.Index(fields=['farm', 'field_name']),
        ]
    
    def __str__(self):
        return f"{self.farm.name} - {self.field_name} - {self.field_value}"


# ============================================================
# SUPERMARKET MANAGEMENT
# ============================================================

class Supermarket(models.Model):
    """Supermarket/Agricultural Shop Profile"""
    
    BUSINESS_TYPES = [
        ('retail', 'Retail Shop'),
        ('wholesale', 'Wholesale Distributor'),
        ('cooperative_shop', 'Cooperative Shop'),
        ('agro_dealer', 'Agro-Dealer'),
        ('hardware', 'Agricultural Hardware'),
        ('other', 'Other'),
    ]
    
    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name='supermarket_profile')
    shop_name = models.CharField(max_length=255)
    business_type = models.CharField(max_length=20, choices=BUSINESS_TYPES)
    registration_number = models.CharField(max_length=100, blank=True, unique=True, null=True)
    phone_number = models.CharField(max_length=20)
    physical_address = models.TextField()
    location_lat = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    location_lng = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    shop_image = models.ImageField(upload_to='supermarket/logos/', null=True, blank=True)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    operating_hours = models.JSONField(
        default=dict,
        blank=True,
        help_text='Store hours in JSON format: {"monday": "08:00-17:00", ...}'
    )
    products_categories = models.JSONField(
        default=list,
        blank=True,
        help_text='List of product categories they sell'
    )
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'supermarkets'
        indexes = [
            models.Index(fields=['owner']),
            models.Index(fields=['is_verified']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.shop_name} ({self.business_type})"


# ============================================================
# SECTION 2: FARM & FIELD MANAGEMENT
# ============================================================

class Cooperative(models.Model):
    """Farmer cooperative/group"""
    
    name = models.CharField(max_length=255)
    registration_number = models.CharField(max_length=100, unique=True)
    admin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='cooperatives')
    location = models.JSONField(null=True, blank=True)  # Store as {"lat": ..., "lng": ...} - switch to PointField with PostGIS
    address = models.TextField(blank=True)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    member_count = models.IntegerField(default=0)
    total_farm_area = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    bank_account = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'cooperatives'
        indexes = [
            models.Index(fields=['registration_number']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.name


class Farm(models.Model):
    """Main farm entity - connects everything"""
    
    FARM_TYPES = [
        ('crop', 'Crop Farm'),
        ('livestock', 'Livestock Farm'),
        ('mixed', 'Mixed Crop & Livestock'),
        ('agroforestry', 'Agroforestry'),
        ('aquaculture', 'Aquaculture'),
        ('poultry', 'Poultry Farm'),
        ('dairy', 'Dairy Farm'),
        ('organic', 'Organic Farm'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
    ]
    
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='farms')
    cooperative = models.ForeignKey(Cooperative, on_delete=models.SET_NULL, null=True, blank=True, related_name='farms')
    name = models.CharField(max_length=255)
    location = models.JSONField(null=True, blank=True)  # {"lat": ..., "lng": ...} - switch to PointField with PostGIS
    address = models.TextField(blank=True)
    total_area_hectares = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    farm_type = models.CharField(max_length=20, choices=FARM_TYPES)
    registration_number = models.CharField(max_length=50, unique=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    is_verified = models.BooleanField(default=False)
    bank_account = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'farms'
        indexes = [
            models.Index(fields=['owner', 'status']),
            models.Index(fields=['cooperative']),
            models.Index(fields=['registration_number']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.owner.get_full_name()}"
    
    @property
    def latitude(self):
        """Extract latitude from location JSON field"""
        if self.location and isinstance(self.location, dict):
            return self.location.get('lat') or self.location.get('latitude')
        return None
    
    @property
    def longitude(self):
        """Extract longitude from location JSON field"""
        if self.location and isinstance(self.location, dict):
            return self.location.get('lng') or self.location.get('longitude')
        return None
    
    def save(self, *args, **kwargs):
        if not self.registration_number:
            self.registration_number = f"FARM-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)


class Field(models.Model):
    """Individual field/plot within a farm"""
    
    SOIL_TYPES = [
        ('sandy', 'Sandy'),
        ('clay', 'Clay'),
        ('loamy', 'Loamy'),
        ('silty', 'Silty'),
        ('peaty', 'Peaty'),
        ('laterite', 'Laterite'),
        ('alluvial', 'Alluvial'),
        ('volcanic', 'Volcanic'),
    ]
    
    SLOPE_TYPES = [
        ('flat', 'Flat (0-3%)'),
        ('gentle', 'Gentle (3-8%)'),
        ('moderate', 'Moderate (8-15%)'),
        ('steep', 'Steep (15-25%)'),
        ('very_steep', 'Very Steep (>25%)'),
    ]
    
    DRAINAGE_TYPES = [
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('moderate', 'Moderate'),
        ('poor', 'Poor'),
        ('very_poor', 'Very Poor'),
    ]
    
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='fields')
    name = models.CharField(max_length=255)
    area_hectares = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    boundary = models.JSONField(null=True, blank=True)  # GeoJSON - switch to PolygonField with PostGIS
    soil_type = models.CharField(max_length=20, choices=SOIL_TYPES)
    slope = models.CharField(max_length=20, choices=SLOPE_TYPES, default='flat')
    drainage = models.CharField(max_length=20, choices=DRAINAGE_TYPES, default='good')
    elevation_meters = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    ph_level = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    irrigation_available = models.BooleanField(default=False)
    irrigation_type = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'fields'
        indexes = [
            models.Index(fields=['farm', 'is_active']),
            models.Index(fields=['soil_type']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.area_hectares} ha)"


# ============================================================
# SECTION 3: CROP MANAGEMENT
# ============================================================

class CropType(models.Model):
    """Master list of crops with default values"""
    
    CATEGORIES = [
        ('cereal', 'Cereal/Grain'),
        ('legume', 'Legume'),
        ('vegetable', 'Vegetable'),
        ('fruit', 'Fruit'),
        ('tuber', 'Tuber/Root'),
        ('cash', 'Cash Crop'),
        ('fodder', 'Fodder'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    scientific_name = models.CharField(max_length=200, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORIES)
    growing_days = models.IntegerField(help_text="Average days from planting to harvest")
    water_requirement_mm = models.IntegerField(help_text="Total water needed per season", null=True, blank=True)
    optimal_temp_min = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    optimal_temp_max = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    planting_distance_cm = models.IntegerField(null=True, blank=True)
    seed_rate_kg_per_ha = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    expected_yield_kg_per_ha = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    image = models.ImageField(upload_to='crops/%Y/%m/', null=True, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'crop_types'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['category']),
        ]
    
    def __str__(self):
        return self.name


class CropSeason(models.Model):
    """Crop planted in a specific field"""
    
    SEASONS = [
        ('main', 'Main Season'),
        ('off', 'Off Season'),
        ('dry', 'Dry Season'),
        ('wet', 'Wet Season'),
        ('long_rain', 'Long Rains'),
        ('short_rain', 'Short Rains'),
    ]
    
    STATUS = [
        ('planned', 'Planned'),
        ('planting', 'Planting'),
        ('planted', 'Planted'),
        ('growing', 'Growing'),
        ('ready_for_harvest', 'Ready for Harvest'),
        ('harvested', 'Harvested'),
        ('failed', 'Failed'),
        ('abandoned', 'Abandoned'),
    ]
    
    field = models.ForeignKey(Field, on_delete=models.CASCADE, related_name='crops')
    crop_type = models.ForeignKey(CropType, on_delete=models.CASCADE, related_name='seasons')
    variety = models.CharField(max_length=100, blank=True)
    season = models.CharField(max_length=20, choices=SEASONS)
    planting_date = models.DateField()
    expected_harvest_date = models.DateField()
    actual_harvest_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='planned')
    estimated_yield_kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    actual_yield_kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    estimated_revenue = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    actual_revenue = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    photo = models.ImageField(upload_to='crops/', null=True, blank=True, help_text="Crop photo (optional)")
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_crops')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'crop_seasons'
        indexes = [
            models.Index(fields=['field', 'status']),
            models.Index(fields=['planting_date']),
            models.Index(fields=['expected_harvest_date']),
        ]
        ordering = ['-planting_date']
    
    def __str__(self):
        return f"{self.crop_type.name} - {self.field.name} ({self.planting_date})"
    
    @property
    def days_to_harvest(self):
        if self.actual_harvest_date:
            return (self.actual_harvest_date - self.planting_date).days
        return None
    
    @property
    def is_overdue(self):
        if self.status == 'growing' and self.expected_harvest_date < timezone.now().date():
            return True
        return False


class InputApplication(models.Model):
    """Track fertilizers, pesticides, and other inputs"""
    
    INPUT_TYPES = [
        ('seed', 'Seeds'),
        ('fertilizer', 'Fertilizer'),
        ('pesticide', 'Pesticide'),
        ('herbicide', 'Herbicide'),
        ('fungicide', 'Fungicide'),
        ('organic', 'Organic Amendment'),
        ('soil_conditioner', 'Soil Conditioner'),
        ('other', 'Other'),
    ]
    
    UNITS = [
        ('kg', 'Kilogram'),
        ('g', 'Gram'),
        ('l', 'Liter'),
        ('ml', 'Milliliter'),
        ('bag', 'Bag'),
        ('bottle', 'Bottle'),
        ('unit', 'Unit'),
    ]
    
    crop_season = models.ForeignKey(CropSeason, on_delete=models.CASCADE, related_name='inputs')
    input_type = models.CharField(max_length=20, choices=INPUT_TYPES)
    product_name = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    unit = models.CharField(max_length=20, choices=UNITS)
    cost_per_unit = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    application_date = models.DateField()
    application_method = models.CharField(max_length=100, blank=True)
    applied_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'input_applications'
        indexes = [
            models.Index(fields=['crop_season', 'input_type']),
            models.Index(fields=['application_date']),
        ]
    
    def __str__(self):
        return f"{self.product_name} - {self.crop_season}"
    
    @property
    def total_cost(self):
        return self.quantity * self.cost_per_unit


class Harvest(models.Model):
    """Harvest records for crops"""
    
    QUALITY_GRADES = [
        ('premium', 'Premium Grade'),
        ('grade_a', 'Grade A'),
        ('grade_b', 'Grade B'),
        ('grade_c', 'Grade C'),
        ('reject', 'Rejected'),
    ]
    
    crop_season = models.ForeignKey(CropSeason, on_delete=models.CASCADE, related_name='harvests')
    harvest_date = models.DateField()
    quantity_kg = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    quality_grade = models.CharField(max_length=20, choices=QUALITY_GRADES)
    selling_price_kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    waste_kg = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    buyer_name = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    harvested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'harvests'
        indexes = [
            models.Index(fields=['crop_season', 'harvest_date']),
            models.Index(fields=['quality_grade']),
        ]
        ordering = ['-harvest_date']
    
    def __str__(self):
        return f"{self.crop_season} - {self.quantity_kg}kg on {self.harvest_date}"
    
    def save(self, *args, **kwargs):
        if self.selling_price_kg and self.quantity_kg:
            self.total_revenue = self.selling_price_kg * self.quantity_kg
        super().save(*args, **kwargs)


# ============================================================
# SECTION 4: LIVESTOCK MANAGEMENT
# ============================================================

class AnimalType(models.Model):
    """Master list of animal species/breeds"""
    
    SPECIES = [
        ('cattle', 'Cattle'),
        ('goat', 'Goat'),
        ('sheep', 'Sheep'),
        ('pig', 'Pig'),
        ('chicken', 'Chicken'),
        ('rabbit', 'Rabbit'),
        ('turkey', 'Turkey'),
        ('duck', 'Duck'),
        ('bee', 'Bee'),
    ]
    
    species = models.CharField(max_length=20, choices=SPECIES)
    breed = models.CharField(max_length=100)
    avg_lifespan_years = models.IntegerField(null=True, blank=True)
    gestation_days = models.IntegerField(null=True, blank=True)
    weaning_days = models.IntegerField(null=True, blank=True)
    avg_milk_liters_per_day = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    avg_egg_per_week = models.IntegerField(null=True, blank=True)
    market_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'animal_types'
        unique_together = ['species', 'breed']
        indexes = [
            models.Index(fields=['species']),
        ]
    
    def __str__(self):
        return f"{self.get_species_display()} - {self.breed}"


class Animal(models.Model):
    """Individual animal tracking"""
    
    GENDER = [
        ('male', 'Male'),
        ('female', 'Female'),
    ]
    
    STATUS = [
        ('alive', 'Alive'),
        ('sold', 'Sold'),
        ('dead', 'Dead'),
        ('missing', 'Missing'),
        ('slaughtered', 'Slaughtered'),
    ]
    
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='animals')
    animal_type = models.ForeignKey(AnimalType, on_delete=models.CASCADE, related_name='animals')
    tag_number = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER)
    birth_date = models.DateField(null=True, blank=True)
    purchase_date = models.DateField(null=True, blank=True)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='alive')
    mother = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='offspring')
    father = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    location = models.CharField(max_length=255, blank=True, help_text="Current pasture/shed")
    photo = models.ImageField(upload_to='animals/', null=True, blank=True, help_text="Animal photo (optional)")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'animals'
        indexes = [
            models.Index(fields=['farm', 'status']),
            models.Index(fields=['tag_number']),
            models.Index(fields=['animal_type']),
        ]
    
    def __str__(self):
        return f"{self.tag_number} - {self.animal_type.breed} ({self.get_gender_display()})"
    
    @property
    def age_months(self):
        if self.birth_date:
            today = timezone.now().date()
            months = (today.year - self.birth_date.year) * 12 + (today.month - self.birth_date.month)
            return months
        return None


class HealthRecord(models.Model):
    """Health tracking for animals"""
    
    RECORD_TYPES = [
        ('vaccination', 'Vaccination'),
        ('treatment', 'Treatment'),
        ('checkup', 'Checkup'),
        ('surgery', 'Surgery'),
        ('laboratory', 'Laboratory Test'),
    ]
    
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE, related_name='health_records')
    record_type = models.CharField(max_length=20, choices=RECORD_TYPES)
    record_date = models.DateField()
    diagnosis = models.CharField(max_length=255, blank=True)
    symptoms = models.TextField(blank=True)
    treatment = models.TextField(blank=True)
    medication_name = models.CharField(max_length=255, blank=True)
    dosage = models.CharField(max_length=100, blank=True)
    administered_by = models.CharField(max_length=255, blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    next_due_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'health_records'
        indexes = [
            models.Index(fields=['animal', 'record_date']),
            models.Index(fields=['next_due_date']),
        ]
        ordering = ['-record_date']
    
    def __str__(self):
        return f"{self.animal.tag_number} - {self.get_record_type_display()} on {self.record_date}"


class BreedingRecord(models.Model):
    """Breeding/Reproduction tracking"""
    
    RESULTS = [
        ('success', 'Successful - Pregnant'),
        ('failed', 'Failed'),
        ('aborted', 'Aborted'),
        ('gave_birth', 'Gave Birth'),
    ]
    
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE, related_name='breeding_records')
    breeding_date = models.DateField()
    mate_animal = models.ForeignKey(Animal, on_delete=models.SET_NULL, null=True, related_name='+')
    method = models.CharField(max_length=100, blank=True, help_text="Natural, Artificial Insemination")
    result = models.CharField(max_length=20, choices=RESULTS, null=True, blank=True)
    expected_calving_date = models.DateField(null=True, blank=True)
    actual_calving_date = models.DateField(null=True, blank=True)
    offspring_count = models.IntegerField(default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'breeding_records'
        indexes = [
            models.Index(fields=['animal', 'breeding_date']),
        ]
        ordering = ['-breeding_date']
    
    def __str__(self):
        return f"{self.animal.tag_number} - Bred on {self.breeding_date}"


class MilkProduction(models.Model):
    """Daily milk production tracking"""
    
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE, related_name='milk_records')
    production_date = models.DateField()
    morning_kg = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    evening_kg = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    total_kg = models.DecimalField(max_digits=6, decimal_places=2, editable=False)
    fat_content = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    protein_content = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'milk_production'
        unique_together = ['animal', 'production_date']
        indexes = [
            models.Index(fields=['animal', 'production_date']),
        ]
        ordering = ['-production_date']
    
    def save(self, *args, **kwargs):
        self.total_kg = self.morning_kg + self.evening_kg
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.animal.tag_number} - {self.production_date}: {self.total_kg}kg"


# ============================================================
# SECTION 5: EQUIPMENT RENTAL
# ============================================================

class Equipment(models.Model):
    """Farm equipment available for rent"""
    
    CATEGORIES = [
        ('tractor', 'Tractor'),
        ('harvester', 'Harvester'),
        ('planter', 'Planter'),
        ('sprayer', 'Sprayer'),
        ('plow', 'Plow'),
        ('cultivator', 'Cultivator'),
        ('trailer', 'Trailer'),
        ('irrigation', 'Irrigation Equipment'),
        ('other', 'Other'),
    ]
    
    STATUS = [
        ('available', 'Available'),
        ('rented', 'Rented'),
        ('maintenance', 'Under Maintenance'),
        ('broken', 'Broken'),
    ]
    
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_equipment')
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=20, choices=CATEGORIES)
    description = models.TextField(blank=True)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2)
    weekly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    monthly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    location = models.CharField(max_length=255)
    images = models.JSONField(default=list, blank=True)
    specifications = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='available')
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'equipment'
        indexes = [
            models.Index(fields=['owner', 'status']),
            models.Index(fields=['category']),
            models.Index(fields=['location']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class EquipmentBooking(models.Model):
    """Equipment rental bookings"""
    
    STATUS = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('disputed', 'Disputed'),
    ]
    
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='bookings')
    renter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='equipment_rentals')
    start_date = models.DateField()
    end_date = models.DateField()
    total_days = models.IntegerField(editable=False)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    deposit_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS, default='pending')
    pickup_location = models.CharField(max_length=255, blank=True)
    return_location = models.CharField(max_length=255, blank=True)
    renter_notes = models.TextField(blank=True)
    owner_notes = models.TextField(blank=True)
    rating_by_renter = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
    rating_by_owner = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'equipment_bookings'
        indexes = [
            models.Index(fields=['equipment', 'status']),
            models.Index(fields=['renter', 'status']),
            models.Index(fields=['start_date', 'end_date']),
        ]
    
    def save(self, *args, **kwargs):
        self.total_days = (self.end_date - self.start_date).days
        self.total_cost = self.total_days * self.equipment.daily_rate
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.equipment.name} - {self.renter.username} ({self.start_date} to {self.end_date})"


# ============================================================
# SECTION 6: MARKETPLACE
# ============================================================

class ProductListing(models.Model):
    """Products for sale in marketplace"""
    
    UNITS = [
        ('kg', 'Kilogram'),
        ('g', 'Gram'),
        ('ton', 'Ton'),
        ('liter', 'Liter'),
        ('piece', 'Piece'),
        ('bunch', 'Bunch'),
        ('crate', 'Crate'),
    ]
    
    STATUS = [
        ('active', 'Active'),
        ('sold', 'Sold'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]
    
    seller = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='listings')
    product_name = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20, choices=UNITS)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    images = models.ImageField(upload_to=product_image_upload_path, null=True, blank=True)
    harvest_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    is_organic = models.BooleanField(default=False)
    delivery_available = models.BooleanField(default=False)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS, default='active')
    is_out_of_stock = models.BooleanField(
        default=False,
        help_text='When marked out of stock: hidden from public marketplace but visible in seller dashboard'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'product_listings'
        indexes = [
            models.Index(fields=['seller', 'status']),
            models.Index(fields=['seller', 'is_out_of_stock']),
            models.Index(fields=['category']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.price_per_unit
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.product_name} - {self.quantity} {self.unit} @ ${self.price_per_unit}"


class Order(models.Model):
    """Purchase orders from buyers"""
    
    STATUS = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchases')
    listing = models.ForeignKey(ProductListing, on_delete=models.CASCADE, related_name='orders')
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    status = models.CharField(max_length=20, choices=STATUS, default='pending')
    delivery_address = models.TextField()
    buyer_notes = models.TextField(blank=True)
    seller_notes = models.TextField(blank=True)
    payment_method = models.CharField(max_length=50, blank=True)
    payment_status = models.CharField(max_length=20, default='pending')
    tracking_number = models.CharField(max_length=100, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'orders'
        indexes = [
            models.Index(fields=['buyer', 'status']),
            models.Index(fields=['listing']),
            models.Index(fields=['created_at']),
        ]
    
    def save(self, *args, **kwargs):
        self.subtotal = self.quantity * self.unit_price
        self.total_amount = self.subtotal + self.delivery_fee
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Order #{self.id} - {self.buyer.username}"


# ============================================================
# SECTION 7: PEST & DISEASE DETECTION
# ============================================================

class PestReport(models.Model):
    """AI-powered pest/disease detection reports"""
    
    SEVERITY = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('severe', 'Severe'),
    ]
    
    farmer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pest_reports')
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='pest_reports')
    field = models.ForeignKey(Field, on_delete=models.CASCADE, related_name='pest_reports', null=True, blank=True)
    crop = models.ForeignKey(CropSeason, on_delete=models.CASCADE, related_name='pest_reports', null=True, blank=True)
    image = models.ImageField(upload_to='pest_detection/%Y/%m/')
    ai_diagnosis = models.CharField(max_length=255)
    analysis_description = models.TextField(blank=True, help_text='Detailed AI analysis of the pest/disease')
    confidence = models.DecimalField(max_digits=5, decimal_places=2)
    severity = models.CharField(max_length=20, choices=SEVERITY)
    affected_area_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    treatment_recommended = models.TextField(blank=True)
    prevention_tips = models.TextField(blank=True)
    organic_options = models.TextField(blank=True, null=True)
    agronomist_verified = models.BooleanField(default=False)
    agronomist_notes = models.TextField(blank=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='verified_reports')
    status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'pest_reports'
        indexes = [
            models.Index(fields=['farmer', 'created_at']),
            models.Index(fields=['farm', 'status']),
            models.Index(fields=['ai_diagnosis']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.ai_diagnosis} - {self.confidence}% - {self.created_at.date()}"


# ============================================================
# SECTION 8: WEATHER & IRRIGATION
# ============================================================

class WeatherAlert(models.Model):
    """Weather alerts for farmers"""
    
    ALERT_TYPES = [
        ('drought', 'Drought Warning'),
        ('flood', 'Flood Warning'),
        ('frost', 'Frost Warning'),
        ('storm', 'Storm Warning'),
        ('heavy_rain', 'Heavy Rain'),
        ('high_wind', 'High Wind'),
        ('heatwave', 'Heatwave'),
    ]
    
    SEVERITY = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('alert', 'Alert'),
        ('emergency', 'Emergency'),
    ]
    
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='weather_alerts')
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    severity = models.CharField(max_length=20, choices=SEVERITY)
    title = models.CharField(max_length=255)
    message = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_read = models.BooleanField(default=False)
    is_acknowledged = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'weather_alerts'
        indexes = [
            models.Index(fields=['farm', 'is_read']),
            models.Index(fields=['start_date', 'end_date']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_alert_type_display()} - {self.farm.name}"


class WeatherData(models.Model):
    """Real-time weather data cached from OpenWeatherMap API"""
    
    farm = models.OneToOneField(Farm, on_delete=models.CASCADE, related_name='weather_data')
    
    # Current conditions
    temperature = models.FloatField(help_text='Temperature in Celsius')
    feels_like = models.FloatField(null=True, blank=True)
    humidity = models.IntegerField(help_text='Humidity percentage')
    pressure = models.IntegerField(help_text='Pressure in hPa', null=True, blank=True)
    wind_speed = models.FloatField(help_text='Wind speed in m/s')
    wind_direction = models.IntegerField(null=True, blank=True, help_text='Wind direction in degrees')
    cloudiness = models.IntegerField(null=True, blank=True, help_text='Cloud percentage')
    condition = models.CharField(max_length=100, help_text='Weather condition (e.g., "Sunny", "Rainy")')
    description = models.CharField(max_length=255, help_text='Detailed condition description')
    icon = models.CharField(max_length=50, null=True, blank=True, help_text='Weather icon code')
    
    # Forecast data (JSON stored as forecasts)
    forecast_data = models.JSONField(default=dict, help_text='5-day forecast data')
    
    # Metadata
    location = models.CharField(max_length=255, help_text='Location name/coordinates')
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'weather_data'
        verbose_name_plural = 'Weather Data'
        ordering = ['-last_updated']
    
    def __str__(self):
        return f"Weather for {self.farm.name} - {self.condition}"
    
    def is_stale(self):
        """Check if data is older than 30 minutes"""
        from django.utils import timezone
        return timezone.now() - self.last_updated > timezone.timedelta(minutes=30)


class IrrigationSchedule(models.Model):
    """Irrigation scheduling and tracking"""
    
    STATUS = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('skipped', 'Skipped'),
    ]
    
    field = models.ForeignKey(Field, on_delete=models.CASCADE, related_name='irrigation_schedules')
    scheduled_date = models.DateField()
    duration_hours = models.DecimalField(max_digits=5, decimal_places=2)
    water_volume_liters = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='scheduled')
    actual_date = models.DateField(null=True, blank=True)
    actual_duration_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'irrigation_schedules'
        indexes = [
            models.Index(fields=['field', 'scheduled_date']),
            models.Index(fields=['status']),
        ]
        ordering = ['scheduled_date']
    
    def __str__(self):
        return f"{self.field.name} - {self.scheduled_date} ({self.duration_hours}h)"


# ============================================================
# SECTION 9: INSURANCE
# ============================================================

class InsurancePolicy(models.Model):
    """Crop insurance policies"""
    
    POLICY_TYPES = [
        ('crop', 'Crop Insurance'),
        ('livestock', 'Livestock Insurance'),
        ('equipment', 'Equipment Insurance'),
    ]
    
    STATUS = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
        ('claimed', 'Claimed'),
    ]
    
    farmer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='insurance_policies')
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='insurance_policies')
    policy_type = models.CharField(max_length=20, choices=POLICY_TYPES)
    policy_number = models.CharField(max_length=100, unique=True)
    crop_type = models.CharField(max_length=100, blank=True)
    area_hectares = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    livestock_count = models.IntegerField(null=True, blank=True)
    sum_insured = models.DecimalField(max_digits=12, decimal_places=2)
    premium_paid = models.DecimalField(max_digits=12, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS, default='active')
    provider = models.CharField(max_length=255)
    policy_document = models.FileField(upload_to='insurance/%Y/%m/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'insurance_policies'
        indexes = [
            models.Index(fields=['farmer', 'status']),
            models.Index(fields=['policy_number']),
            models.Index(fields=['end_date']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.policy_number:
            self.policy_number = f"INS-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.policy_number} - {self.farmer.username}"


class InsuranceClaim(models.Model):
    """Insurance claims"""
    
    STATUS = [
        ('pending', 'Pending Review'),
        ('investigating', 'Under Investigation'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('paid', 'Paid'),
    ]
    
    policy = models.ForeignKey(InsurancePolicy, on_delete=models.CASCADE, related_name='claims')
    claim_date = models.DateField(auto_now_add=True)
    damage_date = models.DateField()
    damage_percentage = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)])
    estimated_loss = models.DecimalField(max_digits=12, decimal_places=2)
    approved_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    payout_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    description = models.TextField()
    photos = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='pending')
    adjuster_notes = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='reviewed_claims')
    paid_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'insurance_claims'
        indexes = [
            models.Index(fields=['policy', 'status']),
            models.Index(fields=['claim_date']),
        ]
        ordering = ['-claim_date']
    
    def __str__(self):
        return f"Claim on {self.policy.policy_number} - {self.get_status_display()}"


# ============================================================
# SECTION 10: LABOR MANAGEMENT
# ============================================================

class Worker(models.Model):
    """Farm workers"""
    
    worker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='worker_profiles')
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='workers')
    hourly_wage = models.DecimalField(max_digits=8, decimal_places=2)
    skills = models.JSONField(default=list, blank=True, null=True)
    hire_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    emergency_contact = models.CharField(max_length=255, blank=True)
    emergency_phone = models.CharField(max_length=15, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'workers'
        unique_together = ['worker', 'farm']
        indexes = [
            models.Index(fields=['farm', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.worker.get_full_name()} - {self.farm.name}"


class WorkShift(models.Model):
    """Individual work shifts"""
    
    TASKS = [
        ('planting', 'Planting'),
        ('weeding', 'Weeding'),
        ('harvesting', 'Harvesting'),
        ('irrigation', 'Irrigation'),
        ('fertilizing', 'Fertilizing'),
        ('pesticide', 'Pesticide Application'),
        ('pruning', 'Pruning'),
        ('feeding', 'Animal Feeding'),
        ('milking', 'Milking'),
        ('cleaning', 'Cleaning'),
        ('maintenance', 'Maintenance'),
        ('other', 'Other'),
    ]
    
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE, related_name='shifts')
    field = models.ForeignKey(Field, on_delete=models.SET_NULL, null=True, blank=True, related_name='shifts')
    date = models.DateField()
    task = models.CharField(max_length=20, choices=TASKS)
    hours_worked = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0)])
    wage_rate = models.DecimalField(max_digits=8, decimal_places=2)
    total_pay = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='recorded_shifts')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'work_shifts'
        indexes = [
            models.Index(fields=['worker', 'date']),
            models.Index(fields=['field', 'date']),
        ]
        ordering = ['-date']
    
    def save(self, *args, **kwargs):
        self.total_pay = self.hours_worked * self.wage_rate
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.worker.worker.get_full_name()} - {self.date} - {self.hours_worked}h"


class Payroll(models.Model):
    """Payroll records"""
    
    STATUS = [
        ('pending', 'Pending'),
        ('processed', 'Processed'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ]
    
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE, related_name='payrolls')
    period_start = models.DateField()
    period_end = models.DateField()
    total_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total_pay = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_pay = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS, default='pending')
    payment_date = models.DateField(null=True, blank=True)
    payment_method = models.CharField(max_length=50, blank=True)
    transaction_id = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payrolls'
        indexes = [
            models.Index(fields=['worker', 'status']),
            models.Index(fields=['period_start', 'period_end']),
        ]
    
    def __str__(self):
        return f"{self.worker.worker.get_full_name()} - {self.period_start} to {self.period_end}"


# ============================================================
# SECTION 11: FINANCIAL TRACKING
# ============================================================

class Transaction(models.Model):
    """Financial transactions for farms"""
    
    TRANSACTION_TYPES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]
    
    CATEGORIES = [
        ('crop_sales', 'Crop Sales'),
        ('livestock_sales', 'Livestock Sales'),
        ('equipment_rental', 'Equipment Rental Income'),
        ('salary', 'Salary/Wages'),
        ('input', 'Farm Inputs'),
        ('equipment', 'Equipment Purchase'),
        ('maintenance', 'Maintenance'),
        ('transport', 'Transport'),
        ('insurance', 'Insurance'),
        ('tax', 'Tax'),
        ('other', 'Other'),
    ]
    
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    category = models.CharField(max_length=20, choices=CATEGORIES)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    date = models.DateField()
    description = models.CharField(max_length=255)
    reference = models.CharField(max_length=100, blank=True)
    receipt = models.FileField(upload_to='receipts/%Y/%m/', null=True, blank=True)
    related_crop = models.ForeignKey(CropSeason, on_delete=models.SET_NULL, null=True, blank=True)
    related_animal = models.ForeignKey(Animal, on_delete=models.SET_NULL, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'transactions'
        indexes = [
            models.Index(fields=['farm', 'transaction_type', 'date']),
            models.Index(fields=['category']),
        ]
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} - ${self.amount} - {self.date}"


# ============================================================
# SECTION 12: NOTIFICATIONS
# ============================================================

class Notification(models.Model):
    """System notifications for users"""
    
    NOTIFICATION_TYPES = [
        ('alert', 'Alert'),
        ('reminder', 'Reminder'),
        ('info', 'Information'),
        ('success', 'Success'),
        ('warning', 'Warning'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    link = models.CharField(max_length=500, blank=True)
    is_read = models.BooleanField(default=False)
    sent_via_sms = models.BooleanField(default=False)
    sent_via_email = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notifications'
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"


# ============================================================
# SECTION 8: PHASE 2 - CONTEXTUAL HELP SYSTEM
# ============================================================

class HelpContent(models.Model):
    """Contextual help system for user guidance"""
    
    TRIGGER_TYPES = [
        ('first_time', 'First Time User'),
        ('inactivity', 'Inactivity Alert'),
        ('error_recovery', 'Error Recovery'),
        ('opportunity', 'Opportunity-Based'),
        ('manual_request', 'Manual Request'),
    ]
    
    CONTENT_TYPES = [
        ('text', 'Text'),
        ('video', 'Video'),
        ('guide', 'Step-by-Step Guide'),
        ('faq', 'FAQ'),
        ('tooltip', 'Tooltip'),
    ]
    
    CATEGORIES = [
        ('crops', 'Crops'),
        ('livestock', 'Livestock'),
        ('equipment', 'Equipment'),
        ('market', 'Marketplace'),
        ('financial', 'Financial'),
        ('reporting', 'Reporting'),
        ('general', 'General'),
    ]
    
    category = models.CharField(max_length=50, choices=CATEGORIES)
    trigger_type = models.CharField(max_length=50, choices=TRIGGER_TYPES)
    content_type = models.CharField(max_length=50, choices=CONTENT_TYPES)
    title = models.CharField(max_length=255)
    content = models.TextField()
    video_url = models.URLField(blank=True, null=True)
    target_page = models.CharField(max_length=255, blank=True, help_text='e.g., /crops/create/')
    target_element = models.CharField(max_length=255, blank=True, help_text='CSS selector for element to highlight')
    priority = models.IntegerField(default=0, help_text='Higher number = shown first')
    is_active = models.BooleanField(default=True)
    view_count = models.IntegerField(default=0)
    helpful_count = models.IntegerField(default=0)
    not_helpful_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'help_content'
        indexes = [
            models.Index(fields=['category', 'trigger_type']),
            models.Index(fields=['is_active', 'priority']),
            models.Index(fields=['target_page']),
        ]
        ordering = ['-priority', '-created_at']
    
    def __str__(self):
        return f"{self.category} - {self.title}"


# ============================================================
# SECTION 9: PHASE 3 - TEMPLATE LIBRARY & RECURRING ACTIONS
# ============================================================

class Template(models.Model):
    """Save and reuse operations as templates"""
    
    CATEGORIES = [
        ('crop_plan', 'Crop Plan'),
        ('treatment', 'Treatment'),
        ('equipment_listing', 'Equipment Listing'),
        ('schedule', 'Schedule'),
        ('report', 'Report'),
    ]
    
    SHARE_LEVELS = [
        ('private', 'Private'),
        ('farm', 'Farm Only'),
        ('cooperative', 'Cooperative'),
        ('public', 'Public Marketplace'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='templates')
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, null=True, blank=True, related_name='templates')
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=50, choices=CATEGORIES)
    description = models.TextField(blank=True)
    template_data = models.JSONField(help_text='Serialized template configuration')
    share_level = models.CharField(max_length=20, choices=SHARE_LEVELS, default='private')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text='Price if shared on marketplace')
    is_active = models.BooleanField(default=True)
    usage_count = models.IntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    total_ratings = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'templates'
        indexes = [
            models.Index(fields=['user', 'category']),
            models.Index(fields=['share_level', 'is_active']),
            models.Index(fields=['farm']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class TemplateRating(models.Model):
    """User ratings for shared templates"""
    
    template = models.ForeignKey(Template, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    review = models.TextField(blank=True)
    is_helpful = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'template_ratings'
        unique_together = ['template', 'user']
        indexes = [
            models.Index(fields=['template']),
            models.Index(fields=['rating']),
        ]
    
    def __str__(self):
        return f"{self.template.name} - {self.rating}★ by {self.user.username}"


class RecurringAction(models.Model):
    """Automated recurring farm tasks"""
    
    FREQUENCIES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('seasonal', 'Seasonal'),
        ('custom', 'Custom CRON'),
    ]
    
    STATUS = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('archived', 'Archived'),
    ]
    
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='recurring_actions')
    action_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    frequency = models.CharField(max_length=20, choices=FREQUENCIES)
    cron_expression = models.CharField(max_length=255, help_text='CRON expression for scheduling')
    action_config = models.JSONField(help_text='Action-specific configuration data')
    assigned_to = models.ManyToManyField(User, blank=True, related_name='assigned_recurring_actions')
    status = models.CharField(max_length=20, choices=STATUS, default='active')
    next_due = models.DateTimeField(null=True, blank=True)
    last_executed = models.DateTimeField(null=True, blank=True)
    execution_count = models.IntegerField(default=0)
    missed_count = models.IntegerField(default=0)
    paused_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'recurring_actions'
        indexes = [
            models.Index(fields=['farm', 'status']),
            models.Index(fields=['next_due']),
            models.Index(fields=['frequency']),
        ]
        ordering = ['next_due', '-created_at']
    
    def __str__(self):
        return f"{self.farm.name} - {self.action_name}"


class RecurringActionLog(models.Model):
    """Execution history for recurring actions"""
    
    STATUSES = [
        ('pending', 'Pending'),
        ('executed', 'Executed'),
        ('missed', 'Missed'),
        ('failed', 'Failed'),
    ]
    
    action = models.ForeignKey(RecurringAction, on_delete=models.CASCADE, related_name='execution_logs')
    scheduled_for = models.DateTimeField()
    executed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    executed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUSES, default='pending')
    notes = models.TextField(blank=True)
    result_data = models.JSONField(null=True, blank=True, help_text='Result or error details')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'recurring_action_logs'
        indexes = [
            models.Index(fields=['action', 'scheduled_for']),
            models.Index(fields=['status']),
        ]
        ordering = ['-scheduled_for']
    
    def __str__(self):
        return f"{self.action.action_name} - {self.scheduled_for}"


class BatchOperation(models.Model):
    """Batch operations on multiple records"""
    
    OPERATION_TYPES = [
        ('crop_harvest', 'Bulk Crop Harvest'),
        ('price_update', 'Price Update'),
        ('status_change', 'Status Change'),
        ('data_export', 'Data Export'),
        ('field_update', 'Field Data Update'),
    ]
    
    STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='batch_operations')
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='batch_operations')
    operation_type = models.CharField(max_length=50, choices=OPERATION_TYPES)
    description = models.CharField(max_length=255)
    record_count = models.IntegerField()
    record_ids = models.JSONField(help_text='List of affected record IDs')
    parameters = models.JSONField(help_text='Operation-specific parameters')
    status = models.CharField(max_length=20, choices=STATUS, default='pending')
    progress_percent = models.IntegerField(default=0)
    results = models.JSONField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'batch_operations'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['farm', 'created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_operation_type_display()} - {self.record_count} records"


# ============================================================
# SECTION 10: PHASE 4 - SMART PREDICTIONS
# ============================================================

class Prediction(models.Model):
    """AI/ML predictions for farm decisions"""
    
    PREDICTION_TYPES = [
        ('harvest_date', 'Harvest Date'),
        ('yield_estimate', 'Yield Estimate'),
        ('pest_risk', 'Pest Risk'),
        ('price_forecast', 'Price Forecast'),
        ('maintenance_needed', 'Maintenance Needed'),
        ('disease_risk', 'Disease Risk'),
        ('water_requirement', 'Water Requirement'),
    ]
    
    OBJECT_TYPES = [
        ('crop', 'Crop'),
        ('field', 'Field'),
        ('animal', 'Animal'),
        ('equipment', 'Equipment'),
        ('market', 'Market Price'),
    ]
    
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='predictions')
    prediction_type = models.CharField(max_length=50, choices=PREDICTION_TYPES)
    object_type = models.CharField(max_length=50, choices=OBJECT_TYPES)
    object_id = models.IntegerField(help_text='ID of the related object (crop, field, animal, etc.)')
    predicted_value = models.CharField(max_length=255, help_text='The prediction result')
    confidence_score = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(1)]
    )
    forecast_date = models.DateField(help_text='Date when prediction applies')
    model_version = models.CharField(max_length=50, default='v1')
    reasoning = models.TextField(blank=True, help_text='Explanation for the prediction')
    factors_used = models.JSONField(default=list, help_text='List of factors used in prediction')
    is_actionable = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'predictions'
        indexes = [
            models.Index(fields=['farm', 'prediction_type']),
            models.Index(fields=['forecast_date']),
            models.Index(fields=['confidence_score']),
        ]
        ordering = ['-forecast_date', '-confidence_score']
    
    def __str__(self):
        return f"{self.farm.name} - {self.get_prediction_type_display()}"


# ============================================================
# SECTION 11: PHASE 5 - SCHEDULED EXPORTS
# ============================================================

class ScheduledExport(models.Model):
    """Scheduled data exports"""
    
    EXPORT_TYPES = [
        ('crops', 'Crop Data'),
        ('livestock', 'Livestock Data'),
        ('financial', 'Financial Summary'),
        ('marketplace', 'Marketplace Activity'),
        ('custom', 'Custom Report'),
    ]
    
    FORMATS = [
        ('csv', 'CSV'),
        ('json', 'JSON'),
        ('xlsx', 'Excel'),
        ('pdf', 'PDF'),
        ('html', 'HTML'),
    ]
    
    FREQUENCIES = [
        ('once', 'One-Time'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scheduled_exports')
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, null=True, blank=True)
    export_type = models.CharField(max_length=50, choices=EXPORT_TYPES)
    file_format = models.CharField(max_length=20, choices=FORMATS)
    frequency = models.CharField(max_length=20, choices=FREQUENCIES, default='once')
    filters = models.JSONField(default=dict, blank=True, help_text='Export filters (date range, etc.)')
    email_recipients = models.JSONField(default=list, help_text='List of email addresses')
    include_summary = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    last_run = models.DateTimeField(null=True, blank=True)
    next_run = models.DateTimeField(null=True, blank=True)
    run_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'scheduled_exports'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['farm', 'frequency']),
            models.Index(fields=['next_run']),
        ]
        ordering = ['next_run', '-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_export_type_display()}"


# ============================================================
# SECTION 12: PHASE 6 - WORKSPACE PREFERENCES
# ============================================================

class WorkspacePreference(models.Model):
    """User workspace switching preferences"""
    
    WORKSPACE_TYPES = [
        ('farmer', 'Farmer View'),
        ('agronomist', 'Agronomist View'),
        ('coop_manager', 'Cooperative Manager'),
        ('equipment_owner', 'Equipment Owner'),
        ('trader', 'Market Trader'),
        ('admin', 'Administrator'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='workspace_preference')
    primary_workspace = models.CharField(max_length=50, choices=WORKSPACE_TYPES)
    secondary_workspaces = models.JSONField(default=list, help_text='List of secondary workspace types')
    last_accessed_workspace = models.CharField(max_length=50, choices=WORKSPACE_TYPES)
    last_accessed_at = models.DateTimeField(auto_now=True)
    workspace_state = models.JSONField(default=dict, help_text='Saved state for each workspace (filters, views, etc.)')
    default_farm = models.ForeignKey(Farm, on_delete=models.SET_NULL, null=True, blank=True)
    quick_stats_layout = models.JSONField(default=dict, help_text='Dashboard widget configuration')
    theme_preference = models.CharField(max_length=20, default='auto', choices=[('light', 'Light'), ('dark', 'Dark'), ('auto', 'Auto')])
    notifications_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'workspace_preferences'
        indexes = [
            models.Index(fields=['primary_workspace']),
            models.Index(fields=['last_accessed_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.primary_workspace}"

# ==== NEW FEATURES ADDED ====
# ==============================================================
# ESSENTIAL NEW FEATURES - Carefully Designed to Integrate
# with Existing FarmWise Models (Animal, Farm, Field, Crop, etc)
# ==============================================================
# (Add the following models to the end of core/models.py)


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
    shared_with_users = models.ManyToManyField(User, blank=True, related_name='feature_shared_documents')
    
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='feature_documents_uploaded')
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
# FEATURE 6: WEATHER ALERTS (RENAMED - Extended)
# ============================================================

class WeatherAlertFeature(models.Model):
    """Extended weather alert tracking"""
    
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='weather_feature_alerts')
    
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
        db_table = 'feature_weather_alerts_extended'
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
    description = models.TextField(blank=True, default='')
    
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


# ============================================================
# FEATURE 10: FARMER NETWORK & KNOWLEDGE SHARING
# ============================================================

class DiscussionForum(models.Model):
    """Discussion forums for farmers to share knowledge"""
    
    CATEGORIES = [
        ('crop_production', 'Crop Production'),
        ('livestock', 'Livestock Management'),
        ('pest_disease', 'Pest & Disease Control'),
        ('soil_water', 'Soil & Water Management'),
        ('equipment', 'Equipment & Machinery'),
        ('markets', 'Markets & Sales'),
        ('financing', 'Financing & Credit'),
        ('climate', 'Climate & Weather'),
        ('certification', 'Certification & Compliance'),
        ('general', 'General Discussion'),
    ]
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORIES)
    
    # Moderator
    is_moderated = models.BooleanField(default=True)
    moderators = models.ManyToManyField(User, related_name='moderated_forums', blank=True)
    
    # Settings
    allow_attachments = models.BooleanField(default=True)
    allow_external_links = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Statistics
    member_count = models.IntegerField(default=0)
    post_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'discussion_forums'
    
    def __str__(self):
        return self.title


class ForumThread(models.Model):
    """Individual discussion thread"""
    
    forum = models.ForeignKey(DiscussionForum, on_delete=models.CASCADE, related_name='threads')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='forum_threads')
    
    title = models.CharField(max_length=255)
    content = models.TextField()
    
    # Status
    is_pinned = models.BooleanField(default=False)
    is_closed = models.BooleanField(default=False)
    
    # Engagement
    view_count = models.IntegerField(default=0)
    reply_count = models.IntegerField(default=0)
    
    # Tags
    tags = models.JSONField(default=list)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'forum_threads'
        indexes = [
            models.Index(fields=['forum', 'is_pinned', 'created_at']),
        ]
    
    def __str__(self):
        return self.title


class ForumReply(models.Model):
    """Reply to forum thread"""
    
    thread = models.ForeignKey(ForumThread, on_delete=models.CASCADE, related_name='replies')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    
    content = models.TextField()
    attachments = models.JSONField(default=list)
    
    # Recognition
    is_helpful = models.BooleanField(default=False)
    helpful_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'forum_replies'
    
    def __str__(self):
        return f"Reply to {self.thread.title}"


class GroupBuyingInitiative(models.Model):
    """Group buying opportunities for farmers"""
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    product_type = models.CharField(max_length=255, help_text='e.g., Fertilizer, Seeds, Equipment')
    
    # Quantity
    minimum_order_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_unit = models.CharField(max_length=50)
    unit_price_without_group = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price_with_group = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Discount
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2)
    
    # Timeline
    start_date = models.DateField()
    end_date = models.DateField()
    delivery_date = models.DateField(null=True, blank=True)
    
    # Organizer
    organizer = models.CharField(max_length=255)
    organizer_contact = models.CharField(max_length=255)
    
    # Participants
    farmers_joined = models.IntegerField(default=0)
    total_quantity_pledged = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Status
    status = models.CharField(max_length=20, choices=[
        ('open', 'Open'),
        ('closed', 'Closed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ])
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'group_buying_initiatives'
    
    def __str__(self):
        return self.title


class GroupBuyingParticipant(models.Model):
    """Farmer participation in group buying"""
    
    initiative = models.ForeignKey(GroupBuyingInitiative, on_delete=models.CASCADE, related_name='participants')
    farmer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_buys')
    
    quantity_pledged = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_received = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Payment
    payment_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('partial', 'Partial'),
        ('refunded', 'Refunded'),
    ], default='pending')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'group_buying_participants'
        unique_together = [['initiative', 'farmer']]
    
    def __str__(self):
        return f"{self.farmer.username} - {self.initiative.title}"


# ============================================================
# FEATURE 11: CARBON FOOTPRINT TRACKER
# ============================================================

class EmissionSource(models.Model):
    """Track farm emission sources"""
    
    SOURCES = [
        ('fuel_diesel', 'Diesel Fuel'),
        ('fuel_petrol', 'Petrol/Gasoline'),
        ('electricity', 'Electricity'),
        ('lpg', 'LPG/Gas'),
        ('fertilizer', 'Fertilizer (Synthetic)'),
        ('pesticide', 'Pesticide Application'),
        ('transport_input', 'Transport of Inputs'),
        ('transport_output', 'Transport of Products'),
        ('livestock_enteric', 'Livestock Enteric Fermentation'),
        ('manure', 'Manure Management'),
        ('machinery', 'Machinery/Equipment'),
        ('other', 'Other'),
    ]
    
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='emission_sources')
    
    source_type = models.CharField(max_length=50, choices=SOURCES)
    name = models.CharField(max_length=255)
    
    # Emission factor
    emission_factor = models.DecimalField(max_digits=10, decimal_places=4, help_text='kg CO2e per unit')
    unit = models.CharField(max_length=50, help_text='e.g., liter, kWh, kg')
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'emission_sources'
    
    def __str__(self):
        return f"{self.get_source_type_display()} - {self.name}"


class EmissionRecord(models.Model):
    """Monthly emission records"""
    
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='emission_records')
    source = models.ForeignKey(EmissionSource, on_delete=models.PROTECT)
    
    # Record
    record_date = models.DateField()
    quantity_used = models.DecimalField(max_digits=10, decimal_places=2)
    calculated_emissions_kg_co2e = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Details
    description = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'emission_records'
        indexes = [
            models.Index(fields=['farm', 'record_date']),
        ]
    
    def __str__(self):
        return f"{self.farm.name} - {self.source.name} ({self.record_date})"


class CarbonSequestration(models.Model):
    """Carbon sequestration activities"""
    
    SEQUESTRATION_TYPES = [
        ('trees', 'Trees/Forestry'),
        ('agroforestry', 'Agroforestry'),
        ('soil_carbon', 'Soil Carbon'),
        ('compost', 'Composting'),
        ('mulch', 'Mulching'),
        ('wetland', 'Wetland Conservation'),
        ('other', 'Other'),
    ]
    
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='sequestration_activities')
    
    activity_type = models.CharField(max_length=50, choices=SEQUESTRATION_TYPES)
    name = models.CharField(max_length=255)
    description = models.TextField()
    
    # Quantity
    area_hectares = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tree_count = models.IntegerField(null=True, blank=True)
    
    # Sequestration rate
    annual_sequestration_kg_co2e = models.DecimalField(max_digits=10, decimal_places=2)
    
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'carbon_sequestration'
    
    def __str__(self):
        return f"{self.farm.name} - {self.get_activity_type_display()}"


# ============================================================
# FEATURE 12: FARM MAP & GEOFENCING
# ============================================================

class FarmBoundary(models.Model):
    """Farm physical boundaries"""
    
    farm = models.OneToOneField(Farm, on_delete=models.CASCADE, related_name='boundary')
    
    # Coordinates (GeoJSON format)
    geojson_boundary = models.JSONField(help_text='GeoJSON polygon of farm boundary')
    
    # Area calculation
    total_area_hectares = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Center point
    center_latitude = models.DecimalField(max_digits=10, decimal_places=7)
    center_longitude = models.DecimalField(max_digits=10, decimal_places=7)
    
    # Metadata
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'farm_boundaries'
    
    def __str__(self):
        return f"{self.farm.name} Boundary"


class Geofence(models.Model):
    """Geofences for livestock tracking"""
    
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='geofences')
    
    name = models.CharField(max_length=255)
    
    # Boundary (GeoJSON)
    geojson_boundary = models.JSONField(help_text='GeoJSON polygon for geofence')
    
    # Alert settings
    enable_exit_alerts = models.BooleanField(default=True)
    enable_entry_alerts = models.BooleanField(default=False)
    alert_channels = models.JSONField(default=list)  # ['sms', 'email', 'push']
    
    # Associated field/pasture
    field = models.ForeignKey(Field, on_delete=models.SET_NULL, null=True, blank=True)
    assigned_livestock = models.ManyToManyField('Animal', blank=True)
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'geofences'
    
    def __str__(self):
        return f"{self.farm.name} - {self.name}"


class LivestockLocation(models.Model):
    """Real-time livestock location tracking"""
    
    livestock = models.ForeignKey('Animal', on_delete=models.CASCADE, related_name='location_history')
    
    latitude = models.DecimalField(max_digits=10, decimal_places=7)
    longitude = models.DecimalField(max_digits=10, decimal_places=7)
    
    # Accuracy
    accuracy_meters = models.IntegerField(null=True, blank=True)
    
    # GPS device info
    device_id = models.CharField(max_length=100, blank=True)
    signal_strength = models.IntegerField(null=True, blank=True, help_text='0-100')
    
    # Geofence status
    is_inside_assigned_geofence = models.BooleanField(default=True)
    
    recorded_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'livestock_locations'
        indexes = [
            models.Index(fields=['livestock', 'recorded_at']),
        ]
    
    def __str__(self):
        return f"{self.livestock.name} location"


class GeofenceAlert(models.Model):
    """Alerts when livestock breaches geofence"""
    
    geofence = models.ForeignKey(Geofence, on_delete=models.CASCADE, related_name='alerts')
    livestock = models.ForeignKey('Animal', on_delete=models.CASCADE)
    
    # Alert type
    alert_type = models.CharField(max_length=20, choices=[
        ('entry', 'Entry'),
        ('exit', 'Exit'),
    ])
    
    # Location
    latitude = models.DecimalField(max_digits=10, decimal_places=7)
    longitude = models.DecimalField(max_digits=10, decimal_places=7)
    
    # Status
    is_resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    
    alert_time = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'geofence_alerts'
    
    def __str__(self):
        return f"Geofence {self.alert_type.upper()} - {self.livestock.name}"


# ============================================================
# FEATURE 13: OFFLINE SYNC & DATA MANAGEMENT
# ============================================================

class OfflineSyncQueue(models.Model):
    """Queue for offline sync when connection restored"""
    
    OPERATION_TYPES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sync_queue')
    
    # Operation details
    model_name = models.CharField(max_length=100)  # e.g., 'Crop', 'Livestock'
    operation = models.CharField(max_length=20, choices=OPERATION_TYPES)
    object_id = models.CharField(max_length=100, null=True, blank=True)
    
    # Data
    data_payload = models.JSONField()
    
    # Status
    is_synced = models.BooleanField(default=False)
    sync_error = models.TextField(blank=True)
    sync_attempted_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'offline_sync_queue'
        indexes = [
            models.Index(fields=['user', 'is_synced']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.operation} {self.model_name}"


class SyncConflict(models.Model):
    """Track sync conflicts when offline changes conflict with server"""
    
    sync_entry = models.ForeignKey(OfflineSyncQueue, on_delete=models.CASCADE, related_name='conflicts')
    
    # Conflict details
    server_version = models.JSONField()
    local_version = models.JSONField()
    
    conflicting_fields = models.JSONField(default=list)
    
    # Resolution
    resolution_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('resolved_auto', 'Auto Resolved'),
        ('resolved_manual', 'Manual Resolved'),
    ], default='pending')
    resolved_data = models.JSONField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'sync_conflicts'
    
    def __str__(self):
        return f"Sync Conflict - {self.sync_entry.model_name}"


# ============================================================
# FEATURE 14: WEATHER ENHANCEMENT - DETAILED FORECASTS
# ============================================================

class WeatherForecast(models.Model):
    """Detailed hourly/daily weather forecast"""
    
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='weather_forecasts')
    
    # Location
    latitude = models.DecimalField(max_digits=10, decimal_places=7)
    longitude = models.DecimalField(max_digits=10, decimal_places=7)
    
    # Forecast date
    forecast_date = models.DateField()
    forecast_time = models.TimeField()
    recorded_at = models.DateTimeField()
    
    # Weather data
    temperature_celsius = models.DecimalField(max_digits=5, decimal_places=1)
    feels_like_celsius = models.DecimalField(max_digits=5, decimal_places=1)
    min_temp_celsius = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    max_temp_celsius = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    
    humidity_percent = models.IntegerField()
    pressure_hpa = models.DecimalField(max_digits=7, decimal_places=1)
    wind_speed_kmh = models.DecimalField(max_digits=5, decimal_places=1)
    wind_direction_degrees = models.IntegerField(null=True, blank=True)
    wind_gust_kmh = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    
    rainfall_mm = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    rainfall_probability_percent = models.IntegerField(default=0)
    
    cloud_coverage_percent = models.IntegerField()
    visibility_km = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    
    uv_index = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    
    # Conditions
    weather_condition = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Growing degree days
    gdd = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, help_text='Growing Degree Days')
    
    # Farm impact
    farming_recommendation = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'weather_forecasts'
        indexes = [
            models.Index(fields=['farm', 'forecast_date']),
        ]
    
    def __str__(self):
        return f"Forecast for {self.farm.name} - {self.forecast_date}"


# ============================================================
# FEATURE 15: FARM PROJECTS MANAGEMENT
# ============================================================

class FarmProject(models.Model):
    """Track farm projects across all 12 categories"""
    
    CATEGORIES = [
        ('crop', '🌾 Crop Production'),
        ('livestock', '🐄 Livestock Production'),
        ('processing', '🏭 Agro-processing'),
        ('infrastructure', '🏗️ Farm Infrastructure'),
        ('soil', '🌱 Soil & Land Management'),
        ('pest', '🐛 Pest & Disease Management'),
        ('mechanization', '🚜 Farm Mechanization'),
        ('marketing', '📢 Marketing & Sales'),
        ('tourism', '🏕️ Farm Tourism'),
        ('sustainability', '🌍 Organic & Sustainability'),
        ('training', '📚 Training & Capacity Building'),
        ('financial', '💰 Financial & Business'),
    ]
    
    PRIORITY = [
        ('critical', '🔴 Critical'),
        ('high', '🟠 High'),
        ('medium', '🟡 Medium'),
        ('low', '🟢 Low'),
    ]
    
    STATUS = [
        ('planning', '📋 Planning'),
        ('in_progress', '⚙️ In Progress'),
        ('on_hold', '⏸️ On Hold'),
        ('completed', '✅ Completed'),
        ('cancelled', '❌ Cancelled'),
    ]
    
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='projects')
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=20, choices=CATEGORIES)
    description = models.TextField()
    start_date = models.DateField()
    target_end_date = models.DateField()
    actual_end_date = models.DateField(null=True, blank=True)
    budget = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    actual_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    priority = models.CharField(max_length=10, choices=PRIORITY, default='medium')
    status = models.CharField(max_length=20, choices=STATUS, default='planning')
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_projects')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'farm_projects'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['farm', 'status']),
            models.Index(fields=['category', 'priority']),
            models.Index(fields=['target_end_date']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.farm.name}"
    
    @property
    def progress(self):
        """Calculate project progress percentage"""
        tasks = self.tasks.all()
        if not tasks.exists():
            return 0
        completed = tasks.filter(completed=True).count()
        return int((completed / tasks.count()) * 100)
    
    @property
    def budget_variance(self):
        """Calculate budget variance"""
        if self.budget and self.actual_cost:
            return float(self.actual_cost - self.budget)
        return None
    
    @property
    def days_remaining(self):
        """Calculate days until target end date"""
        if self.target_end_date and self.status != 'completed':
            remaining = (self.target_end_date - timezone.now().date()).days
            return max(0, remaining)
        return None
    
    @property
    def is_overdue(self):
        """Check if project is overdue"""
        if self.status in ['planning', 'in_progress'] and self.target_end_date < timezone.now().date():
            return True
        return False


class ProjectTask(models.Model):
    """Individual tasks within a project"""
    
    project = models.ForeignKey(FarmProject, on_delete=models.CASCADE, related_name='tasks')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_project_tasks')
    due_date = models.DateField()
    completed = models.BooleanField(default=False)
    completed_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'project_tasks'
        ordering = ['due_date']
        indexes = [
            models.Index(fields=['project', 'completed']),
            models.Index(fields=['assigned_to', 'due_date']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.project.name}"


class ProjectResource(models.Model):
    """Resources allocated to projects"""
    
    RESOURCE_TYPES = [
        ('labor', '👥 Labor'),
        ('equipment', '🚜 Equipment'),
        ('material', '📦 Material'),
        ('capital', '💰 Capital'),
        ('land', '🗺️ Land'),
        ('water', '💧 Water'),
    ]
    
    project = models.ForeignKey(FarmProject, on_delete=models.CASCADE, related_name='resources')
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPES)
    name = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    unit = models.CharField(max_length=50, blank=True)
    cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'project_resources'
        indexes = [
            models.Index(fields=['project', 'resource_type']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.project.name}"


class ProjectMilestone(models.Model):
    """Key milestones for tracking progress"""
    
    project = models.ForeignKey(FarmProject, on_delete=models.CASCADE, related_name='milestones')
    name = models.CharField(max_length=255)
    target_date = models.DateField()
    achieved_date = models.DateField(null=True, blank=True)
    achieved = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'project_milestones'
        ordering = ['target_date']
        indexes = [
            models.Index(fields=['project', 'achieved']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.project.name}"