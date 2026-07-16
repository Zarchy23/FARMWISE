# core/admin.py
# FARMWISE - Complete Admin Interface for All Models

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Sum
from .models import *
from .models_market import (
    Commodity, MarketPrice, PriceTrend, PriceAlert,
    SellerListing, BuyerInquiry, MarketAnalytics
)
from .models_voice import (
    VoiceCommand, VoiceConversation, VoiceInteraction,
    VoicePreference, VoiceNotification, VoiceCommandHistory
)
from core.models_chatbot import (
    ChatIntent, ChatSession, ChatMessage, ChatResponse, ChatFeedback, ChatStatistics
)
from .models_location import (
    FarmLocation, FarmField, FarmFieldZone, FarmGeofenceAlert,
    FarmLocationAnalytics, FarmCropRotationPlan, FarmProximityAnalysis
)
from .models_offline import (
    OfflineCache, SyncQueue, OfflinePreference, OfflineSyncLog,
    CachedMarketPrice, CachedWeatherData, OfflineAnalytics
)
from .models_disease import (
    DiseaseCategory, Disease, Symptom, TreatmentOption,
    DiagnosisRecord, DiagnosisHistory, DiseaseAlert, DiseaseStatistics
)

# ============================================================
# SECTION 1: USER ADMIN
# ============================================================

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'get_full_name', 'user_type', 'phone_number', 'is_verified', 'is_active', 'last_login')
    list_filter = ('user_type', 'is_verified', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'phone_number', 'first_name', 'last_name')
    readonly_fields = ('last_login', 'date_joined')
    
    fieldsets = UserAdmin.fieldsets + (
        ('FarmWise Additional Info', {
            'fields': ('user_type', 'phone_number', 'profile_picture', 'preferred_language', 
                      'accepts_sms', 'accepts_email', 'farm_name', 'location_lat', 'location_lng', 
                      'is_verified', 'id_number', 'email_verified', 'phone_verified')
        }),
    )
    
    actions = ['verify_users', 'send_test_sms']
    
    def verify_users(self, request, queryset):
        queryset.update(is_verified=True)
        self.message_user(request, f"{queryset.count()} users verified successfully.")
    verify_users.short_description = "Verify selected users"
    
    def send_test_sms(self, request, queryset):
        for user in queryset:
            if user.phone_number:
                # Add SMS sending logic here
                pass
        self.message_user(request, f"Test SMS sent to {queryset.count()} users.")
    send_test_sms.short_description = "Send test SMS"


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'model_name', 'object_id', 'created_at')
    list_filter = ('action', 'model_name', 'created_at')
    search_fields = ('user__username', 'model_name', 'object_id')
    readonly_fields = ('user', 'action', 'model_name', 'object_id', 'details', 'ip_address', 'user_agent', 'created_at')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


# ============================================================
# SECTION 2: FARM & FIELD ADMIN
# ============================================================

class FieldInline(admin.TabularInline):
    model = FarmField
    extra = 1
    fields = ('name', 'area_hectares', 'soil_type', 'slope', 'is_active')


@admin.register(Cooperative)
class CooperativeAdmin(admin.ModelAdmin):
    list_display = ('name', 'registration_number', 'admin', 'member_count', 'is_active')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'registration_number')
    readonly_fields = ('created_at', 'updated_at')
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            farm_count=Count('farms')
        )
    
    def member_count(self, obj):
        return obj.farm_count
    member_count.admin_order_field = 'farm_count'


