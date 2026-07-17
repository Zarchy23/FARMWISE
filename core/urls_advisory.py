"""
Farmer Advisory System URL Configuration - Simplified AI-based Advisory
"""

from django.urls import path
from . import views_advisory as advisory_views

app_name = 'advisory'

urlpatterns = [
    # Main Advisory - redirects to structured form
    path('', advisory_views.advisory_dashboard, name='dashboard'),
    
    # Structured Advisory with AI
    path('structured/', advisory_views.structured_advisory_form, name='structured_form'),
    path('structured/history/', advisory_views.structured_advisory_history, name='structured_history'),
    path('structured/<int:request_id>/', advisory_views.structured_advisory_detail, name='structured_detail'),
    
    # Dosage Calculators (useful tools)
    path('dosage-calculator/', advisory_views.dosage_calculator, name='dosage_calculator'),
    path('animal-dosage/', advisory_views.animal_dosage_calculator, name='animal_dosage_calculator'),
]
