# core/urls.py
# All FarmWise application URLs

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import views_api

app_name = 'core'

# Setup DRF router for API viewsets
router = DefaultRouter()

# Phase 1: Validation & Activity
router.register(r'validation-rules', views_api.ValidationRuleViewSet, basename='validation-rule')
router.register(r'validation-logs', views_api.ValidationLogViewSet, basename='validation-log')
router.register(r'activities', views_api.ActivityTimelineViewSet, basename='activity')
router.register(r'user-history', views_api.UserHistoryViewSet, basename='user-history')
router.register(r'farm-history', views_api.FarmHistoryViewSet, basename='farm-history')

# Phase 2: Help System
router.register(r'help-content', views_api.HelpContentViewSet, basename='help-content')

# Phase 3: Templates, Recurring Actions, Batch Ops
router.register(r'templates', views_api.TemplateViewSet, basename='template')
router.register(r'template-ratings', views_api.TemplateRatingViewSet, basename='template-rating')
router.register(r'recurring-actions', views_api.RecurringActionViewSet, basename='recurring-action')
router.register(r'recurring-action-logs', views_api.RecurringActionLogViewSet, basename='recurring-action-log')
router.register(r'batch-operations', views_api.BatchOperationViewSet, basename='batch-operation')

# Phase 4: Predictions
router.register(r'predictions', views_api.PredictionViewSet, basename='prediction')

# Phase 5: Scheduled Exports
router.register(r'scheduled-exports', views_api.ScheduledExportViewSet, basename='scheduled-export')

# Phase 6: Workspace Preferences
router.register(r'workspace-preferences', views_api.WorkspacePreferenceViewSet, basename='workspace-preference')

# Validation API (custom methods)
validation_api = views_api.ValidateDataAPIView.as_view({
    'post': 'crop'
})