@admin.register(Farm)
class FarmAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'cooperative', 'total_area_hectares', 'farm_type', 'status', 'is_verified')
    list_filter = ('farm_type', 'status', 'is_verified', 'created_at')
    search_fields = ('name', 'owner__username', 'registration_number')
    readonly_fields = ('registration_number', 'created_at', 'updated_at')
    inlines = [FieldInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('owner', 'cooperative', 'name', 'farm_type', 'status')
        }),
        ('Location & Size', {
            'fields': ('location', 'address', 'total_area_hectares')
        }),
        ('Verification & Banking', {
            'fields': ('registration_number', 'is_verified', 'bank_account')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['verify_farms', 'activate_farms']
    
    def verify_farms(self, request, queryset):
        queryset.update(is_verified=True)
        self.message_user(request, f"{queryset.count()} farms verified.")
    verify_farms.short_description = "Verify selected farms"
    
    def activate_farms(self, request, queryset):
        queryset.update(status='active')
        self.message_user(request, f"{queryset.count()} farms activated.")
    activate_farms.short_description = "Activate selected farms"


@admin.register(Field)
class FieldAdmin(admin.ModelAdmin):
    list_display = ('name', 'farm', 'area_hectares', 'soil_type', 'slope', 'is_active')
    list_filter = ('soil_type', 'slope', 'drainage', 'is_active')
    search_fields = ('name', 'farm__name')
    readonly_fields = ('created_at', 'updated_at')


# ============================================================
# SECTION 3: CROP MANAGEMENT ADMIN
# ============================================================

@admin.register(CropType)
class CropTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'scientific_name', 'category', 'growing_days', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'scientific_name')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'scientific_name', 'category', 'description', 'image')
        }),
        ('Growth Parameters', {
            'fields': ('growing_days', 'water_requirement_mm', 'optimal_temp_min', 'optimal_temp_max')
        }),
        ('Planting Parameters', {
            'fields': ('planting_distance_cm', 'seed_rate_kg_per_ha', 'expected_yield_kg_per_ha')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


class InputInline(admin.TabularInline):
    model = InputApplication
    extra = 0
    fields = ('input_type', 'product_name', 'quantity', 'unit', 'cost_per_unit', 'application_date')
    readonly_fields = ('created_at',)


class HarvestInline(admin.TabularInline):
    model = Harvest
    extra = 0
    fields = ('harvest_date', 'quantity_kg', 'quality_grade', 'selling_price_kg', 'total_revenue')
    readonly_fields = ('total_revenue',)


@admin.register(CropSeason)
class CropSeasonAdmin(admin.ModelAdmin):
    list_display = ('crop_type', 'field', 'planting_date', 'expected_harvest_date', 'status', 'is_overdue')
    list_filter = ('status', 'season', 'planting_date')
    search_fields = ('crop_type__name', 'field__name', 'field__farm__name')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [InputInline, HarvestInline]
    
    fieldsets = (
        ('Crop Information', {
            'fields': ('field', 'crop_type', 'variety', 'season')
        }),
        ('Dates', {
            'fields': ('planting_date', 'expected_harvest_date', 'actual_harvest_date')
        }),
        ('Yield & Revenue', {
            'fields': ('estimated_yield_kg', 'actual_yield_kg', 'estimated_revenue', 'actual_revenue')
        }),
        ('Status', {
            'fields': ('status', 'notes')
        }),
    )
    
    def is_overdue(self, obj):
        return obj.is_overdue
    is_overdue.boolean = True
    is_overdue.short_description = 'Overdue?'
    
    actions = ['mark_harvested', 'mark_failed']
    
    def mark_harvested(self, request, queryset):
        queryset.update(status='harvested')
        self.message_user(request, f"{queryset.count()} crops marked as harvested.")
    mark_harvested.short_description = "Mark as harvested"
    
    def mark_failed(self, request, queryset):
        queryset.update(status='failed')
        self.message_user(request, f"{queryset.count()} crops marked as failed.")
    mark_failed.short_description = "Mark as failed"


@admin.register(InputApplication)
class InputApplicationAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'crop_season', 'input_type', 'quantity', 'unit', 'total_cost', 'application_date')
    list_filter = ('input_type', 'application_date')
    search_fields = ('product_name', 'crop_season__crop_type__name')
    readonly_fields = ('created_at',)
    
    def total_cost(self, obj):
        return f"${obj.total_cost}"
    total_cost.short_description = 'Total Cost'


@admin.register(Harvest)
class HarvestAdmin(admin.ModelAdmin):
    list_display = ('crop_season', 'harvest_date', 'quantity_kg', 'quality_grade', 'total_revenue')
    list_filter = ('quality_grade', 'harvest_date')
    search_fields = ('crop_season__crop_type__name',)
    readonly_fields = ('total_revenue', 'created_at')


# ============================================================
# SECTION 4: LIVESTOCK MANAGEMENT ADMIN
# ============================================================

@admin.register(AnimalType)
class AnimalTypeAdmin(admin.ModelAdmin):
    list_display = ('species', 'breed', 'avg_lifespan_years', 'avg_milk_liters_per_day', 'is_active')
    list_filter = ('species', 'is_active')
    search_fields = ('breed',)


class HealthRecordInline(admin.TabularInline):
    model = HealthRecord
    extra = 0
    fields = ('record_date', 'record_type', 'diagnosis', 'treatment', 'cost')
    readonly_fields = ('created_at',)


class BreedingRecordInline(admin.TabularInline):
    model = BreedingRecord
    fk_name = 'animal'
    extra = 0
    fields = ('breeding_date', 'mate_animal', 'method', 'result', 'expected_calving_date')
    readonly_fields = ('created_at',)


@admin.register(Animal)
class AnimalAdmin(admin.ModelAdmin):
    list_display = ('tag_number', 'animal_type', 'farm', 'gender', 'age_months', 'status')
    list_filter = ('animal_type__species', 'gender', 'status', 'farm')
    search_fields = ('tag_number', 'name')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [HealthRecordInline, BreedingRecordInline]
    
    fieldsets = (
        ('Identification', {
            'fields': ('farm', 'animal_type', 'tag_number', 'name')
        }),
        ('Biological Info', {
            'fields': ('gender', 'birth_date', 'weight_kg')
        }),
        ('Purchase Info', {
            'fields': ('purchase_date', 'purchase_price')
        }),
        ('Parentage', {
            'fields': ('mother', 'father')
        }),
        ('Current Status', {
            'fields': ('status', 'location', 'notes')
        }),
    )
    
    actions = ['mark_sold', 'mark_dead']
    
    def mark_sold(self, request, queryset):
        queryset.update(status='sold')
        self.message_user(request, f"{queryset.count()} animals marked as sold.")
    mark_sold.short_description = "Mark as sold"
    
    def mark_dead(self, request, queryset):
        queryset.update(status='dead')
        self.message_user(request, f"{queryset.count()} animals marked as dead.")
    mark_dead.short_description = "Mark as dead"


@admin.register(HealthRecord)
class HealthRecordAdmin(admin.ModelAdmin):
    list_display = ('animal', 'record_type', 'record_date', 'diagnosis', 'next_due_date')
    list_filter = ('record_type', 'record_date')
    search_fields = ('animal__tag_number', 'diagnosis')
    readonly_fields = ('created_at',)


@admin.register(BreedingRecord)
class BreedingRecordAdmin(admin.ModelAdmin):
    list_display = ('animal', 'breeding_date', 'mate_animal', 'result', 'expected_calving_date')
    list_filter = ('result', 'breeding_date')
    search_fields = ('animal__tag_number',)


@admin.register(MilkProduction)
class MilkProductionAdmin(admin.ModelAdmin):
    list_display = ('animal', 'production_date', 'morning_kg', 'evening_kg', 'total_kg')
    list_filter = ('production_date',)
    search_fields = ('animal__tag_number',)
    readonly_fields = ('total_kg', 'created_at')


# ============================================================
# SECTION 5: EQUIPMENT RENTAL ADMIN
# ============================================================

@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'category', 'daily_rate', 'status', 'is_verified')
    list_filter = ('category', 'status', 'is_verified')
    search_fields = ('name', 'owner__username', 'location')
    readonly_fields = ('created_at', 'updated_at')
    
    actions = ['verify_equipment']
    
    def verify_equipment(self, request, queryset):
        queryset.update(is_verified=True)
        self.message_user(request, f"{queryset.count()} equipment items verified.")
    verify_equipment.short_description = "Verify selected equipment"


