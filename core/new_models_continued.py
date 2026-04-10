# ============================================================
# CONTINUATION OF NEW MODELS - FEATURES 10-14
# ADD THIS TO END OF core/models.py
# ============================================================

from django.db import models
from django.contrib.auth.models import User

# Note: Farm, Field, Crop, Livestock, Equipment defined in core/models.py
# Use string references for ForeignKeys to avoid circular imports

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
    
    farm = models.ForeignKey('Farm', on_delete=models.CASCADE, related_name='emission_sources')
    
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
    
    farm = models.ForeignKey('Farm', on_delete=models.CASCADE, related_name='emission_records')
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
    
    farm = models.ForeignKey('Farm', on_delete=models.CASCADE, related_name='sequestration_activities')
    
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


class CarbonFootprintReport(models.Model):
    """Monthly/yearly carbon footprint summary"""
    
    farm = models.ForeignKey('Farm', on_delete=models.CASCADE, related_name='carbon_reports')
    
    # Period
    report_period = models.CharField(max_length=20, choices=[
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ])
    year = models.IntegerField()
    month = models.IntegerField(null=True, blank=True)
    
    # Totals
    total_emissions_kg_co2e = models.DecimalField(max_digits=15, decimal_places=2)
    total_sequestration_kg_co2e = models.DecimalField(max_digits=15, decimal_places=2)
    net_carbon_footprint_kg_co2e = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Per hectare
    emissions_per_hectare = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Breakdown
    emission_breakdown = models.JSONField(default=dict)
    
    # Carbon neutral status
    is_carbon_neutral = models.BooleanField(default=False)
    offset_needed_kg_co2e = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Recommendations
    recommendations = models.TextField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'carbon_footprint_reports'
        unique_together = [['farm', 'report_period', 'year', 'month']]
    
    def __str__(self):
        return f"{self.farm.name} - Carbon Report {self.year}"


# ============================================================
# FEATURE 12: FARM MAP & GEOFENCING
# ============================================================

class FarmBoundary(models.Model):
    """Farm physical boundaries"""
    
    farm = models.OneToOneField('Farm', on_delete=models.CASCADE, related_name='boundary')
    
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
    
    farm = models.ForeignKey('Farm', on_delete=models.CASCADE, related_name='geofences')
    
    name = models.CharField(max_length=255)
    
    # Boundary (GeoJSON)
    geojson_boundary = models.JSONField(help_text='GeoJSON polygon for geofence')
    
    # Alert settings
    enable_exit_alerts = models.BooleanField(default=True)
    enable_entry_alerts = models.BooleanField(default=False)
    alert_channels = models.JSONField(default=list)  # ['sms', 'email', 'push']
    
    # Associated field/pasture
    field = models.ForeignKey('Field', on_delete=models.SET_NULL, null=True, blank=True)
    assigned_livestock = models.ManyToManyField('Livestock', blank=True)
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'geofences'
    
    def __str__(self):
        return f"{self.farm.name} - {self.name}"


class LivestockLocation(models.Model):
    """Real-time livestock location tracking"""
    
    livestock = models.ForeignKey('Livestock', on_delete=models.CASCADE, related_name='location_history')
    
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
    livestock = models.ForeignKey('Livestock', on_delete=models.CASCADE)
    
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
    
    farm = models.ForeignKey('Farm', on_delete=models.CASCADE, related_name='weather_forecasts')
    
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


class WeatherAlert(models.Model):
    """Severe weather alerts"""
    
    ALERT_TYPES = [
        ('frost', 'Frost'),
        ('excessive_heat', 'Excessive Heat'),
        ('drought', 'Drought'),
        ('flood', 'Flood'),
        ('high_wind', 'High Wind'),
        ('hailstorm', 'Hailstorm'),
        ('storm', 'Storm'),
        ('extreme_humidity', 'Extreme Humidity'),
        ('other', 'Other'),
    ]
    
    farm = models.ForeignKey('Farm', on_delete=models.CASCADE, related_name='weather_alerts')
    
    alert_type = models.CharField(max_length=50, choices=ALERT_TYPES)
    severity = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ])
    
    # Alert details
    alert_issued_at = models.DateTimeField()
    alert_effective_from = models.DateTimeField()
    alert_expires_at = models.DateTimeField()
    
    description = models.TextField()
    recommended_actions = models.TextField()
    
    # Status
    is_acknowledged = models.BooleanField(default=False)
    acknowledged_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    
    response_actions = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'weather_alerts'
        indexes = [
            models.Index(fields=['farm', 'alert_effective_from']),
        ]
    
    def __str__(self):
        return f"{self.get_alert_type_display()} - {self.farm.name}"
