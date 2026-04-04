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
    profile_picture = models.ImageField(upload_to='profiles/%Y/%m/', null=True, blank=True)
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
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    action = models.CharField(max_length=20, choices=ACTIONS)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100)
    details = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'audit_logs'
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['model_name', 'object_id']),
        ]
    
    def __str__(self):
        return f"{self.user} - {self.action} - {self.model_name} at {self.created_at}"


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
        ('planted', 'Planted'),
        ('growing', 'Growing'),
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
    images = models.FileField(upload_to='marketplace/products/', null=True, blank=True)
    harvest_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    is_organic = models.BooleanField(default=False)
    delivery_available = models.BooleanField(default=False)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'product_listings'
        indexes = [
            models.Index(fields=['seller', 'status']),
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
    confidence = models.DecimalField(max_digits=5, decimal_places=2)
    severity = models.CharField(max_length=20, choices=SEVERITY)
    affected_area_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    treatment_recommended = models.TextField(blank=True)
    prevention_tips = models.TextField(blank=True)
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
    skills = models.JSONField(default=list, blank=True)
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