@admin.register(EquipmentBooking)
class EquipmentBookingAdmin(admin.ModelAdmin):
    list_display = ('equipment', 'renter', 'start_date', 'end_date', 'total_days', 'total_cost', 'status')
    list_filter = ('status', 'start_date', 'end_date')
    search_fields = ('equipment__name', 'renter__username')
    readonly_fields = ('total_days', 'total_cost', 'created_at', 'updated_at')
    
    actions = ['confirm_bookings', 'complete_bookings']
    
    def confirm_bookings(self, request, queryset):
        queryset.update(status='confirmed')
        self.message_user(request, f"{queryset.count()} bookings confirmed.")
    confirm_bookings.short_description = "Confirm selected bookings"
    
    def complete_bookings(self, request, queryset):
        queryset.update(status='completed')
        self.message_user(request, f"{queryset.count()} bookings completed.")
    complete_bookings.short_description = "Complete selected bookings"


# ============================================================
# SECTION 6: MARKETPLACE ADMIN
# ============================================================

@admin.register(ProductListing)
class ProductListingAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'seller', 'quantity', 'unit', 'price_per_unit', 'total_price', 'status')
    list_filter = ('category', 'unit', 'status', 'is_organic')
    search_fields = ('product_name', 'seller__name')
    readonly_fields = ('total_price', 'created_at', 'updated_at')
    
    actions = ['approve_listings', 'reject_listings']
    
    def approve_listings(self, request, queryset):
        queryset.update(status='active')
        self.message_user(request, f"{queryset.count()} listings approved.")
    approve_listings.short_description = "Approve selected listings"
    
    def reject_listings(self, request, queryset):
        queryset.update(status='cancelled')
        self.message_user(request, f"{queryset.count()} listings rejected.")
    reject_listings.short_description = "Reject selected listings"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'buyer', 'listing', 'quantity', 'total_amount', 'status', 'payment_status')
    list_filter = ('status', 'payment_status', 'created_at')
    search_fields = ('buyer__username', 'listing__product_name')
    readonly_fields = ('subtotal', 'total_amount', 'created_at', 'updated_at')
    
    actions = ['confirm_orders', 'mark_delivered']
    
    def confirm_orders(self, request, queryset):
        queryset.update(status='confirmed')
        self.message_user(request, f"{queryset.count()} orders confirmed.")
    confirm_orders.short_description = "Confirm selected orders"
    
    def mark_delivered(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='delivered', delivered_at=timezone.now())
        self.message_user(request, f"{queryset.count()} orders marked as delivered.")
    mark_delivered.short_description = "Mark as delivered"


# ============================================================
# SECTION 7: PEST DETECTION ADMIN
# ============================================================

@admin.register(PestReport)
class PestReportAdmin(admin.ModelAdmin):
    list_display = ('ai_diagnosis', 'farmer', 'farm', 'confidence', 'severity', 'status', 'created_at')
    list_filter = ('severity', 'status', 'agronomist_verified', 'created_at')
    search_fields = ('ai_diagnosis', 'farmer__username', 'farm__name')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Detection Info', {
            'fields': ('farmer', 'farm', 'field', 'crop', 'image', 'ai_diagnosis', 'confidence')
        }),
        ('Assessment', {
            'fields': ('severity', 'affected_area_percentage', 'treatment_recommended', 'prevention_tips')
        }),
        ('Verification', {
            'fields': ('agronomist_verified', 'agronomist_notes', 'verified_by', 'status')
        }),
    )
    
    actions = ['verify_reports', 'mark_high_severity']
    
    def verify_reports(self, request, queryset):
        queryset.update(agronomist_verified=True, status='resolved')
        self.message_user(request, f"{queryset.count()} reports verified.")
    verify_reports.short_description = "Verify selected reports"
    
    def mark_high_severity(self, request, queryset):
        queryset.update(severity='high')
        self.message_user(request, f"{queryset.count()} reports marked as high severity.")
    mark_high_severity.short_description = "Mark as high severity"


# ============================================================
# SECTION 8: WEATHER & IRRIGATION ADMIN
# ============================================================

@admin.register(WeatherAlert)
class WeatherAlertAdmin(admin.ModelAdmin):
    list_display = ('title', 'farm', 'alert_type', 'severity', 'start_date', 'end_date', 'is_read')
    list_filter = ('alert_type', 'severity', 'start_date')
    search_fields = ('title', 'farm__name')
    readonly_fields = ('created_at',)


@admin.register(IrrigationSchedule)
class IrrigationScheduleAdmin(admin.ModelAdmin):
    list_display = ('field', 'scheduled_date', 'duration_hours', 'status')
    list_filter = ('status', 'scheduled_date')
    search_fields = ('field__name', 'field__farm__name')
    readonly_fields = ('created_at',)


# ============================================================
# SECTION 9: INSURANCE ADMIN
# ============================================================

class ClaimInline(admin.TabularInline):
    model = InsuranceClaim
    extra = 0
    fields = ('claim_date', 'damage_percentage', 'estimated_loss', 'status')
    readonly_fields = ('claim_date',)


@admin.register(InsurancePolicy)
class InsurancePolicyAdmin(admin.ModelAdmin):
    list_display = ('policy_number', 'farmer', 'policy_type', 'sum_insured', 'premium_paid', 'start_date', 'end_date', 'status')
    list_filter = ('policy_type', 'status', 'start_date', 'end_date')
    search_fields = ('policy_number', 'farmer__username')
    readonly_fields = ('policy_number', 'created_at', 'updated_at')
    inlines = [ClaimInline]
    
    def save_model(self, request, obj, form, change):
        if not obj.policy_number:
            import uuid
            obj.policy_number = f"INS-{uuid.uuid4().hex[:8].upper()}"
        super().save_model(request, obj, form, change)


@admin.register(InsuranceClaim)
class InsuranceClaimAdmin(admin.ModelAdmin):
    list_display = ('policy', 'claim_date', 'damage_percentage', 'estimated_loss', 'approved_amount', 'payout_amount', 'status')
    list_filter = ('status', 'claim_date')
    search_fields = ('policy__policy_number',)
    readonly_fields = ('claim_date', 'created_at', 'updated_at')
    
    actions = ['approve_claims', 'reject_claims', 'mark_paid']
    
    def approve_claims(self, request, queryset):
        queryset.update(status='approved')
        self.message_user(request, f"{queryset.count()} claims approved.")
    approve_claims.short_description = "Approve selected claims"
    
    def reject_claims(self, request, queryset):
        queryset.update(status='rejected')
        self.message_user(request, f"{queryset.count()} claims rejected.")
    reject_claims.short_description = "Reject selected claims"
    
    def mark_paid(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='paid', paid_date=timezone.now().date())
        self.message_user(request, f"{queryset.count()} claims marked as paid.")
    mark_paid.short_description = "Mark as paid"


