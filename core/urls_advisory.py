"""
Farmer Advisory System URL Configuration
"""

from django.urls import path
from . import views_advisory as advisory_views

app_name = 'advisory'

urlpatterns = [
    # Dashboard and Profile
    path('', advisory_views.advisory_dashboard, name='dashboard'),
    path('setup-profile/', advisory_views.setup_farm_profile, name='setup_farm_profile'),
    
    # Land Preparation Guides
    path('land-guides/', advisory_views.land_preparation_guides, name='land_guides'),
    path('land-guides/<int:guide_id>/', advisory_views.land_preparation_detail, name='land_detail'),
    
    # Pest Management Guides
    path('pest-guides/', advisory_views.pest_management_guides, name='pest_guides'),
    path('pest-guides/<int:guide_id>/', advisory_views.pest_management_detail, name='pest_detail'),
    
    # Pesticide Database
    path('pesticides/', advisory_views.pesticide_database, name='pesticide_database'),
    path('pesticides/<int:pesticide_id>/', advisory_views.pesticide_detail, name='pesticide_detail'),
    
    # Dosage Calculator
    path('dosage-calculator/', advisory_views.dosage_calculator, name='dosage_calculator'),
    
    # Veterinary Drug Database
    path('veterinary/', advisory_views.veterinary_drug_database, name='veterinary_database'),
    path('veterinary/<int:drug_id>/', advisory_views.veterinary_drug_detail, name='veterinary_detail'),
    
    # Animal Dosage Calculator
    path('animal-dosage/', advisory_views.animal_dosage_calculator, name='animal_dosage_calculator'),
    
    # Advisory Requests
    path('submit-request/', advisory_views.submit_advisory_request, name='submit_request'),
    path('requests/', advisory_views.my_advisory_requests, name='my_requests'),
    path('requests/<int:request_id>/', advisory_views.advisory_request_detail, name='request_detail'),
    
    # Knowledge Base
    path('knowledge/', advisory_views.knowledge_base, name='knowledge_base'),
    path('knowledge/<int:article_id>/', advisory_views.knowledge_article_detail, name='knowledge_article'),
    
    # API Endpoints
    path('api/land-guides/', advisory_views.api_land_guides, name='api_land_guides'),
    path('api/pest-guides/', advisory_views.api_pest_guides, name='api_pest_guides'),
    path('api/calculate-dosage/', advisory_views.api_calculate_dosage, name='api_calculate_dosage'),
    path('api/animal-dosage/', advisory_views.api_animal_dosage, name='api_animal_dosage'),
]