urlpatterns = [
    # ============================================================
    # API ROUTES (DRF)
    # ============================================================
    path('api/', include(router.urls)),
    path('api/validate/crop/', views_api.ValidateDataAPIView.as_view({'post': 'crop'}), name='api_validate_crop'),
    path('api/validate/livestock/', views_api.ValidateDataAPIView.as_view({'post': 'livestock'}), name='api_validate_livestock'),
    path('api/validate/marketplace/', views_api.ValidateDataAPIView.as_view({'post': 'marketplace'}), name='api_validate_marketplace'),
    
    # ============================================================
    # HOME & DASHBOARD
    # ============================================================
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('wallboard/', views.wallboard, name='wallboard'),
    path('api-keys-debug/', views.api_keys_debug, name='api_keys_debug'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('settings/', views.settings, name='settings'),
    path('settings/change-password/', views.change_password, name='change_password'),
    
    # ============================================================
    # FARM MANAGEMENT
    # ============================================================
    path('farms/', views.farm_list, name='farm_list'),
    path('farms/create/', views.farm_create, name='farm_create'),
    path('farms/<int:pk>/', views.farm_detail, name='farm_detail'),
    path('farms/<int:pk>/edit/', views.farm_edit, name='farm_edit'),
    path('farms/<int:pk>/delete/', views.farm_delete, name='farm_delete'),
    path('farms/<int:farm_id>/fields/add/', views.field_create, name='field_create'),
    path('fields/<int:pk>/edit/', views.field_edit, name='field_edit'),
    path('fields/<int:pk>/delete/', views.field_delete, name='field_delete'),
    
    # ============================================================
    # CROP MANAGEMENT
    # ============================================================
    path('crops/', views.crop_list, name='crop_list'),
    path('crops/plant/', views.crop_plant, name='crop_plant'),
    path('crops/<int:pk>/', views.crop_detail, name='crop_detail'),
    path('crops/<int:pk>/edit/', views.crop_edit, name='crop_edit'),
    path('crops/<int:pk>/delete/', views.crop_delete, name='crop_delete'),
    path('crops/<int:crop_id>/harvest/', views.crop_harvest, name='crop_harvest'),
    path('crops/<int:crop_id>/input/add/', views.input_add, name='input_add'),
    
    # ============================================================
    # LIVESTOCK MANAGEMENT
    # ============================================================
    path('livestock/', views.animal_list, name='animal_list'),
    path('livestock/add/', views.animal_add, name='animal_add'),
    path('livestock/<int:pk>/', views.animal_detail, name='animal_detail'),
    path('livestock/<int:pk>/edit/', views.animal_edit, name='animal_edit'),
    path('livestock/<int:pk>/delete/', views.animal_delete, name='animal_delete'),
    path('livestock/<int:animal_id>/health/add/', views.health_record_add, name='health_record_add'),
    path('livestock/<int:animal_id>/breeding/add/', views.breeding_record_add, name='breeding_record_add'),
    path('livestock/<int:animal_id>/milk/add/', views.milk_production_add, name='milk_production_add'),
    
    # ============================================================
    # EQUIPMENT RENTAL
    # ============================================================
    path('equipment/', views.equipment_list, name='equipment_list'),
    path('equipment/add/', views.equipment_add, name='equipment_add'),
    path('equipment/<int:pk>/', views.equipment_detail, name='equipment_detail'),
    path('equipment/<int:pk>/edit/', views.equipment_edit, name='equipment_edit'),
    path('equipment/<int:pk>/book/', views.equipment_book, name='equipment_book'),
    path('equipment/my-bookings/', views.my_bookings, name='my_bookings'),
    path('equipment/booking/<int:pk>/cancel/', views.cancel_booking, name='cancel_booking'),
    
    # ============================================================
    # MARKETPLACE
    # ============================================================
    path('marketplace/', views.marketplace_list, name='marketplace'),
    path('marketplace/sell/', views.create_listing, name='create_listing'),
    path('marketplace/<int:pk>/edit/', views.edit_listing, name='edit_listing'),
    path('marketplace/<int:pk>/delete/', views.delete_listing, name='delete_listing'),
    path('marketplace/<int:pk>/', views.listing_detail, name='listing_detail'),
    path('marketplace/<int:pk>/buy/', views.buy_product, name='buy_product'),
    path('marketplace/my-listings/', views.my_listings, name='my_listings'),
    path('marketplace/orders/', views.my_orders, name='my_orders'),
    
    # ============================================================
    # PEST DETECTION
    # ============================================================
    path('pest-detection/', views.pest_detection, name='pest_detection'),
    path('pest-detection/upload/', views.pest_upload, name='pest_upload'),
    path('pest-detection/history/', views.pest_history, name='pest_history'),
    path('pest-detection/<int:pk>/', views.pest_detail, name='pest_detail'),
    
    # ============================================================
    # WEATHER
    # ============================================================
    path('weather/', views.weather_forecast, name='weather'),
    path('weather/alerts/', views.weather_alerts, name='weather_alerts'),
    path('weather/alerts/<int:pk>/read/', views.mark_alert_read, name='mark_alert_read'),
    
    # ============================================================
    # IRRIGATION
    # ============================================================
    path('irrigation/', views.irrigation_dashboard, name='irrigation'),
    path('irrigation/schedule/', views.irrigation_schedule, name='irrigation_schedule'),
    path('irrigation/<int:pk>/complete/', views.complete_irrigation, name='complete_irrigation'),
    
    # ============================================================
    # INSURANCE
    # ============================================================
    path('insurance/', views.insurance_dashboard, name='insurance'),
    path('insurance/buy/', views.buy_insurance, name='buy_insurance'),
    path('insurance/<int:pk>/', views.insurance_detail, name='insurance_detail'),
    path('insurance/<int:policy_id>/claim/', views.file_claim, name='file_claim'),
    path('insurance/claims/', views.my_claims, name='my_claims'),
    
    # ============================================================
    # LABOR MANAGEMENT
    # ============================================================
    path('labor/', views.labor_dashboard, name='labor'),
    path('labor/workers/add/', views.add_worker, name='add_worker'),
    path('labor/workers/<int:pk>/edit/', views.edit_worker, name='edit_worker'),
    path('labor/workers/<int:worker_id>/hours/', views.log_hours, name='log_hours'),
    path('labor/payroll/', views.payroll_list, name='payroll_list'),
    path('labor/payroll/<int:pk>/process/', views.process_payroll, name='process_payroll'),
    path('labor/payroll/<int:pk>/edit/', views.payroll_edit, name='payroll_edit'),
    
    # ============================================================
    # REPORTS
    # ============================================================
    path('reports/', views.reports_dashboard, name='reports'),
    path('reports/financial/', views.financial_report, name='financial_report'),
    path('reports/crop-yield/', views.crop_yield_report, name='crop_yield_report'),
    path('reports/livestock/', views.livestock_report, name='livestock_report'),
    path('reports/export/<str:report_type>/', views.export_report, name='export_report'),
    
    # ============================================================
    # NOTIFICATIONS
    # ============================================================
    path('notifications/', views.notification_list, name='notification_list'),
    path('notifications/<int:pk>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    
    # ============================================================
    # LEGACY API ENDPOINTS (for AJAX/JavaScript)
    # ============================================================
    path('api/farms/', views.api_farms, name='api_farms'),
    path('api/fields/<int:farm_id>/', views.api_fields, name='api_fields'),
    path('api/weather/<int:farm_id>/', views.api_weather, name='api_weather'),
    path('api/notifications/', views.api_notifications, name='api_notifications'),
]