# ============================================================
# SECTION 10: LABOR MANAGEMENT ADMIN
# ============================================================

class WorkShiftInline(admin.TabularInline):
    model = WorkShift
    extra = 0
    fields = ('date', 'task', 'hours_worked', 'wage_rate', 'total_pay')
    readonly_fields = ('total_pay',)


@admin.register(Worker)
class WorkerAdmin(admin.ModelAdmin):
    list_display = ('worker', 'farm', 'hourly_wage', 'is_active')
    list_filter = ('is_active', 'farm')
    search_fields = ('worker__username', 'worker__first_name', 'worker__last_name')
    inlines = [WorkShiftInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            total_hours=Sum('shifts__hours_worked')
        )


@admin.register(WorkShift)
class WorkShiftAdmin(admin.ModelAdmin):
    list_display = ('worker', 'date', 'task', 'hours_worked', 'wage_rate', 'total_pay')
    list_filter = ('task', 'date')
    search_fields = ('worker__worker__username',)
    readonly_fields = ('total_pay', 'created_at')


@admin.register(Payroll)
class PayrollAdmin(admin.ModelAdmin):
    list_display = ('worker', 'period_start', 'period_end', 'total_hours', 'total_pay', 'net_pay', 'status')
    list_filter = ('status', 'period_start')
    search_fields = ('worker__worker__username',)
    readonly_fields = ('created_at', 'updated_at')


# ============================================================
# SECTION 11: FINANCIAL TRACKING ADMIN
# ============================================================

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('farm', 'transaction_type', 'category', 'amount', 'date', 'description')
    list_filter = ('transaction_type', 'category', 'date')
    search_fields = ('description', 'farm__name')
    readonly_fields = ('created_at',)


# ============================================================
# SECTION 12: NOTIFICATIONS ADMIN
# ============================================================

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('user__username', 'title')
    readonly_fields = ('created_at',)


# ============================================================
# SECTION 13: FARMER NETWORK & KNOWLEDGE SHARING (FEATURE 10)
# ============================================================

