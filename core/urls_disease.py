from django.urls import path
from core.views_disease_web import (
    DiseaseDashboardView,
    DiagnosisListView,
    DiseaseLibraryView,
    DiseaseDetailView,
    DiagnosisCreateView,
    DiagnosisEditView,
    DiagnosisDetailView,
    DiseaseAlertsView,
    diagnosis_report_view,
)

app_name = 'disease'

urlpatterns = [
    # Dashboard
    path('', DiseaseDashboardView.as_view(), name='dashboard'),
    
    # Diagnoses
    path('diagnoses/', DiagnosisListView.as_view(), name='diagnosis_list'),
    path('diagnoses/create/', DiagnosisCreateView.as_view(), name='diagnosis_create'),
    path('diagnoses/<int:pk>/', DiagnosisDetailView.as_view(), name='diagnosis_detail'),
    path('diagnoses/<int:pk>/edit/', DiagnosisEditView.as_view(), name='diagnosis_edit'),
    path('diagnoses/<int:pk>/report/', diagnosis_report_view, name='diagnosis_report'),
    
    # Disease Library
    path('library/', DiseaseLibraryView.as_view(), name='disease_library'),
    path('library/<int:pk>/', DiseaseDetailView.as_view(), name='disease_detail'),
    
    # Alerts
    path('alerts/', DiseaseAlertsView.as_view(), name='alerts_list'),
]
