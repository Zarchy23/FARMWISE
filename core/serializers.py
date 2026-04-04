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