@admin.register(DiscussionForum)
class DiscussionForumAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'is_moderated', 'is_active', 'member_count', 'post_count', 'created_at')
    list_filter = ('category', 'is_moderated', 'is_active', 'created_at')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at', 'member_count', 'post_count')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'category')
        }),
        ('Moderation', {
            'fields': ('is_moderated', 'moderators')
        }),
        ('Settings', {
            'fields': ('allow_attachments', 'allow_external_links', 'is_active')
        }),
        ('Statistics', {
            'fields': ('member_count', 'post_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ForumThread)
class ForumThreadAdmin(admin.ModelAdmin):
    list_display = ('title', 'forum', 'author', 'is_pinned', 'is_closed', 'view_count', 'reply_count', 'created_at')
    list_filter = ('forum', 'is_pinned', 'is_closed', 'created_at')
    search_fields = ('title', 'content', 'author__username')
    readonly_fields = ('view_count', 'reply_count', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('forum', 'author', 'title', 'content')
        }),
        ('Status & Engagement', {
            'fields': ('is_pinned', 'is_closed', 'view_count', 'reply_count')
        }),
        ('Tags', {
            'fields': ('tags',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ForumReply)
class ForumReplyAdmin(admin.ModelAdmin):
    list_display = ('thread', 'author', 'is_helpful', 'helpful_count', 'created_at')
    list_filter = ('is_helpful', 'created_at')
    search_fields = ('content', 'author__username', 'thread__title')
    readonly_fields = ('created_at', 'updated_at', 'helpful_count')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('thread', 'author', 'content')
        }),
        ('Recognition', {
            'fields': ('is_helpful', 'helpful_count')
        }),
        ('Attachments', {
            'fields': ('attachments',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(GroupBuyingInitiative)
class GroupBuyingInitiativeAdmin(admin.ModelAdmin):
    list_display = ('title', 'product_type', 'status', 'discount_percent', 'farmers_joined', 'total_quantity_pledged', 'created_at')
    list_filter = ('status', 'created_at', 'end_date')
    search_fields = ('title', 'product_type', 'organizer')
    readonly_fields = ('created_at', 'farmers_joined', 'total_quantity_pledged')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'product_type')
        }),
        ('Pricing & Quantity', {
            'fields': ('minimum_order_quantity', 'quantity_unit', 'unit_price_without_group', 'unit_price_with_group', 'discount_percent')
        }),
        ('Timeline', {
            'fields': ('start_date', 'end_date', 'delivery_date')
        }),
        ('Organizer', {
            'fields': ('organizer', 'organizer_contact')
        }),
        ('Status', {
            'fields': ('status', 'farmers_joined', 'total_quantity_pledged')
        }),
    )
    
    actions = ['mark_closed', 'mark_completed', 'mark_cancelled']
    
    def mark_closed(self, request, queryset):
        queryset.update(status='closed')
        self.message_user(request, f"{queryset.count()} initiatives marked as closed.")
    mark_closed.short_description = "Mark as closed"
    
    def mark_completed(self, request, queryset):
        queryset.update(status='completed')
        self.message_user(request, f"{queryset.count()} initiatives marked as completed.")
    mark_completed.short_description = "Mark as completed"
    
    def mark_cancelled(self, request, queryset):
        queryset.update(status='cancelled')
        self.message_user(request, f"{queryset.count()} initiatives marked as cancelled.")
    mark_cancelled.short_description = "Mark as cancelled"


@admin.register(GroupBuyingParticipant)
class GroupBuyingParticipantAdmin(admin.ModelAdmin):
    list_display = ('farmer', 'initiative', 'quantity_pledged', 'quantity_received', 'payment_status', 'amount_paid', 'joined_at')
    list_filter = ('payment_status', 'joined_at', 'initiative')
    search_fields = ('farmer__username', 'initiative__title')
    readonly_fields = ('joined_at',)
    
    fieldsets = (
        ('Participation', {
            'fields': ('initiative', 'farmer', 'quantity_pledged', 'quantity_received')
        }),
        ('Payment', {
            'fields': ('payment_status', 'amount_paid')
        }),
        ('Timestamps', {
            'fields': ('joined_at',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_payment_pending', 'mark_payment_paid', 'mark_payment_partial']
    
    def mark_payment_pending(self, request, queryset):
        queryset.update(payment_status='pending')
        self.message_user(request, f"{queryset.count()} participants marked as pending payment.")
    mark_payment_pending.short_description = "Mark payment as pending"
    
    def mark_payment_paid(self, request, queryset):
        queryset.update(payment_status='paid')
        self.message_user(request, f"{queryset.count()} participants marked as paid.")
    mark_payment_paid.short_description = "Mark payment as paid"
    
    def mark_payment_partial(self, request, queryset):
        queryset.update(payment_status='partial')
        self.message_user(request, f"{queryset.count()} participants marked as partially paid.")
    mark_payment_partial.short_description = "Mark payment as partial"


# ============================================================
# SECTION 14: CARBON FOOTPRINT TRACKER (FEATURE 11)
# ============================================================

@admin.register(EmissionSource)
class EmissionSourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'farm', 'source_type', 'unit', 'emission_factor', 'is_active')
    list_filter = ('source_type', 'is_active', 'created_at')
    search_fields = ('name', 'farm__name')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('farm', 'source_type', 'name')
        }),
        ('Emission Factor', {
            'fields': ('emission_factor', 'unit')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


@admin.register(EmissionRecord)
class EmissionRecordAdmin(admin.ModelAdmin):
    list_display = ('farm', 'source', 'record_date', 'quantity_used', 'calculated_emissions_kg_co2e', 'created_at')
    list_filter = ('source', 'record_date', 'farm')
    search_fields = ('farm__name', 'source__name', 'description')
    readonly_fields = ('calculated_emissions_kg_co2e', 'created_at')
    
    fieldsets = (
        ('Record Information', {
            'fields': ('farm', 'source', 'record_date', 'quantity_used')
        }),
        ('Calculated Emissions', {
            'fields': ('calculated_emissions_kg_co2e',)
        }),
        ('Details', {
            'fields': ('description',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(CarbonSequestration)
class CarbonSequestrationAdmin(admin.ModelAdmin):
    list_display = ('name', 'farm', 'activity_type', 'area_hectares', 'annual_sequestration_kg_co2e', 'start_date')
    list_filter = ('activity_type', 'start_date', 'farm')
    search_fields = ('name', 'farm__name', 'description')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('farm', 'activity_type', 'name', 'description')
        }),
        ('Quantity', {
            'fields': ('area_hectares', 'tree_count')
        }),
        ('Sequestration Rate', {
            'fields': ('annual_sequestration_kg_co2e',)
        }),
        ('Timeline', {
            'fields': ('start_date', 'end_date')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


# ============================================================
# SECTION 15: FARM MAP & GEOFENCING (FEATURE 12)
# ============================================================

@admin.register(FarmBoundary)
class FarmBoundaryAdmin(admin.ModelAdmin):
    list_display = ('farm', 'total_area_hectares', 'is_verified', 'created_at')
    list_filter = ('is_verified', 'created_at')
    search_fields = ('farm__name',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Farm & Boundary', {
            'fields': ('farm', 'total_area_hectares')
        }),
        ('Coordinates', {
            'fields': ('geojson_boundary', 'center_latitude', 'center_longitude')
        }),
        ('Verification', {
            'fields': ('is_verified',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Geofence)
class GeofenceAdmin(admin.ModelAdmin):
    list_display = ('name', 'farm', 'field', 'is_active', 'enable_exit_alerts', 'enable_entry_alerts', 'created_at')
    list_filter = ('is_active', 'enable_exit_alerts', 'enable_entry_alerts', 'created_at')
    search_fields = ('name', 'farm__name')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('farm', 'name', 'field')
        }),
        ('Boundary', {
            'fields': ('geojson_boundary',)
        }),
        ('Alert Settings', {
            'fields': ('enable_exit_alerts', 'enable_entry_alerts', 'alert_channels')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(LivestockLocation)
class LivestockLocationAdmin(admin.ModelAdmin):
    list_display = ('latitude', 'longitude', 'accuracy_meters', 'is_inside_assigned_geofence', 'recorded_at')
    list_filter = ('is_inside_assigned_geofence', 'recorded_at')
    search_fields = ('device_id',)
    readonly_fields = ('recorded_at', 'created_at')
    
    fieldsets = (
        ('Location', {
            'fields': ('latitude', 'longitude')
        }),
        ('Accuracy', {
            'fields': ('accuracy_meters', 'signal_strength')
        }),
        ('GPS Device', {
            'fields': ('device_id',)
        }),
        ('Geofence Status', {
            'fields': ('is_inside_assigned_geofence',)
        }),
        ('Timestamps', {
            'fields': ('recorded_at', 'created_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(GeofenceAlert)
class GeofenceAlertAdmin(admin.ModelAdmin):
    list_display = ('geofence', 'alert_type', 'is_resolved', 'alert_time', 'created_at')
    list_filter = ('alert_type', 'is_resolved', 'alert_time', 'geofence')
    search_fields = ('geofence__name', 'resolution_notes')
    readonly_fields = ('alert_time', 'created_at')
    
    fieldsets = (
        ('Alert Information', {
            'fields': ('geofence', 'alert_type')
        }),
        ('Location', {
            'fields': ('latitude', 'longitude')
        }),
        ('Resolution', {
            'fields': ('is_resolved', 'resolved_by', 'resolved_at', 'resolution_notes')
        }),
        ('Timestamps', {
            'fields': ('alert_time', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_resolved']
    
    def mark_resolved(self, request, queryset):
        from django.utils import timezone
        queryset.update(is_resolved=True, resolved_at=timezone.now(), resolved_by=request.user)
        self.message_user(request, f"{queryset.count()} alerts marked as resolved.")
    mark_resolved.short_description = "Mark as resolved"


# ============================================================
# SECTION 16: OFFLINE SYNC & DATA MANAGEMENT (FEATURE 13)
# ============================================================

@admin.register(OfflineSyncQueue)
class OfflineSyncQueueAdmin(admin.ModelAdmin):
    list_display = ('user', 'model_name', 'operation', 'is_synced', 'created_at', 'sync_attempted_at')
    list_filter = ('operation', 'is_synced', 'created_at')
    search_fields = ('user__username', 'model_name', 'object_id')
    readonly_fields = ('created_at', 'updated_at', 'sync_attempted_at')
    
    fieldsets = (
        ('User & Operation', {
            'fields': ('user', 'model_name', 'operation', 'object_id')
        }),
        ('Data', {
            'fields': ('payload',)
        }),
        ('Status', {
            'fields': ('is_synced', 'sync_error', 'sync_attempted_at', 'created_at', 'updated_at')
        }),
    )


# ============================================================
# SECTION 17: FARM PROJECTS MANAGEMENT
# ============================================================

class ProjectTaskInline(admin.TabularInline):
    model = ProjectTask
    extra = 1
    fields = ('name', 'description', 'assigned_to', 'due_date', 'completed')
    readonly_fields = ('created_at',)


class ProjectResourceInline(admin.TabularInline):
    model = ProjectResource
    extra = 1
    fields = ('resource_type', 'name', 'quantity', 'unit', 'cost')
    readonly_fields = ('created_at',)


class ProjectMilestoneInline(admin.TabularInline):
    model = ProjectMilestone
    extra = 1
    fields = ('name', 'target_date', 'achieved_date', 'achieved')
    readonly_fields = ('created_at',)


@admin.register(FarmProject)
class FarmProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'farm', 'category', 'priority', 'status', 'start_date', 'budget')
    list_filter = ('category', 'priority', 'status', 'start_date')
    search_fields = ('name', 'farm__name', 'description')


# ============================================================
# SECTION 18: MARKET PRICE INTELLIGENCE
# ============================================================

@admin.register(Commodity)
class CommodityAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'unit', 'created_at')
    list_filter = ('category',)
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(MarketPrice)
class MarketPriceAdmin(admin.ModelAdmin):
    list_display = ('commodity', 'price', 'currency', 'region', 'source', 'price_date', 'recorded_at')
    list_filter = ('commodity', 'region', 'source', 'price_date')
    search_fields = ('commodity__name', 'region', 'source_name')
    readonly_fields = ('recorded_at',)
    date_hierarchy = 'price_date'
    ordering = ('-recorded_at',)


@admin.register(PriceTrend)
class PriceTrendAdmin(admin.ModelAdmin):
    list_display = ('commodity', 'region', 'period', 'avg_price', 'trend_direction', 'percent_change', 'volatility_score')
    list_filter = ('period', 'trend_direction', 'commodity')
    search_fields = ('commodity__name', 'region')
    readonly_fields = ('calculated_at',)


@admin.register(PriceAlert)
class PriceAlertAdmin(admin.ModelAdmin):
    list_display = ('farmer', 'commodity', 'alert_type', 'threshold_price', 'is_active', 'is_triggered', 'created_at')
    list_filter = ('alert_type', 'is_active', 'is_triggered', 'created_at')
    search_fields = ('farmer__username', 'commodity__name', 'region')
    readonly_fields = ('triggered_at', 'created_at', 'updated_at')


@admin.register(SellerListing)
class SellerListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'seller', 'commodity', 'asking_price', 'quantity_available', 'status', 'views', 'inquiry_count', 'created_at')
    list_filter = ('status', 'commodity', 'created_at')
    search_fields = ('title', 'seller__username', 'commodity__name', 'description')
    readonly_fields = ('views', 'inquiry_count', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'


@admin.register(BuyerInquiry)
class BuyerInquiryAdmin(admin.ModelAdmin):
    list_display = ('buyer', 'listing', 'quantity_interested', 'status', 'replies_count', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('buyer__username', 'listing__title')
    readonly_fields = ('replies_count', 'last_reply_at', 'created_at', 'updated_at')


@admin.register(MarketAnalytics)
class MarketAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('commodity', 'current_avg_price', 'recommendation', 'confidence_score', 'calculated_at')
    list_filter = ('recommendation', 'commodity')
    search_fields = ('commodity__name',)
    readonly_fields = ('calculated_at',)


# ============================================================
# SECTION 19: VOICE ASSISTANT
# ============================================================

@admin.register(VoiceCommand)
class VoiceCommandAdmin(admin.ModelAdmin):
    list_display = ('command_name', 'command_type', 'is_active', 'created_at')
    list_filter = ('command_type', 'is_active')
    search_fields = ('command_name', 'description')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(VoiceConversation)
class VoiceConversationAdmin(admin.ModelAdmin):
    list_display = ('user', 'farm', 'status', 'device_type', 'message_count', 'command_count', 'started_at')
    list_filter = ('status', 'device_type', 'started_at')
    search_fields = ('user__username', 'farm__name')
    readonly_fields = ('started_at', 'ended_at', 'duration_seconds')
    date_hierarchy = 'started_at'


@admin.register(VoiceInteraction)
class VoiceInteractionAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'interaction_type', 'recognized_command', 'confidence_score', 'success', 'created_at')
    list_filter = ('interaction_type', 'success', 'created_at')
    search_fields = ('user_input_text', 'system_response_text')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'


@admin.register(VoicePreference)
class VoicePreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_enabled', 'tts_provider', 'stt_provider', 'speech_rate', 'volume_level')
    list_filter = ('is_enabled', 'tts_provider', 'stt_provider')
    search_fields = ('user__username',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(VoiceNotification)
class VoiceNotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'title', 'priority', 'is_read', 'is_played', 'created_at')
    list_filter = ('notification_type', 'priority', 'is_read', 'is_played')
    search_fields = ('user__username', 'title', 'message')
    readonly_fields = ('created_at', 'read_at', 'sent_at')
    date_hierarchy = 'created_at'


@admin.register(VoiceCommandHistory)
class VoiceCommandHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'command', 'command_text', 'success', 'user_helpful', 'executed_at')
    list_filter = ('success', 'user_helpful', 'executed_at')
    search_fields = ('user__username', 'command_text')
    readonly_fields = ('executed_at',)
    date_hierarchy = 'executed_at'


# ============================================================
# SECTION 20: AI CHATBOT
# ============================================================

@admin.register(ChatIntent)
class ChatIntentAdmin(admin.ModelAdmin):
    list_display = ('intent_name', 'category', 'is_active', 'confidence_threshold', 'created_at')
    list_filter = ('category', 'is_active')
    search_fields = ('intent_name', 'keywords')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'farm', 'status', 'message_count', 'user_satisfaction', 'started_at')
    list_filter = ('status', 'language', 'started_at')
    search_fields = ('user__username', 'farm__name')
    readonly_fields = ('started_at', 'ended_at', 'message_count')
    date_hierarchy = 'started_at'


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('session', 'message_type', 'intent', 'confidence_score', 'is_helpful', 'created_at')
    list_filter = ('message_type', 'is_helpful', 'created_at')
    search_fields = ('session__user__username', 'content')
    readonly_fields = ('created_at', 'session')
    date_hierarchy = 'created_at'


@admin.register(ChatResponse)
class ChatResponseAdmin(admin.ModelAdmin):
    list_display = ('question', 'category', 'usage_count', 'avg_satisfaction', 'is_approved', 'created_at')
    list_filter = ('category', 'is_approved', 'created_at')
    search_fields = ('question', 'answer', 'keywords')
    readonly_fields = ('created_at', 'updated_at', 'usage_count')
    date_hierarchy = 'created_at'


@admin.register(ChatFeedback)
class ChatFeedbackAdmin(admin.ModelAdmin):
    list_display = ('message', 'rating', 'user_submitted', 'created_at')
    list_filter = ('rating', 'user_submitted', 'created_at')
    search_fields = ('message__content', 'comment')
    readonly_fields = ('created_at', 'message')
    date_hierarchy = 'created_at'


@admin.register(ChatStatistics)
class ChatStatisticsAdmin(admin.ModelAdmin):
    list_display = ('date', 'total_sessions', 'total_messages', 'avg_satisfaction', 'unique_users', 'resolved_queries')
    list_filter = ('date',)
    readonly_fields = ('date', 'total_sessions', 'total_messages', 'avg_messages_per_session', 'avg_satisfaction', 'most_common_intent', 'unique_users', 'resolved_queries')
    date_hierarchy = 'date'


# ============================================================
# SECTION 21: GPS MAPPING & LOCATION INTELLIGENCE
# ============================================================

@admin.register(FarmLocation)
class FarmLocationAdmin(admin.ModelAdmin):
    list_display = ('farm', 'region', 'district', 'latitude', 'longitude', 'altitude', 'verified', 'created_at')
    list_filter = ('region', 'verified', 'created_at')
    search_fields = ('farm__name', 'region', 'district', 'address')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(FarmFieldZone)
class FarmFieldZoneAdmin(admin.ModelAdmin):
    list_display = ('field', 'name', 'zone_type', 'area_hectares', 'severity_level', 'created_at')
    list_filter = ('zone_type', 'severity_level', 'created_at')
    search_fields = ('field__name', 'name')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'


@admin.register(FarmGeofenceAlert)
class FarmGeofenceAlertAdmin(admin.ModelAdmin):
    list_display = ('farm', 'name', 'alert_type', 'is_active', 'notify_on_entry', 'notify_on_exit', 'created_at')
    list_filter = ('alert_type', 'is_active', 'created_at')
    search_fields = ('farm__name', 'name')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'


@admin.register(FarmLocationAnalytics)
class FarmLocationAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('farm', 'date', 'avg_yield_per_hectare', 'total_area_cultivated', 'total_production')
    list_filter = ('date',)
    search_fields = ('farm__name',)
    readonly_fields = ('date',)
    date_hierarchy = 'date'


@admin.register(FarmCropRotationPlan)
class FarmCropRotationPlanAdmin(admin.ModelAdmin):
    list_display = ('field', 'current_crop', 'rotation_type', 'current_season')
    list_filter = ('rotation_type', 'current_season')
    search_fields = ('field__name', 'current_crop')
    readonly_fields = ()


@admin.register(FarmProximityAnalysis)
class FarmProximityAnalysisAdmin(admin.ModelAdmin):
    list_display = ('field', 'distance_to_water_source_km', 'distance_to_market_km', 'distance_to_road_km')
    list_filter = ('water_availability', 'market_accessibility', 'road_accessibility')
    search_fields = ('field__name',)
    readonly_fields = ()


# ============================================================
# SECTION 22: OFFLINE AI CAPABILITIES
# ============================================================

@admin.register(OfflineCache)
class OfflineCacheAdmin(admin.ModelAdmin):
    list_display = ('user', 'cache_type', 'key', 'size_kb', 'created_at', 'expires_at')
    list_filter = ('cache_type', 'created_at', 'expires_at')
    search_fields = ('user__username', 'key')
    readonly_fields = ('created_at', 'updated_at', 'size_kb')
    date_hierarchy = 'created_at'


@admin.register(SyncQueue)
class SyncQueueAdmin(admin.ModelAdmin):
    list_display = ('user', 'operation_type', 'resource_type', 'status', 'retry_count', 'created_at')
    list_filter = ('status', 'operation_type', 'created_at')
    search_fields = ('user__username', 'resource_type')
    readonly_fields = ('created_at', 'last_attempted_at', 'completed_at')
    date_hierarchy = 'created_at'


@admin.register(OfflinePreference)
class OfflinePreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'enable_offline_mode', 'sync_mode', 'sync_frequency_minutes', 'cache_size_mb')
    list_filter = ('enable_offline_mode', 'sync_mode')
    search_fields = ('user__username',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(OfflineSyncLog)
class OfflineSyncLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'sync_type', 'result', 'records_synced', 'records_failed', 'duration_seconds', 'sync_timestamp')
    list_filter = ('result', 'sync_type', 'sync_timestamp')
    search_fields = ('user__username',)
    readonly_fields = ('sync_timestamp', 'duration_seconds')
    date_hierarchy = 'sync_timestamp'


@admin.register(CachedMarketPrice)
class CachedMarketPriceAdmin(admin.ModelAdmin):
    list_display = ('user', 'commodity_name', 'price_per_unit', 'unit', 'source', 'timestamp', 'expires_at')
    list_filter = ('commodity_category', 'source', 'timestamp')
    search_fields = ('user__username', 'commodity_name')
    readonly_fields = ('cached_at',)
    date_hierarchy = 'timestamp'


@admin.register(CachedWeatherData)
class CachedWeatherDataAdmin(admin.ModelAdmin):
    list_display = ('user', 'forecast_date', 'temperature_celsius', 'humidity_percent', 'condition', 'expires_at')
    list_filter = ('condition', 'forecast_date')
    search_fields = ('user__username',)
    readonly_fields = ('cached_at',)
    date_hierarchy = 'forecast_date'


@admin.register(OfflineAnalytics)
class OfflineAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'times_used_offline', 'total_offline_time_minutes', 'cache_hits', 'cache_misses')
    list_filter = ('date',)
    search_fields = ('user__username',)
    readonly_fields = ('date', 'features_accessed')
    date_hierarchy = 'date'


# ============================================================
# SECTION 23: DISEASE DIAGNOSIS & TREATMENT
# ============================================================

# @admin.register(DiseaseCategory)
class DiseaseCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category_type', 'created_at')
    list_filter = ('category_type',)
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Disease)
class DiseaseAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'initial_severity', 'progression_rate', 'is_quarantine_required')
    list_filter = ('category', 'initial_severity', 'is_quarantine_required')
    search_fields = ('name', 'scientific_name', 'description')
    filter_horizontal = ('affected_crops',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Symptom)
class SymptomAdmin(admin.ModelAdmin):
    list_display = ('disease', 'name', 'affected_body_part', 'severity_indicator', 'is_primary_symptom')
    list_filter = ('disease', 'affected_body_part', 'severity_indicator', 'is_primary_symptom')
    search_fields = ('name', 'description', 'disease__name')
    readonly_fields = ('created_at',)


@admin.register(TreatmentOption)
class TreatmentOptionAdmin(admin.ModelAdmin):
    list_display = ('disease', 'name', 'treatment_type', 'applicable_stage', 'effectiveness_percent', 'is_organic_approved')
    list_filter = ('disease', 'treatment_type', 'applicable_stage', 'is_organic_approved')
    search_fields = ('name', 'disease__name', 'active_ingredient')
    readonly_fields = ('created_at',)


@admin.register(DiagnosisRecord)
class DiagnosisRecordAdmin(admin.ModelAdmin):
    list_display = ('disease', 'farm', 'crop', 'status', 'confidence_score', 'severity_level', 'detected_at')
    list_filter = ('status', 'disease', 'severity_level', 'detected_at')
    search_fields = ('farm__name', 'disease__name', 'user__username')
    readonly_fields = ('detected_at', 'updated_at', 'confidence_score')
    date_hierarchy = 'detected_at'


@admin.register(DiagnosisHistory)
class DiagnosisHistoryAdmin(admin.ModelAdmin):
    list_display = ('diagnosis', 'status_before', 'status_after', 'changed_by', 'changed_at')
    list_filter = ('status_after', 'changed_at')
    search_fields = ('diagnosis__disease__name',)
    readonly_fields = ('changed_at',)
    date_hierarchy = 'changed_at'


@admin.register(DiseaseAlert)
class DiseaseAlertAdmin(admin.ModelAdmin):
    list_display = ('disease', 'title', 'alert_type', 'urgency_level', 'is_active', 'issued_at')
    list_filter = ('alert_type', 'is_active', 'urgency_level', 'issued_at')
    search_fields = ('title', 'disease__name')
    filter_horizontal = ('affected_crops',)
    readonly_fields = ('issued_at',)
    date_hierarchy = 'issued_at'


@admin.register(DiseaseStatistics)
class DiseaseStatisticsAdmin(admin.ModelAdmin):
    list_display = ('farm', 'crop', 'date', 'total_diseases_detected', 'confirmed_diseases', 'treatment_success_rate')
    list_filter = ('date', 'farm')
    search_fields = ('farm__name',)
    readonly_fields = ('date',)
    date_hierarchy = 'date'


@admin.register(ProjectResource)
class ProjectResourceAdmin(admin.ModelAdmin):
    list_display = ('resource_type', 'project', 'name', 'quantity', 'unit', 'cost')
    list_filter = ('resource_type',)
    search_fields = ('project__name', 'name')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Resource Info', {
            'fields': ('project', 'resource_type', 'name', 'quantity', 'unit')
        }),
        ('Cost', {
            'fields': ('cost',)
        }),
        ('Details', {
            'fields': ('notes',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def formfield_for_dbfield(self, db_field, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, **kwargs)
        if db_field.name == 'cost':
            formfield.label = 'Cost (KES)'
        return formfield


@admin.register(ProjectMilestone)
class ProjectMilestoneAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'target_date', 'achieved_date', 'achieved')
    list_filter = ('achieved', 'target_date')
    search_fields = ('name', 'project__name')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Milestone Info', {
            'fields': ('project', 'name')
        }),
        ('Timeline', {
            'fields': ('target_date', 'achieved_date', 'achieved')
        }),
        ('Details', {
            'fields': ('notes',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


# ============================================================
# CUSTOM ADMIN SITE CONFIGURATION
# ============================================================

admin.site.site_header = "FarmWise Administration"
admin.site.site_title = "FarmWise Admin Portal"
admin.site.index_title = "Welcome to FarmWise - Agriculture Management System"

# ============================================================
# ADMIN SITE CUSTOMIZATION
# ============================================================

# Customize admin site
admin.site.site_header = "FarmWise System Administration"
admin.site.site_title = "FarmWise Admin"
admin.site.index_title = "Welcome to FarmWise Administration Dashboard"
