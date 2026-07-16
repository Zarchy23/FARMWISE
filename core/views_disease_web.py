from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta

from core.models_disease import (
    Disease, Symptom, TreatmentOption, DiagnosisRecord, DiagnosisHistory,
    DiseaseAlert, DiseaseStatistics, DiseaseCategory
)
from core.models import Farm, CropType
from core.services.disease_service import DiseaseService


# ============================================================
# Disease Dashboard View
# ============================================================

class DiseaseDashboardView(LoginRequiredMixin, ListView):
    """Disease diagnosis dashboard"""
    template_name = 'disease/dashboard.html'
    context_object_name = 'recent_diagnoses'
    paginate_by = 5

    def get_queryset(self):
        """Get recent diagnoses for logged-in user"""
        user_farms = Farm.objects.filter(owner=self.request.user)
        if user_farms.exists():
            return DiagnosisRecord.objects.filter(
                farm__in=user_farms
            ).order_by('-detected_at')[:5]
        return DiagnosisRecord.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_farms = Farm.objects.filter(owner=self.request.user)
        
        # Calculate statistics
        if user_farms.exists():
            all_diagnoses = DiagnosisRecord.objects.filter(farm__in=user_farms)
        else:
            all_diagnoses = DiagnosisRecord.objects.none()
        
        context['total_diagnoses'] = all_diagnoses.count()
        context['confirmed_diagnoses'] = all_diagnoses.filter(status='confirmed').count()
        context['pending_diagnoses'] = all_diagnoses.filter(status='pending').count()
        context['cured_diagnoses'] = all_diagnoses.filter(status='cured').count()
        
        # Active alerts
        context['active_alerts'] = DiseaseAlert.objects.filter(
            is_active=True,
            expires_at__gt=timezone.now()
        ).order_by('-urgency_level')[:5]
        context['alerts_count'] = DiseaseAlert.objects.filter(
            is_active=True,
            expires_at__gt=timezone.now()
        ).count()
        
        # Most common diseases
        if user_farms.exists():
            context['most_common_diseases'] = DiseaseStatistics.objects.filter(
                farm__in=user_farms
            ).order_by('-total_diseases_detected')[:3]
        else:
            context['most_common_diseases'] = DiseaseStatistics.objects.none()
        
        return context


# ============================================================
# Diagnosis List View
# ============================================================

class DiagnosisListView(LoginRequiredMixin, ListView):
    """All diagnoses for user's farms"""
    template_name = 'disease/diagnosis_list.html'
    context_object_name = 'diagnoses'
    paginate_by = 20

    def get_queryset(self):
        user_farms = Farm.objects.filter(owner=self.request.user)
        if user_farms.exists():
            queryset = DiagnosisRecord.objects.filter(
                farm__in=user_farms
            ).select_related('disease', 'farm', 'crop').order_by('-detected_at')
        else:
            queryset = DiagnosisRecord.objects.none()
        
        # Apply filters
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(disease__name__icontains=search) |
                Q(farm__name__icontains=search)
            )
        
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_farms = Farm.objects.filter(owner=self.request.user)
        if user_farms.exists():
            all_diagnoses = DiagnosisRecord.objects.filter(farm__in=user_farms)
        else:
            all_diagnoses = DiagnosisRecord.objects.none()
        
        context['total_diagnoses'] = all_diagnoses.count()
        context['pending_count'] = all_diagnoses.filter(status='pending').count()
        context['confirmed_count'] = all_diagnoses.filter(status='confirmed').count()
        context['cured_count'] = all_diagnoses.filter(status='cured').count()
        
        return context


# ============================================================
# Disease Library View
# ============================================================

class DiseaseLibraryView(LoginRequiredMixin, ListView):
    """Browse all diseases"""
    template_name = 'disease/disease_library.html'
    context_object_name = 'diseases'
    paginate_by = 12

    def get_queryset(self):
        queryset = Disease.objects.all().select_related('category').prefetch_related(
            'symptom_set', 'treatmentoption_set', 'affected_crops'
        )
        
        # Apply filters
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category_id=category)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = DiseaseCategory.objects.all()
        return context


# ============================================================
# Disease Detail View
# ============================================================

class DiseaseDetailView(LoginRequiredMixin, DetailView):
    """Detailed disease information"""
    model = Disease
    template_name = 'disease/disease_detail.html'
    context_object_name = 'disease'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        disease = self.get_object()
        
        # Count diagnoses for this disease
        user_farms = Farm.objects.filter(owner=self.request.user)
        context['diagnosis_count'] = DiagnosisRecord.objects.filter(
            disease=disease,
            farm__in=user_farms
        ).count()
        
        return context


# ============================================================
# Diagnosis Create/Edit Views
# ============================================================

