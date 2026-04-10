# core/serializers.py
# FARMWISE - REST API Serializers for Mobile App Integration

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import *

User = get_user_model()


# ============================================================
# SECTION 1: USER SERIALIZERS
# ============================================================

class UserSerializer(serializers.ModelSerializer):
    """Basic user serializer"""
    
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone_number', 'first_name', 'last_name', 
                  'full_name', 'user_type', 'profile_picture', 'is_verified', 'date_joined']
        read_only_fields = ['id', 'date_joined', 'is_verified']
    
    def get_full_name(self, obj):
        return obj.get_full_name()


class UserRegisterSerializer(serializers.ModelSerializer):
    """User registration serializer"""
    
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'phone_number', 'password', 'password2', 
                  'first_name', 'last_name', 'user_type']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """User profile serializer"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone_number', 'first_name', 'last_name', 
                  'profile_picture', 'preferred_language', 'accepts_sms', 'accepts_email',
                  'farm_name', 'location_lat', 'location_lng']


# ============================================================
# SECTION 2: FARM & FIELD SERIALIZERS
# ============================================================

class FarmListSerializer(serializers.ModelSerializer):
    """Farm list serializer (lightweight)"""
    
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    
    class Meta:
        model = Farm
        fields = ['id', 'name', 'owner_name', 'total_area_hectares', 'farm_type', 
                  'status', 'is_verified', 'created_at']


class FarmDetailSerializer(serializers.ModelSerializer):
    """Farm detail serializer (full)"""
    
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    cooperative_name = serializers.CharField(source='cooperative.name', read_only=True)
    
    class Meta:
        model = Farm
        fields = '__all__'
        read_only_fields = ['id', 'registration_number', 'created_at', 'updated_at']


class FieldSerializer(serializers.ModelSerializer):
    """Field serializer"""
    
    farm_name = serializers.CharField(source='farm.name', read_only=True)
    
    class Meta:
        model = Field
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


# ============================================================
# SECTION 3: CROP MANAGEMENT SERIALIZERS
# ============================================================

class CropTypeSerializer(serializers.ModelSerializer):
    """Crop type serializer"""
    
    class Meta:
        model = CropType
        fields = '__all__'


class CropSeasonListSerializer(serializers.ModelSerializer):
    """Crop season list serializer"""
    
    crop_name = serializers.CharField(source='crop_type.name', read_only=True)
    field_name = serializers.CharField(source='field.name', read_only=True)
    farm_name = serializers.CharField(source='field.farm.name', read_only=True)
    
    class Meta:
        model = CropSeason
        fields = ['id', 'crop_name', 'field_name', 'farm_name', 'planting_date', 
                  'expected_harvest_date', 'status', 'actual_yield_kg']


class CropSeasonDetailSerializer(serializers.ModelSerializer):
    """Crop season detail serializer"""
    
    crop_type_detail = CropTypeSerializer(source='crop_type', read_only=True)
    field_detail = FieldSerializer(source='field', read_only=True)
    
    class Meta:
        model = CropSeason
        fields = '__all__'


class InputApplicationSerializer(serializers.ModelSerializer):
    """Input application serializer"""
    
    total_cost = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    
    class Meta:
        model = InputApplication
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'total_cost']


class HarvestSerializer(serializers.ModelSerializer):
    """Harvest serializer"""
    
    total_revenue_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Harvest
        fields = '__all__'
        read_only_fields = ['id', 'created_at']
    
    def get_total_revenue_display(self, obj):
        return f"${obj.total_revenue}" if obj.total_revenue else None


# ============================================================
# SECTION 4: LIVESTOCK SERIALIZERS
# ============================================================

class AnimalTypeSerializer(serializers.ModelSerializer):
    """Animal type serializer"""
    
    species_display = serializers.CharField(source='get_species_display', read_only=True)
    
    class Meta:
        model = AnimalType
        fields = '__all__'


class AnimalListSerializer(serializers.ModelSerializer):
    """Animal list serializer"""
    
    species = serializers.CharField(source='animal_type.species', read_only=True)
    breed = serializers.CharField(source='animal_type.breed', read_only=True)
    farm_name = serializers.CharField(source='farm.name', read_only=True)
    age_months = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Animal
        fields = ['id', 'tag_number', 'name', 'species', 'breed', 'farm_name', 
                  'gender', 'age_months', 'status', 'weight_kg']


class AnimalDetailSerializer(serializers.ModelSerializer):
    """Animal detail serializer"""
    
    animal_type_detail = AnimalTypeSerializer(source='animal_type', read_only=True)
    farm_name = serializers.CharField(source='farm.name', read_only=True)
    age_months = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Animal
        fields = '__all__'


class HealthRecordSerializer(serializers.ModelSerializer):
    """Health record serializer"""
    
    record_type_display = serializers.CharField(source='get_record_type_display', read_only=True)
    animal_tag = serializers.CharField(source='animal.tag_number', read_only=True)
    
    class Meta:
        model = HealthRecord
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class MilkProductionSerializer(serializers.ModelSerializer):
    """Milk production serializer"""
    
    animal_tag = serializers.CharField(source='animal.tag_number', read_only=True)
    
    class Meta:
        model = MilkProduction
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'total_kg']


# ============================================================
# SECTION 5: EQUIPMENT RENTAL SERIALIZERS
# ============================================================

class EquipmentListSerializer(serializers.ModelSerializer):
    """Equipment list serializer"""
    
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    
    class Meta:
        model = Equipment
        fields = ['id', 'name', 'category', 'category_display', 'daily_rate', 
                  'location', 'status', 'owner_name', 'images']


class EquipmentDetailSerializer(serializers.ModelSerializer):
    """Equipment detail serializer"""
    
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    owner_phone = serializers.CharField(source='owner.phone_number', read_only=True)
    
    class Meta:
        model = Equipment
        fields = '__all__'


class EquipmentBookingSerializer(serializers.ModelSerializer):
    """Equipment booking serializer"""
    
    equipment_name = serializers.CharField(source='equipment.name', read_only=True)
    renter_name = serializers.CharField(source='renter.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = EquipmentBooking
        fields = '__all__'
        read_only_fields = ['id', 'total_days', 'total_cost', 'created_at', 'updated_at']


class EquipmentBookingCreateSerializer(serializers.ModelSerializer):
    """Create equipment booking serializer"""
    
    class Meta:
        model = EquipmentBooking
        fields = ['equipment', 'start_date', 'end_date', 'pickup_location', 'renter_notes']


# ============================================================
# SECTION 6: MARKETPLACE SERIALIZERS
# ============================================================

class ProductListingListSerializer(serializers.ModelSerializer):
    """Product listing list serializer"""
    
    seller_name = serializers.CharField(source='seller.name', read_only=True)
    
    class Meta:
        model = ProductListing
        fields = ['id', 'product_name', 'category', 'quantity', 'unit', 
                  'price_per_unit', 'total_price', 'seller_name', 'images', 
                  'is_organic', 'created_at']


class ProductListingDetailSerializer(serializers.ModelSerializer):
    """Product listing detail serializer"""
    
    seller_name = serializers.CharField(source='seller.name', read_only=True)
    seller_phone = serializers.CharField(source='seller.owner.phone_number', read_only=True)
    
    class Meta:
        model = ProductListing
        fields = '__all__'


class OrderSerializer(serializers.ModelSerializer):
    """Order serializer"""
    
    product_name = serializers.CharField(source='listing.product_name', read_only=True)
    buyer_name = serializers.CharField(source='buyer.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['id', 'subtotal', 'total_amount', 'created_at', 'updated_at']


# ============================================================
# SECTION 7: PEST DETECTION SERIALIZERS
# ============================================================

class PestReportSerializer(serializers.ModelSerializer):
    """Pest report serializer"""
    
    farmer_name = serializers.CharField(source='farmer.get_full_name', read_only=True)
    farm_name = serializers.CharField(source='farm.name', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    
    class Meta:
        model = PestReport
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class PestReportCreateSerializer(serializers.ModelSerializer):
    """Create pest report serializer"""
    
    class Meta:
        model = PestReport
        fields = ['farm', 'field', 'crop', 'image', 'notes']


# ============================================================
# SECTION 8: WEATHER & IRRIGATION SERIALIZERS
# ============================================================

class WeatherAlertSerializer(serializers.ModelSerializer):
    """Weather alert serializer"""
    
    farm_name = serializers.CharField(source='farm.name', read_only=True)
    alert_type_display = serializers.CharField(source='get_alert_type_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    
    class Meta:
        model = WeatherAlert
        fields = '__all__'


class IrrigationScheduleSerializer(serializers.ModelSerializer):
    """Irrigation schedule serializer"""
    
    field_name = serializers.CharField(source='field.name', read_only=True)
    farm_name = serializers.CharField(source='field.farm.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = IrrigationSchedule
        fields = '__all__'


# ============================================================
# SECTION 9: INSURANCE SERIALIZERS
# ============================================================

class InsurancePolicySerializer(serializers.ModelSerializer):
    """Insurance policy serializer"""
    
    farmer_name = serializers.CharField(source='farmer.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = InsurancePolicy
        fields = '__all__'
        read_only_fields = ['id', 'policy_number', 'created_at', 'updated_at']


class InsuranceClaimSerializer(serializers.ModelSerializer):
    """Insurance claim serializer"""
    
    policy_number = serializers.CharField(source='policy.policy_number', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = InsuranceClaim
        fields = '__all__'
        read_only_fields = ['id', 'claim_date', 'created_at', 'updated_at']


# ============================================================
# SECTION 10: LABOR SERIALIZERS
# ============================================================

class WorkerSerializer(serializers.ModelSerializer):
    """Worker serializer"""
    
    worker_name = serializers.CharField(source='worker.get_full_name', read_only=True)
    farm_name = serializers.CharField(source='farm.name', read_only=True)
    
    class Meta:
        model = Worker
        fields = '__all__'


class WorkShiftSerializer(serializers.ModelSerializer):
    """Work shift serializer"""
    
    worker_name = serializers.CharField(source='worker.worker.get_full_name', read_only=True)
    task_display = serializers.CharField(source='get_task_display', read_only=True)
    field_name = serializers.CharField(source='field.name', read_only=True)
    
    class Meta:
        model = WorkShift
        fields = '__all__'
        read_only_fields = ['id', 'total_pay', 'created_at']


class PayrollSerializer(serializers.ModelSerializer):
    """Payroll serializer"""
    
    worker_name = serializers.CharField(source='worker.worker.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Payroll
        fields = '__all__'


# ============================================================
# SECTION 11: FINANCIAL SERIALIZERS
# ============================================================

class TransactionSerializer(serializers.ModelSerializer):
    """Transaction serializer"""
    
    farm_name = serializers.CharField(source='farm.name', read_only=True)
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    
    class Meta:
        model = Transaction
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


# ============================================================
# SECTION 12: NOTIFICATION SERIALIZER
# ============================================================

class NotificationSerializer(serializers.ModelSerializer):
    """Notification serializer"""
    
    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


# ============================================================
# SECTION 13: DASHBOARD STATS SERIALIZER
# ============================================================

class DashboardStatsSerializer(serializers.Serializer):
    """Dashboard statistics serializer"""
    
    total_farms = serializers.IntegerField()
    total_fields = serializers.IntegerField()
    active_crops = serializers.IntegerField()
    total_livestock = serializers.IntegerField()
    pending_alerts = serializers.IntegerField()
    monthly_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    monthly_expenses = serializers.DecimalField(max_digits=12, decimal_places=2)
    monthly_profit = serializers.DecimalField(max_digits=12, decimal_places=2)


# ============================================================
# SECTION 14: VALIDATION & ACTIVITY SERIALIZERS
# ============================================================

class ValidationRuleSerializer(serializers.ModelSerializer):
    """Validation rule serializer"""
    
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    
    class Meta:
        model = ValidationRule
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class ValidationLogSerializer(serializers.ModelSerializer):
    """Validation log serializer"""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    source_display = serializers.CharField(source='get_form_or_api_display', read_only=True)
    
    class Meta:
        model = ValidationLog
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class UserHistorySerializer(serializers.ModelSerializer):
    """User history serializer"""
    
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = UserHistory
        fields = '__all__'
        read_only_fields = ['id', 'first_used', 'last_used']


class FarmHistorySerializer(serializers.ModelSerializer):
    """Farm history serializer"""
    
    farm_name = serializers.CharField(source='farm.name', read_only=True)
    
    class Meta:
        model = FarmHistory
        fields = '__all__'
        read_only_fields = ['id', 'first_used', 'last_used']


class ActivityLogSerializer(serializers.ModelSerializer):
    """Activity log serializer for timeline"""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    farm_name = serializers.CharField(read_only=True)
    icon = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    
    class Meta:
        model = AuditLog
        fields = ['id', 'timestamp', 'user_name', 'farm_name', 'icon', 'title', 
                  'description', 'severity', 'model_name', 'details', 'created_at']
        read_only_fields = ['id', 'created_at', 'timestamp']
    
    def get_icon(self, obj):
        return obj.details.get('icon', '📋') if obj.details else '📋'
    
    def get_title(self, obj):
        return obj.details.get('title', obj.model_name) if obj.details else obj.model_name
    
    def get_description(self, obj):
        return obj.details.get('description', '') if obj.details else ''


# ============================================================
# FEATURE 10: FARMER NETWORK & KNOWLEDGE SHARING SERIALIZERS
# ============================================================

class DiscussionForumSerializer(serializers.ModelSerializer):
    thread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = DiscussionForum
        fields = ['id', 'title', 'description', 'category', 'is_moderated', 'is_active', 
                  'member_count', 'post_count', 'thread_count', 'created_at', 'updated_at']
    
    def get_thread_count(self, obj):
        return obj.threads.count()


class ForumThreadSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source='author.username', read_only=True)
    reply_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ForumThread
        fields = ['id', 'forum', 'author', 'author_username', 'title', 'content', 'is_pinned', 
                  'is_closed', 'view_count', 'reply_count', 'tags', 'created_at', 'updated_at']
    
    def get_reply_count(self, obj):
        return obj.replies.count()


class ForumReplySerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source='author.username', read_only=True)
    
    class Meta:
        model = ForumReply
        fields = ['id', 'thread', 'author', 'author_username', 'content', 'attachments', 
                  'is_helpful', 'helpful_count', 'created_at', 'updated_at']


class GroupBuyingInitiativeSerializer(serializers.ModelSerializer):
    participant_count = serializers.SerializerMethodField()
    
    class Meta:
        model = GroupBuyingInitiative
        fields = ['id', 'title', 'description', 'product_type', 'minimum_order_quantity', 
                  'quantity_unit', 'unit_price_without_group', 'unit_price_with_group', 
                  'discount_percent', 'start_date', 'end_date', 'delivery_date', 'organizer', 
                  'organizer_contact', 'farmers_joined', 'total_quantity_pledged', 
                  'participant_count', 'status', 'created_at']
    
    def get_participant_count(self, obj):
        return obj.participants.count()


class GroupBuyingParticipantSerializer(serializers.ModelSerializer):
    farmer_username = serializers.CharField(source='farmer.username', read_only=True)
    
    class Meta:
        model = GroupBuyingParticipant
        fields = ['id', 'initiative', 'farmer', 'farmer_username', 'quantity_pledged', 
                  'quantity_received', 'payment_status', 'amount_paid', 'joined_at']


# ============================================================
# FEATURE 11: CARBON FOOTPRINT TRACKER SERIALIZERS
# ============================================================

class EmissionSourceSerializer(serializers.ModelSerializer):
    farm_name = serializers.CharField(source='farm.name', read_only=True)
    
    class Meta:
        model = EmissionSource
        fields = ['id', 'farm', 'farm_name', 'source_type', 'name', 'emission_factor', 
                  'unit', 'is_active', 'created_at']


class EmissionRecordSerializer(serializers.ModelSerializer):
    farm_name = serializers.CharField(source='farm.name', read_only=True)
    source_name = serializers.CharField(source='source.name', read_only=True)
    
    class Meta:
        model = EmissionRecord
        fields = ['id', 'farm', 'farm_name', 'source', 'source_name', 'record_date', 
                  'quantity_used', 'calculated_emissions_kg_co2e', 'description', 'created_at']


class CarbonSequestrationSerializer(serializers.ModelSerializer):
    farm_name = serializers.CharField(source='farm.name', read_only=True)
    
    class Meta:
        model = CarbonSequestration
        fields = ['id', 'farm', 'farm_name', 'activity_type', 'name', 'description', 
                  'area_hectares', 'tree_count', 'annual_sequestration_kg_co2e', 
                  'start_date', 'end_date', 'created_at']


class CarbonFootprintReportSerializer(serializers.ModelSerializer):
    farm_name = serializers.CharField(source='farm.name', read_only=True)
    
    class Meta:
        model = CarbonFootprintReport
        fields = ['id', 'farm', 'farm_name', 'report_period', 'year', 'month', 
                  'total_emissions_kg_co2e', 'total_sequestration_kg_co2e', 
                  'net_carbon_footprint_kg_co2e', 'emissions_per_hectare', 
                  'emission_breakdown', 'is_carbon_neutral', 'offset_needed_kg_co2e', 
                  'recommendations', 'created_at']


# ============================================================
# FEATURE 12: FARM MAPPING & GEOFENCING SERIALIZERS
# ============================================================

class FarmBoundarySerializer(serializers.ModelSerializer):
    farm_name = serializers.CharField(source='farm.name', read_only=True)
    
    class Meta:
        model = FarmBoundary
        fields = ['id', 'farm', 'farm_name', 'geojson_boundary', 'total_area_hectares', 
                  'center_latitude', 'center_longitude', 'is_verified', 'created_at', 'updated_at']


class GeofenceSerializer(serializers.ModelSerializer):
    farm_name = serializers.CharField(source='farm.name', read_only=True)
    field_name = serializers.CharField(source='field.name', read_only=True)
    livestock_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Geofence
        fields = ['id', 'farm', 'farm_name', 'field', 'field_name', 'name', 
                  'geojson_boundary', 'enable_exit_alerts', 'enable_entry_alerts', 
                  'alert_channels', 'livestock_count', 'is_active', 'created_at']
    
    def get_livestock_count(self, obj):
        return obj.assigned_livestock.count()


class LivestockLocationSerializer(serializers.ModelSerializer):
    livestock_name = serializers.CharField(source='livestock.name', read_only=True)
    
    class Meta:
        model = LivestockLocation
        fields = ['id', 'livestock', 'livestock_name', 'latitude', 'longitude', 
                  'accuracy_meters', 'device_id', 'signal_strength', 
                  'is_inside_assigned_geofence', 'recorded_at', 'created_at']


class GeofenceAlertSerializer(serializers.ModelSerializer):
    geofence_name = serializers.CharField(source='geofence.name', read_only=True)
    livestock_name = serializers.CharField(source='livestock.name', read_only=True)
    resolved_by_username = serializers.CharField(source='resolved_by.username', read_only=True)
    
    class Meta:
        model = GeofenceAlert
        fields = ['id', 'geofence', 'geofence_name', 'livestock', 'livestock_name', 
                  'alert_type', 'latitude', 'longitude', 'is_resolved', 'resolved_by', 
                  'resolved_by_username', 'resolved_at', 'resolution_notes', 'alert_time', 'created_at']


# ============================================================
# FEATURE 13: OFFLINE SYNC & DATA MANAGEMENT SERIALIZERS
# ============================================================

class OfflineSyncQueueSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = OfflineSyncQueue
        fields = ['id', 'user', 'user_username', 'model_name', 'operation', 'object_id', 
                  'data_payload', 'is_synced', 'sync_error', 'sync_attempted_at', 
                  'created_at', 'updated_at']


class SyncConflictSerializer(serializers.ModelSerializer):
    sync_entry_id = serializers.IntegerField(source='sync_entry.id', read_only=True)
    
    class Meta:
        model = SyncConflict
        fields = ['id', 'sync_entry', 'sync_entry_id', 'server_version', 'local_version', 
                  'conflicting_fields', 'resolution_status', 'resolved_data', 
                  'resolved_by', 'created_at']


# ============================================================
# FEATURE 14: WEATHER ENHANCEMENT SERIALIZERS
# ============================================================

class WeatherForecastSerializer(serializers.ModelSerializer):
    farm_name = serializers.CharField(source='farm.name', read_only=True)
    
    class Meta:
        model = WeatherForecast
        fields = ['id', 'farm', 'farm_name', 'latitude', 'longitude', 'forecast_date', 
                  'forecast_time', 'recorded_at', 'temperature_celsius', 'feels_like_celsius', 
                  'min_temp_celsius', 'max_temp_celsius', 'humidity_percent', 'pressure_hpa', 
                  'wind_speed_kmh', 'wind_direction_degrees', 'wind_gust_kmh', 'rainfall_mm', 
                  'rainfall_probability_percent', 'cloud_coverage_percent', 'visibility_km', 
                  'uv_index', 'weather_condition', 'description', 'gdd', 'farming_recommendation', 'created_at']


class WeatherAlertSerializer(serializers.ModelSerializer):
    farm_name = serializers.CharField(source='farm.name', read_only=True)
    acknowledged_by_username = serializers.CharField(source='acknowledged_by.username', read_only=True)
    
    class Meta:
        model = WeatherAlert
        fields = ['id', 'farm', 'farm_name', 'alert_type', 'severity', 'alert_issued_at', 
                  'alert_effective_from', 'alert_expires_at', 'description', 'recommended_actions', 
                  'is_acknowledged', 'acknowledged_by', 'acknowledged_by_username', 'acknowledged_at', 
                  'response_actions', 'created_at']