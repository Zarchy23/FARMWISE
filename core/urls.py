# core/urls.py
# All FarmWise application URLs

from django.urls import path, include
from django.views.generic import RedirectView
from . import views
from . import views_pest_verification
from . import views_dashboards

# API imports have been removed - using HTML templates instead
# from .api import views_market
# from .api import views_voice
# from .api import views_chatbot
# from .api import views_location
# from .api import views_offline
# from .api import views_disease

app_name = 'core'

# DRF routers have been removed - using traditional Django views

urlpatterns = [
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
    path('livestock/breeding/select/', views.breeding_record_select_animal, name='breeding_record_select_animal'),
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
    path('marketplace/<int:pk>/toggle-stock/', views.toggle_out_of_stock, name='toggle_out_of_stock'),
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
    # PEST DETECTION VERIFICATION (AGRONOMIST)
    # ============================================================
    path('pest-verification/dashboard/', views_pest_verification.agronomist_pest_dashboard, name='agronomist_pest_dashboard'),
    path('pest-verification/<int:pk>/', views_pest_verification.pest_verification_detail, name='pest_verification_detail'),
    path('api/pest-reports/<int:pk>/approve/', views_pest_verification.api_approve_pest_report, name='api_approve_pest_report'),
    path('api/pest-reports/<int:pk>/reject/', views_pest_verification.api_reject_pest_report, name='api_reject_pest_report'),
    path('api/pest-reports/statistics/', views_pest_verification.agronomist_statistics, name='agronomist_statistics'),
    
    # ============================================================
    # WEATHER
    # ============================================================
    path('weather/', views.weather_forecast, name='weather'),
    path('weather/alerts/', views.weather_alerts, name='weather_alerts'),
    path('weather/alerts/<int:pk>/read/', views.mark_alert_read, name='mark_alert_read'),
    
    # FREE Weather APIs (Open-Meteo - no API key required!)
    path('api/weather/<int:farm_id>/forecast/', views.api_weather_forecast_live, name='api_weather_forecast_live'),
    path('api/weather/<int:farm_id>/agricultural/', views.api_weather_agricultural, name='api_weather_agricultural'),
    
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
    path('labor/workers/select-hours/', views.log_hours_select_worker, name='log_hours_select_worker'),
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
    # FEATURE 10: FARMER NETWORK & KNOWLEDGE SHARING
    # ============================================================
    path('community/forums/', views.forum_list, name='forum_list'),
    path('community/forums/create/', views.forum_create, name='forum_create'),
    path('community/forums/<int:pk>/', views.forum_detail, name='forum_detail'),
    path('community/forums/<int:forum_id>/threads/', views.forum_threads, name='forum_threads'),
    path('community/forums/<int:forum_id>/thread/create/', views.thread_create, name='thread_create'),
    path('community/thread/<int:pk>/', views.thread_detail, name='thread_detail'),
    path('community/thread/<int:thread_id>/reply/', views.reply_create, name='reply_create'),
    path('community/group-buying/', views.group_buying_list, name='group_buying_list'),
    path('community/group-buying/create/', views.group_buying_create, name='group_buying_create'),
    path('community/group-buying/<int:pk>/', views.group_buying_detail, name='group_buying_detail'),
    path('community/group-buying/<int:initiative_id>/join/', views.group_buying_join, name='group_buying_join'),
    
    # ============================================================
    # FEATURE 11: CARBON FOOTPRINT TRACKER
    # ============================================================
    path('carbon/tracker/', views.carbon_tracker, name='carbon_tracker'),
    path('carbon/tracker/record/create/', views.emission_record_create, name='emission_record_create'),
    path('carbon/tracker/source/create/', views.emission_source_create, name='emission_source_create'),
    path('carbon/report/', views.carbon_report, name='carbon_report'),
    path('carbon/report/<int:pk>/', views.carbon_report_detail, name='carbon_report_detail'),
    path('carbon/sequestration/create/', views.sequestration_create, name='sequestration_create'),
    
    # ============================================================
    # FEATURE 12: FARM MAPPING & GEOFENCING
    # ============================================================
    path('mapping/farm-map/', views.farm_map, name='farm_map'),
    path('mapping/farm-boundary/<int:farm_id>/', views.farm_boundary_detail, name='farm_boundary_detail'),
    path('mapping/geofences/', views.geofence_list, name='geofence_list'),
    path('mapping/geofences/create/', views.geofence_create, name='geofence_create'),
    path('mapping/geofences/<int:pk>/', views.geofence_detail, name='geofence_detail'),
    path('mapping/geofences/<int:pk>/edit/', views.geofence_edit, name='geofence_edit'),
    path('mapping/livestock-tracking/', views.livestock_tracking, name='livestock_tracking'),
    path('mapping/livestock/<int:livestock_id>/locations/', views.livestock_locations, name='livestock_locations'),
    path('mapping/geofence-alerts/', views.geofence_alerts, name='geofence_alerts'),
    path('mapping/geofences/<int:geofence_id>/alerts/', views.geofence_alerts, name='geofence_alerts_detail'),
    path('mapping/geofence-alerts/<int:alert_id>/resolve/', views.resolve_geofence_alert, name='resolve_geofence_alert'),
    
    # ============================================================
    # FEATURE 13: OFFLINE SYNC & DATA MANAGEMENT
    # ============================================================
    path('sync/dashboard/', views.sync_dashboard, name='sync_dashboard'),
    path('sync/queue/', views.sync_queue, name='sync_queue'),
    path('sync/conflicts/', views.sync_conflicts, name='sync_conflicts'),
    path('sync/conflicts/<int:pk>/resolve/', views.resolve_sync_conflict, name='resolve_sync_conflict'),
    path('sync/retry/<int:pk>/', views.retry_sync, name='retry_sync'),
    
    # ============================================================
    # REMINDERS - FARM ACTIVITY REMINDERS
    # ============================================================
    path('reminders/', views.reminder_list, name='reminder_list'),
    path('reminders/create/', views.reminder_create, name='reminder_create'),
    path('reminders/dashboard/', views.reminder_dashboard, name='reminder_dashboard'),
    path('reminders/<int:pk>/', views.reminder_detail, name='reminder_detail'),
    path('reminders/<int:pk>/edit/', views.reminder_edit, name='reminder_edit'),
    path('reminders/<int:pk>/complete/', views.reminder_complete, name='reminder_complete'),
    path('reminders/<int:pk>/delete/', views.reminder_delete, name='reminder_delete'),
    
    # ============================================================
    # EXPORT ENDPOINTS
    # ============================================================
    path('export/crops/', views.export_crops, name='export_crops'),
    path('export/livestock/', views.export_livestock, name='export_livestock'),
    path('export/equipment/', views.export_equipment, name='export_equipment'),
    path('export/insurance/policies/', views.export_insurance_policies, name='export_insurance_policies'),
    path('export/payroll/', views.export_payroll, name='export_payroll'),
    path('export/pest/reports/', views.export_pest_reports, name='export_pest_reports'),
    path('export/carbon/report/', views.export_carbon_report, name='export_carbon_report'),
    path('export/reminders/', views.export_reminders, name='export_reminders'),
    path('export/marketplace/products/', views.export_marketplace_products, name='export_marketplace_products'),
    
    # ============================================================
    # FARM PROJECTS MANAGEMENT
    # ============================================================
    path('projects/', views.project_list, name='project_list'),
    path('projects/dashboard/', views.project_dashboard, name='project_dashboard'),
    path('projects/create/', views.project_create, name='project_create'),
    path('projects/<int:pk>/', views.project_detail, name='project_detail'),
    path('projects/<int:pk>/edit/', views.project_edit, name='project_edit'),
    path('projects/<int:pk>/delete/', views.project_delete, name='project_delete'),
    path('projects/<int:pk>/task/add/', views.project_add_task, name='project_add_task'),
    path('projects/<int:pk>/task/<int:task_id>/complete/', views.project_complete_task, name='project_complete_task'),
    path('projects/<int:pk>/resource/add/', views.project_add_resource, name='project_add_resource'),
    path('projects/<int:pk>/milestone/add/', views.project_add_milestone, name='project_add_milestone'),
    path('projects/<int:pk>/milestone/<int:milestone_id>/achieve/', views.project_achieve_milestone, name='project_achieve_milestone'),
    
    # ============================================================
    # ANALYTICS - Real-time metrics and KPIs
    # ============================================================
    path('analytics/', views.analytics_dashboard, name='analytics_dashboard'),
    path('analytics/report/', views.generate_analytics_report, name='generate_analytics_report'),
    

    
    # ============================================================
    # HTML DASHBOARDS (Replaced JSON APIs)
    # ============================================================
    # Offline Mode Dashboard
    path('offline/dashboard/', views_dashboards.offline_dashboard, name='offline_dashboard'),
    
    # Market Dashboard
    path('market/dashboard/', views_dashboards.market_dashboard, name='market_dashboard'),
    
    # Voice Assistant Dashboard
    path('voice/dashboard/', views_dashboards.voice_dashboard, name='voice_dashboard'),
    path('voice/commands/', views_dashboards.voice_commands, name='voice_commands'),
    path('voice/history/', views_dashboards.voice_history, name='voice_history'),
    path('voice/preferences/', views_dashboards.voice_preferences, name='voice_preferences'),
    path('voice/interface/', views_dashboards.voice_interface, name='voice_interface'),
    path('api/voice/process/', views_dashboards.api_voice_process, name='api_voice_process'),
    
    # Chatbot Dashboard
    path('chat/', RedirectView.as_view(url='/chat/dashboard/', permanent=False), name='chat_redirect'),
    path('chat/dashboard/', views_dashboards.chatbot_dashboard, name='chatbot_dashboard'),
    path('chat/interface/', views_dashboards.chat_interface, name='chat_interface'),
    
    # Location/GPS Dashboard
    path('location/dashboard/', views_dashboards.location_dashboard, name='location_dashboard'),
    
    # Disease Diagnosis Dashboard
    path('disease/dashboard/', views_dashboards.disease_dashboard, name='disease_dashboard'),
    
    # ============================================================
    # Disease Management (Web Interface)
    # ============================================================
    path('disease/', include(('core.urls_disease', 'disease'))),
    
    # ============================================================
    # SUPERMARKET MANAGEMENT
    # ============================================================
    path('supermarket/', include('core.urls_supermarket')),
    
    # ============================================================
    # PAYMENT SYSTEM (Phase 3.2)
    # ============================================================
    path('webhooks/', include('core.payments.webhooks_urls')),  # Webhook endpoints
    
    # ============================================================
    # FARMER ADVISORY SYSTEM
    # ============================================================
    path('advisory/', include('core.urls_advisory')),
    
    # ============================================================
    # LEGACY API ENDPOINTS (for AJAX/JavaScript)
    # ============================================================
    path('api/chat/message/', views_dashboards.api_chat_message, name='api_chat_message'),
    path('api/farms/', views.api_farms, name='api_farms'),
    path('api/fields/<int:farm_id>/', views.api_fields, name='api_fields'),
    path('api/weather/<int:farm_id>/', views.api_weather, name='api_weather'),
    path('api/notifications/', views.api_notifications, name='api_notifications'),
    path('api/map/save-drawing/', views.save_map_drawing, name='save_map_drawing'),
    path('api/geofences/<int:id>/alert/', views.set_geofence_alert, name='set_geofence_alert'),
]