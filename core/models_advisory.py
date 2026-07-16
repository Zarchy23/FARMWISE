"""
Farmer Advisory System Models
Provides comprehensive guidance for land preparation, pest management, and livestock care
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class FarmProfile(models.Model):
    """Comprehensive farm profile for context-specific advisory"""
    
    FARM_TYPES = [
        ('crop_oriented', 'Crop-Oriented Farm'),
        ('livestock_oriented', 'Livestock-Oriented Farm'),
        ('mixed_income', 'Mixed Farm with Off-Farm Income'),
        ('mixed_integrated', 'Integrated Mixed Farm'),
    ]
    
    AGRO_ECOLOGICAL_ZONES = [
        ('natural_region_1', 'Natural Region I - High rainfall'),
        ('natural_region_2a', 'Natural Region IIa - Moderate rainfall'),
        ('natural_region_2b', 'Natural Region IIb - Moderate rainfall'),
        ('natural_region_3', 'Natural Region III - Semi-arid'),
        ('natural_region_4', 'Natural Region IV - Arid'),
        ('natural_region_5', 'Natural Region V - Very arid'),
    ]
    
    LAND_PREPARATION_METHODS = [
        ('conventional_ploughing', 'Conventional Ploughing'),
        ('minimum_tillage', 'Minimum Tillage'),
        ('conservation_tillage', 'Conservation Tillage'),
        ('oxen_drawn', 'Oxen-Drawn Plow'),
        ('hand_hoe', 'Hand Hoe'),
        ('mechanized', 'Mechanized/Tractor'),
        ('pfumvudza', 'Pfumvudza/Conservation Agriculture'),
        ('intwasa', 'Intwasa Water Conservation'),
    ]
    
    user = models.OneToOneField('core.User', on_delete=models.CASCADE, related_name='farm_profile')
    farm_name = models.CharField(max_length=200)
    farm_type = models.CharField(max_length=30, choices=FARM_TYPES, default='mixed_integrated')
    
    # Location and context
    location = models.CharField(max_length=200, help_text="District/Province")
    agro_ecological_zone = models.CharField(max_length=30, choices=AGRO_ECOLOGICAL_ZONES)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Land resources
    total_land_area_hectares = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    arable_land_hectares = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    
    # Land preparation preferences
    primary_land_preparation_method = models.CharField(max_length=30, choices=LAND_PREPARATION_METHODS)
    labor_availability = models.CharField(max_length=100, help_text="Describe available labor (family, hired, etc.)")
    equipment_inventory = models.TextField(help_text="List available equipment (tractors, plows, sprayers, etc.)")
    
    # Soil information
    soil_type = models.CharField(max_length=100, help_text="e.g., Sandy loam, Clay, Red soil")
    soil_ph = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True, help_text="Soil pH level")
    
    # Water access
    water_source = models.CharField(max_length=100, help_text="e.g., Borehole, River, Dam")
    irrigation_access = models.BooleanField(default=False)
    
    # Additional context
    farming_experience_years = models.IntegerField(validators=[MinValueValidator(0)], help_text="Years of farming experience")
    primary_crops = models.TextField(help_text="List primary crops grown")
    livestock_types = models.TextField(help_text="List livestock types and approximate numbers")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.farm_name} - {self.user.username}"
    
    class Meta:
        verbose_name = "Farm Profile"
        verbose_name_plural = "Farm Profiles"


class LandPreparationGuide(models.Model):
    """Context-specific land preparation guidance"""
    
    CROP_TYPES = [
        ('maize', 'Maize'),
        ('tobacco', 'Tobacco'),
        ('cotton', 'Cotton'),
        ('wheat', 'Wheat'),
        ('sorghum', 'Sorghum'),
        ('millet', 'Millet'),
        ('vegetables', 'Vegetables'),
        ('sugarcane', 'Sugarcane'),
        ('soybeans', 'Soybeans'),
        ('groundnuts', 'Groundnuts'),
    ]
    
    SOIL_TYPES = [
        ('sandy', 'Sandy Soil'),
        ('loamy', 'Loamy Soil'),
        ('clay', 'Clay Soil'),
        ('sandy_loam', 'Sandy Loam'),
        ('clay_loam', 'Clay Loam'),
    ]
    
    title = models.CharField(max_length=200)
    crop_type = models.CharField(max_length=30, choices=CROP_TYPES)
    soil_type = models.CharField(max_length=30, choices=SOIL_TYPES)
    agro_ecological_zone = models.CharField(max_length=30, choices=FarmProfile.AGRO_ECOLOGICAL_ZONES)
    
    # Guidance content
    preparation_method = models.CharField(max_length=30, choices=FarmProfile.LAND_PREPARATION_METHODS)
    rainfall_requirement_mm = models.IntegerField(help_text="Minimum rainfall requirement in mm")
    consecutive_rainy_days = models.IntegerField(default=3, help_text="Consecutive rainy days needed")
    
    # Detailed guidance
    step_by_step_guide = models.TextField(help_text="Detailed step-by-step preparation instructions")
    timing_recommendations = models.TextField(help_text="When to start preparation based on weather patterns")
    manure_application_rate = models.CharField(max_length=100, help_text="e.g., 5 tonnes per hectare")
    fertilizer_recommendations = models.TextField(help_text="Basal and top dressing fertilizer recommendations")
    
    # Water conservation
    water_conservation_technique = models.CharField(max_length=100, blank=True, help_text="e.g., Pfumvudza, mulching")
    water_conservation_instructions = models.TextField(blank=True)
    
    # Risk factors
    common_challenges = models.TextField(help_text="Common challenges and solutions")
    pest_prevention_measures = models.TextField(help_text="Pre-planting pest prevention measures")
    
    # Seasonal alerts
    optimal_planting_window_start = models.DateField(help_text="Start of optimal planting window")
    optimal_planting_window_end = models.DateField(help_text="End of optimal planting window")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.title} - {self.crop_type}"
    
    class Meta:
        verbose_name = "Land Preparation Guide"
        verbose_name_plural = "Land Preparation Guides"
        ordering = ['crop_type', 'agro_ecological_zone']


class PestManagementGuide(models.Model):
    """Integrated Pest Management (IPM) guidance"""
    
    PEST_SEVERITY = [
        ('low', 'Low - Monitor only'),
        ('medium', 'Medium - Cultural controls'),
        ('high', 'High - Chemical intervention needed'),
        ('severe', 'Severe - Immediate action required'),
    ]
    
    CONTROL_METHODS = [
        ('cultural', 'Cultural Control'),
        ('biological', 'Biological Control'),
        ('chemical', 'Chemical Control'),
        ('mechanical', 'Mechanical Control'),
        ('integrated', 'Integrated Pest Management'),
    ]
    
    pest_name = models.CharField(max_length=200)
    scientific_name = models.CharField(max_length=200, blank=True)
    affected_crops = models.TextField(help_text="List of affected crops")
    
    # Pest identification
    description = models.TextField(help_text="Physical description for identification")
    damage_symptoms = models.TextField(help_text="Symptoms of pest damage")
    life_cycle = models.TextField(help_text="Life cycle and timing")
    
    # IPM approach
    primary_control_method = models.CharField(max_length=30, choices=CONTROL_METHODS, default='integrated')
    severity_threshold = models.CharField(max_length=30, choices=PEST_SEVERITY)
    
    # Cultural controls (non-chemical)
    cultural_controls = models.TextField(help_text="Non-chemical prevention methods")
    intercropping_recommendations = models.TextField(blank=True, help_text="Effective intercropping combinations")
    crop_rotation_suggestions = models.TextField(blank=True)
    sanitation_practices = models.TextField(blank=True, help_text="Field sanitation and hygiene")
    
    # Biological controls
    biological_controls = models.TextField(blank=True, help_text="Natural predators and biological agents")
    beneficial_insects = models.TextField(blank=True, help_text="Insects that attract beneficial species")
    pheromone_traps = models.TextField(blank=True, help_text="Pheromone trap usage instructions")
    
    # Chemical controls (last resort)
    chemical_controls = models.TextField(blank=True, help_text="Chemical options only when necessary")
    pesticide_recommendations = models.ManyToManyField('PesticideInfo', blank=True, related_name='pest_guides')
    application_timing = models.TextField(blank=True, help_text="When to apply if chemicals are needed")
    
    # Monitoring
    monitoring_frequency = models.CharField(max_length=100, help_text="How often to monitor for this pest")
    scouting_methods = models.TextField(help_text="How to scout and identify infestation levels")
    action_threshold = models.TextField(help_text="When to take action based on pest numbers")
    
    # Regional effectiveness
    regional_notes = models.TextField(blank=True, help_text="Effectiveness variations by region/climate")
    climate_factors = models.TextField(blank=True, help_text="Climate conditions that affect pest prevalence")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.pest_name} - {self.affected_crops}"
    
    class Meta:
        verbose_name = "Pest Management Guide"
        verbose_name_plural = "Pest Management Guides"
        ordering = ['pest_name']


class PesticideInfo(models.Model):
    """Comprehensive pesticide information database"""
    
    APPLICATION_METHODS = [
        ('spray', 'Spray'),
        ('dust', 'Dust'),
        ('granular', 'Granular'),
        ('seed_treatment', 'Seed Treatment'),
        ('soil_drench', 'Soil Drench'),
    ]
    
    TOXICITY_CLASS = [
        ('class_ia', 'Class Ia - Extremely Hazardous'),
        ('class_ib', 'Class Ib - Highly Hazardous'),
        ('class_ii', 'Class II - Moderately Hazardous'),
        ('class_iii', 'Class III - Slightly Hazardous'),
        ('class_u', 'Class U - Unlikely to present acute hazard'),
    ]
    
    product_name = models.CharField(max_length=200)
    active_ingredient = models.CharField(max_length=200)
    manufacturer = models.CharField(max_length=200)
    
    # Application details
    application_method = models.CharField(max_length=30, choices=APPLICATION_METHODS)
    recommended_rate_per_hectare = models.CharField(max_length=100, help_text="e.g., 0.4L/ha")
    concentration = models.CharField(max_length=100, help_text="Active ingredient concentration")
    
    # Target information
    target_pests = models.TextField(help_text="Pests this pesticide controls")
    compatible_crops = models.TextField(help_text="Crops this can be used on")
    
    # Safety information
    toxicity_class = models.CharField(max_length=30, choices=TOXICITY_CLASS)
    pre_harvest_interval_days = models.IntegerField(help_text="Days between last application and harvest")
    re_entry_interval_hours = models.IntegerField(help_text="Hours before re-entering treated field")
    
    # Safety warnings
    safety_precautions = models.TextField(help_text="Personal protective equipment and handling precautions")
    environmental_concerns = models.TextField(blank=True, help_text="Environmental impact and precautions")
    first_aid_measures = models.TextField(help_text="First aid in case of exposure")
    
    # Storage and disposal
    storage_requirements = models.TextField(help_text="Proper storage conditions")
    disposal_instructions = models.TextField(help_text="Safe disposal methods")
    
    # Resistance management
    resistance_management = models.TextField(blank=True, help_text="Strategies to prevent pest resistance")
    max_applications_per_season = models.IntegerField(default=3, help_text="Maximum applications per season")
    
    # Regional effectiveness
    regional_effectiveness = models.TextField(blank=True, help_text="Effectiveness variations by region")
    climate_limitations = models.TextField(blank=True, help_text="Climate conditions affecting effectiveness")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.product_name} ({self.active_ingredient})"
    
    class Meta:
        verbose_name = "Pesticide Information"
        verbose_name_plural = "Pesticide Information"
        ordering = ['product_name']


class PesticideDosageCalculator(models.Model):
    """Sprayer-specific dosage calculations"""
    
    SPRAYER_TYPES = [
        ('knapsack_16l', 'Knapsack Sprayer 16L'),
        ('knapsack_18l', 'Knapsack Sprayer 18L'),
        ('knapsack_20l', 'Knapsack Sprayer 20L'),
        ('motorized_pump', 'Motorized Pump'),
        ('tractor_mounted', 'Tractor-Mounted Sprayer'),
        ('drone_sprayer', 'Drone Sprayer'),
    ]
    
    sprayer_type = models.CharField(max_length=30, choices=SPRAYER_TYPES)
    capacity_liters = models.DecimalField(max_digits=5, decimal_places=1)
    coverage_per_tank_hectares = models.DecimalField(max_digits=5, decimal_places=3, help_text="Hectares covered per full tank")
    
    # Calibration data
    nozzle_type = models.CharField(max_length=100)
    pressure_psi = models.IntegerField(help_text="Operating pressure in PSI")
    flow_rate_liters_per_minute = models.DecimalField(max_digits=5, decimal_places=2)
    
    # Usage factors
    walking_speed_meters_per_minute = models.DecimalField(max_digits=6, decimal_places=2, help_text="For knapsack sprayers")
    spray_width_meters = models.DecimalField(max_digits=4, decimal_places=2, help_text="Spray swath width")
    
    # Efficiency factors
    drone_efficiency_reduction = models.DecimalField(max_digits=3, decimal_places=1, default=25.0, 
                                                      help_text="Percentage dosage reduction for drone sprayers")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def calculate_dosage(self, pesticide_rate_per_hectare, field_area_hectares):
        """Calculate pesticide and water requirements"""
        total_pesticide_ml = float(pesticide_rate_per_hectare) * float(field_area_hectares) * 1000
        total_water_liters = float(field_area_hectares) / float(self.coverage_per_tank_hectares) * float(self.capacity_liters)
        number_of_tanks = float(total_water_liters) / float(self.capacity_liters)
        
        return {
            'total_pesticide_ml': total_pesticide_ml,
            'total_water_liters': total_water_liters,
            'number_of_tanks': round(number_of_tanks, 1),
            'pesticide_per_tank_ml': total_pesticide_ml / number_of_tanks if number_of_tanks > 0 else 0
        }
    
    def __str__(self):
        return f"{self.sprayer_type} - {self.capacity_liters}L"
    
    class Meta:
        verbose_name = "Pesticide Dosage Calculator"
        verbose_name_plural = "Pesticide Dosage Calculators"


class VeterinaryDrug(models.Model):
    """Veterinary drug database with dosage information"""
    
    ANIMAL_SPECIES = [
        ('cattle', 'Cattle'),
        ('horses', 'Horses'),
        ('swine', 'Swine/Pigs'),
        ('sheep', 'Sheep'),
        ('goats', 'Goats'),
        ('poultry', 'Poultry'),
        ('dogs', 'Dogs'),
        ('cats', 'Cats'),
        ('rabbits', 'Rabbits'),
    ]
    
    ADMINISTRATION_ROUTES = [
        ('im', 'Intramuscular (IM)'),
        ('sc', 'Subcutaneous (SC)'),
        ('iv', 'Intravenous (IV)'),
        ('po', 'Oral (PO)'),
        ('topical', 'Topical'),
        ('intramammary', 'Intramammary'),
        ('intrauterine', 'Intrauterine'),
    ]
    
    DRUG_CLASS = [
        ('antibiotic', 'Antibiotic'),
        ('anti_inflammatory', 'Anti-inflammatory'),
        ('anthelmintic', 'Anthelmintic/Dewormer'),
        ('vitamin', 'Vitamin/Supplement'),
        ('hormone', 'Hormone'),
        ('sedative', 'Sedative/Anesthetic'),
        ('antiparasitic', 'Antiparasitic'),
        ('vaccine', 'Vaccine'),
    ]
    
    drug_name = models.CharField(max_length=200)
    generic_name = models.CharField(max_length=200)
    manufacturer = models.CharField(max_length=200)
    drug_class = models.CharField(max_length=30, choices=DRUG_CLASS)
    
    # Species-specific dosage
    species = models.CharField(max_length=30, choices=ANIMAL_SPECIES)
    min_dosage = models.DecimalField(max_digits=10, decimal_places=2, help_text="Minimum dosage")
    max_dosage = models.DecimalField(max_digits=10, decimal_places=2, help_text="Maximum dosage")
    dosage_unit = models.CharField(max_length=20, help_text="e.g., mg/kg, U/kg, mL/kg")
    
    # Administration details
    administration_route = models.CharField(max_length=30, choices=ADMINISTRATION_ROUTES)
    frequency = models.CharField(max_length=100, help_text="e.g., q 24 h, q 12 h, once daily")
    duration_days = models.IntegerField(null=True, blank=True, help_text="Treatment duration in days")
    
    # Safety and restrictions
    eldu_restricted = models.BooleanField(default=False, help_text="Extralabel Drug Use restricted")
    eldu_prohibited_food_animals = models.BooleanField(default=False, help_text="ELDU prohibited for food-producing animals")
    max_single_dose = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, 
                                           help_text="Maximum single dose")
    max_daily_dose = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                        help_text="Maximum daily dose")
    
    # Withdrawal periods
    meat_withdrawal_days = models.IntegerField(null=True, blank=True, help_text="Days before slaughter")
    milk_withdrawal_days = models.IntegerField(null=True, blank=True, help_text="Days before milk consumption")
    egg_withdrawal_days = models.IntegerField(null=True, blank=True, help_text="Days before egg consumption")
    
    # Contraindications and warnings
    contraindications = models.TextField(help_text="When NOT to use this drug")
    side_effects = models.TextField(help_text="Common side effects")
    drug_interactions = models.TextField(blank=True, help_text="Known drug interactions")
    pregnancy_warnings = models.TextField(blank=True, help_text="Use during pregnancy")
    
    # Storage and handling
    storage_requirements = models.TextField(help_text="Storage conditions")
    shelf_life_months = models.IntegerField(help_text="Shelf life in months")
    
    # Additional notes
    special_instructions = models.TextField(blank=True, help_text="Additional administration instructions")
    veterinary_consultation_required = models.BooleanField(default=True, 
                                                           help_text="Always consult veterinarian before use")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    def calculate_dose(self, animal_weight_kg):
        """Calculate dose based on animal weight"""
        # Use minimum dosage for calculation
        dose = float(self.min_dosage) * float(animal_weight_kg)
        return {
            'calculated_dose': dose,
            'unit': self.dosage_unit,
            'administration_route': self.administration_route,
            'frequency': self.frequency,
            'meat_withdrawal': self.meat_withdrawal_days,
            'milk_withdrawal': self.milk_withdrawal_days,
            'consult_veterinarian': self.veterinary_consultation_required
        }
    
    def __str__(self):
        return f"{self.drug_name} - {self.species}"
    
    class Meta:
        verbose_name = "Veterinary Drug"
        verbose_name_plural = "Veterinary Drugs"
        ordering = ['drug_name', 'species']


class AdvisoryRequest(models.Model):
    """Track farmer advisory requests and responses"""
    
    REQUEST_TYPES = [
        ('land_preparation', 'Land Preparation Guidance'),
        ('pest_management', 'Pest Management'),
        ('pesticide_dosage', 'Pesticide Dosage Calculation'),
        ('livestock_dosage', 'Livestock Dosage Guidance'),
        ('general_advisory', 'General Farm Advisory'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('needs_followup', 'Needs Follow-up'),
    ]
    
    user = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='advisory_requests')
    request_type = models.CharField(max_length=30, choices=REQUEST_TYPES)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    
    # Request details
    subject = models.CharField(max_length=200)
    description = models.TextField()
    
    # Context information
    crop_type = models.CharField(max_length=100, blank=True)
    animal_species = models.CharField(max_length=100, blank=True)
    field_area_hectares = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    animal_weight_kg = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    
    # Response
    ai_response = models.TextField(blank=True)
    expert_response = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    
    # Follow-up
    follow_up_required = models.BooleanField(default=False)
    follow_up_date = models.DateField(null=True, blank=True)
    follow_up_notes = models.TextField(blank=True)
    
    # Feedback
    user_satisfaction = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
    user_feedback = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.subject}"
    
    class Meta:
        verbose_name = "Advisory Request"
        verbose_name_plural = "Advisory Requests"
        ordering = ['-created_at']


class AdvisoryKnowledgeBase(models.Model):
    """Knowledge base for advisory system responses"""
    
    KNOWLEDGE_TYPES = [
        ('land_prep', 'Land Preparation'),
        ('pest_management', 'Pest Management'),
        ('livestock', 'Livestock Management'),
        ('pesticide_safety', 'Pesticide Safety'),
        ('veterinary', 'Veterinary Medicine'),
        ('general', 'General Agriculture'),
    ]
    
    title = models.CharField(max_length=200)
    knowledge_type = models.CharField(max_length=30, choices=KNOWLEDGE_TYPES)
    
    # Content
    question = models.TextField(help_text="Common question or problem")
    answer = models.TextField(help_text="Detailed answer or guidance")
    
    # Context
    relevant_crops = models.TextField(blank=True, help_text="Relevant crops for this knowledge")
    relevant_regions = models.TextField(blank=True, help_text="Relevant regions or agro-ecological zones")
    season = models.CharField(max_length=50, blank=True, help_text="Relevant season")
    
    # References
    source = models.CharField(max_length=200, blank=True, help_text="Source of information")
    last_verified = models.DateField(null=True, blank=True)
    
    # Usage tracking
    access_count = models.IntegerField(default=0)
    helpful_rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.title} - {self.knowledge_type}"
    
    class Meta:
        verbose_name = "Advisory Knowledge Base"
        verbose_name_plural = "Advisory Knowledge Base"
        ordering = ['knowledge_type', 'title']