class DiagnosisCreateView(LoginRequiredMixin, CreateView):
    """Create new diagnosis"""
    model = DiagnosisRecord
    template_name = 'disease/diagnosis_form.html'
    fields = ['disease', 'farm', 'crop', 'status', 'confidence_score', 'description', 'severity_level']
    success_url = '/disease/diagnoses/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_farms = Farm.objects.filter(owner=self.request.user)
        
        context['farms'] = user_farms
        context['crops'] = CropType.objects.all()
        context['diseases'] = Disease.objects.all()
        context['has_farms'] = user_farms.exists()
        
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        
        # Handle environmental factors JSON
        env_data = {}
        if self.request.POST.get('environmental_factors_temperature'):
            env_data['temperature'] = float(self.request.POST.get('environmental_factors_temperature'))
        if self.request.POST.get('environmental_factors_humidity'):
            env_data['humidity'] = float(self.request.POST.get('environmental_factors_humidity'))
        if self.request.POST.get('environmental_factors_rainfall'):
            env_data['rainfall'] = float(self.request.POST.get('environmental_factors_rainfall'))
        form.instance.environmental_factors = env_data
        
        # Handle detected symptoms
        symptoms_text = self.request.POST.get('detected_symptoms', '')
        form.instance.detected_symptoms = [s.strip() for s in symptoms_text.split(',') if s.strip()]
        
        return super().form_valid(form)


class DiagnosisEditView(LoginRequiredMixin, UpdateView):
    """Edit existing diagnosis"""
    model = DiagnosisRecord
    template_name = 'disease/diagnosis_form.html'
    fields = ['disease', 'farm', 'crop', 'status', 'confidence_score', 'description', 'severity_level']
    success_url = '/disease/diagnoses/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_farms = Farm.objects.filter(owner=self.request.user)
        context['crops'] = CropType.objects.all()
        context['diseases'] = Disease.objects.all()
        context['farms'] = user_farms
        context['has_farms'] = user_farms.exists()
        return context

    def get_queryset(self):
        user_farms = Farm.objects.filter(owner=self.request.user)
        if user_farms.exists():
            return DiagnosisRecord.objects.filter(farm__in=user_farms)
        # If user has no farms (admin), show all diagnoses
        return DiagnosisRecord.objects.all()

    def form_valid(self, form):
        # Handle environmental factors JSON
        env_data = {}
        if self.request.POST.get('environmental_factors_temperature'):
            env_data['temperature'] = float(self.request.POST.get('environmental_factors_temperature'))
        if self.request.POST.get('environmental_factors_humidity'):
            env_data['humidity'] = float(self.request.POST.get('environmental_factors_humidity'))
        if self.request.POST.get('environmental_factors_rainfall'):
            env_data['rainfall'] = float(self.request.POST.get('environmental_factors_rainfall'))
        form.instance.environmental_factors = env_data
        
        # Handle detected symptoms
        symptoms_text = self.request.POST.get('detected_symptoms', '')
        form.instance.detected_symptoms = [s.strip() for s in symptoms_text.split(',') if s.strip()]
        
        return super().form_valid(form)


# ============================================================
# Diagnosis Detail View
# ============================================================

class DiagnosisDetailView(LoginRequiredMixin, DetailView):
    """Detailed diagnosis view"""
    model = DiagnosisRecord
    template_name = 'disease/diagnosis_detail.html'
    context_object_name = 'diagnosis'

    def get_queryset(self):
        user_farms = Farm.objects.filter(owner=self.request.user)
        if user_farms.exists():
            return DiagnosisRecord.objects.filter(farm__in=user_farms)
        # If user has no farms (admin), show all diagnoses
        return DiagnosisRecord.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        diagnosis = self.get_object()
        
        # Get treatment plan
        context['treatment_plan'] = DiseaseService.get_treatment_plan(diagnosis)
        
        # Calculate days since diagnosis
        context['days_since'] = (timezone.now() - diagnosis.detected_at).days
        
        # Get status history
        context['status_history'] = DiagnosisHistory.objects.filter(
            diagnosis=diagnosis
        ).order_by('-changed_at')
        
        return context


# ============================================================
# Disease Alerts View
# ============================================================

class DiseaseAlertsView(LoginRequiredMixin, ListView):
    """Active disease alerts"""
    template_name = 'disease/alerts.html'
    context_object_name = 'alerts'
    paginate_by = 20

    def get_queryset(self):
        queryset = DiseaseAlert.objects.select_related('disease').prefetch_related('affected_crops').order_by('-issued_at')
        
        # Apply filters
        alert_type = self.request.GET.get('type')
        if alert_type:
            queryset = queryset.filter(alert_type=alert_type)
        
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(
                is_active=True,
                expires_at__gt=timezone.now()
            )
        elif status == 'expired':
            queryset = queryset.filter(
                Q(is_active=False) | Q(expires_at__lte=timezone.now())
            )
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        all_alerts = DiseaseAlert.objects.all()
        context['total_alerts'] = all_alerts.count()
        context['outbreak_count'] = all_alerts.filter(alert_type='outbreak').count()
        context['warning_count'] = all_alerts.filter(alert_type='warning').count()
        
        return context


# ============================================================
# Diagnosis Report View
# ============================================================

def diagnosis_report_view(request, pk):
    """Generate diagnosis PDF report"""
    diagnosis = get_object_or_404(DiagnosisRecord, pk=pk)
    user_farms = Farm.objects.filter(owner=request.user)
    
    # Check permission - allow if user has no farms (admin) or owns the farm
    if user_farms.exists() and diagnosis.farm not in user_farms:
        return redirect('/disease/diagnoses/')
    
    treatment_plan = DiseaseService.get_treatment_plan(diagnosis)
    
    context = {
        'diagnosis': diagnosis,
        'treatment_plan': treatment_plan,
        'generated_at': timezone.now(),
    }
    
    return render(request, 'disease/diagnosis_report.html', context)
