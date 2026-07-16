# core/api/views_disease.py
# Disease diagnosis API views

from rest_framework import viewsets, status, views
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
import logging

from core.models_disease import (
    DiseaseCategory, Disease, Symptom, TreatmentOption,
    DiagnosisRecord, DiagnosisHistory, DiseaseAlert, DiseaseStatistics
)
from core.api.serializers_disease import (
    DiseaseCategorySerializer, DiseaseSerializer, SymptomSerializer,
    TreatmentOptionSerializer, DiagnosisRecordSerializer, DiagnosisDetailSerializer,
    DiagnosisHistorySerializer, DiseaseAlertSerializer, DiseaseStatisticsSerializer
)
from core.services.disease_service import DiseaseService
from core.models import Farm, CropType

logger = logging.getLogger(__name__)


class DiseaseCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """Browse disease categories"""
    queryset = DiseaseCategory.objects.all()
    serializer_class = DiseaseCategorySerializer
    permission_classes = [IsAuthenticated]


class DiseaseViewSet(viewsets.ReadOnlyModelViewSet):
    """Browse disease catalog"""
    queryset = Disease.objects.prefetch_related('symptoms', 'treatments')
    serializer_class = DiseaseSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['category']
    search_fields = ['name', 'scientific_name']
    
    @action(detail=True, methods=['get'])
    def treatment_plan(self, request, pk=None):
        """Get treatment recommendations for a disease"""
        disease = self.get_object()
        treatments = TreatmentOption.objects.filter(disease=disease).order_by('-effectiveness_percent')
        
        serializer = TreatmentOptionSerializer(treatments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def prevention_measures(self, request, pk=None):
        """Get prevention measures"""
        disease = self.get_object()
        measures = DiseaseService.get_disease_prevention_measures(disease)
        return Response(measures)
    
    @action(detail=True, methods=['get'])
    def quarantine_info(self, request, pk=None):
        """Get quarantine requirements"""
        disease = self.get_object()
        info = DiseaseService.check_quarantine_requirements(disease)
        return Response(info)
    
    @action(detail=True, methods=['get'])
    def similar_diseases(self, request, pk=None):
        """Get similar diseases"""
        disease = self.get_object()
        similar = DiseaseService.get_similar_diseases(disease)
        
        serializer = self.get_serializer(similar, many=True)
        return Response(serializer.data)


class SymptomViewSet(viewsets.ReadOnlyModelViewSet):
    """Browse disease symptoms"""
    queryset = Symptom.objects.select_related('disease')
    serializer_class = SymptomSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['disease', 'affected_body_part', 'severity_indicator']
    search_fields = ['name', 'description']


class TreatmentOptionViewSet(viewsets.ReadOnlyModelViewSet):
    """Browse treatment options"""
    queryset = TreatmentOption.objects.select_related('disease')
    serializer_class = TreatmentOptionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['disease', 'treatment_type', 'applicable_stage']
    ordering_fields = ['effectiveness_percent', 'cost_per_hectare']


class DiagnosisRecordViewSet(viewsets.ModelViewSet):
    """Manage diagnosis records"""
    permission_classes = [IsAuthenticated]
    filterset_fields = ['farm', 'status', 'disease']
    ordering_fields = ['detected_at', 'confidence_score', 'severity_level']
    
    def get_queryset(self):
        """Filter diagnoses for current user"""
        return DiagnosisRecord.objects.filter(
            user=self.request.user
        ).select_related('disease', 'farm', 'crop').order_by('-detected_at')
    
    def get_serializer_class(self):
        """Use detail serializer for retrieve"""
        if self.action == 'retrieve':
            return DiagnosisDetailSerializer
        return DiagnosisRecordSerializer
    
    @action(detail=False, methods=['post'])
    def diagnose_from_symptoms(self, request):
        """Diagnose disease from symptom list"""
        try:
            farm_id = request.data.get('farm_id')
            crop_id = request.data.get('crop_id')
            symptoms = request.data.get('symptoms', [])
            environmental_factors = request.data.get('environmental_factors', {})
            
            farm = Farm.objects.get(id=farm_id, owner=request.user)
            crop = CropType.objects.get(id=crop_id) if crop_id else None
            
            # Get diagnosis matches
            matches = DiseaseService.diagnose_from_symptoms(
                farm, crop, symptoms, environmental_factors
            )
            
            result = []
            for match in matches:
                result.append({
                    'disease_id': match['disease'].id,
                    'disease_name': match['disease'].name,
                    'confidence': match['confidence'],
                    'matched_symptoms': match['matched_symptoms'],
                    'primary_symptoms': match['primary_symptoms']
                })
            
            return Response({
                'matches': result,
                'total_matches': len(result)
            })
        
        except Exception as e:
            logger.error(f"Error diagnosing: {str(e)}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def create_diagnosis(self, request):
        """Create a new diagnosis"""
        try:
            farm_id = request.data.get('farm_id')
            crop_id = request.data.get('crop_id')
            disease_id = request.data.get('disease_id')
            symptoms = request.data.get('symptoms', [])
            severity = request.data.get('severity', 'moderate')
            description = request.data.get('description', '')
            confidence = float(request.data.get('confidence', 0.0))
            location = request.data.get('location')
            image_url = request.data.get('image_url')
            environmental_factors = request.data.get('environmental_factors', {})
            
            farm = Farm.objects.get(id=farm_id, owner=request.user)
            crop = CropType.objects.get(id=crop_id) if crop_id else None
            disease = Disease.objects.get(id=disease_id)
            
            diagnosis = DiseaseService.create_diagnosis(
                user=request.user,
                farm=farm,
                crop=crop,
                disease=disease,
                symptoms=symptoms,
                severity=severity,
                description=description,
                confidence=confidence,
                environmental_factors=environmental_factors,
                location=location,
                image_url=image_url
            )
            
            # Recommend treatment
            DiseaseService.recommend_treatment(diagnosis)
            
            serializer = self.get_serializer(diagnosis)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            logger.error(f"Error creating diagnosis: {str(e)}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def treatment_plan(self, request, pk=None):
        """Get treatment plan for diagnosis"""
        diagnosis = self.get_object()
        plan = DiseaseService.get_treatment_plan(diagnosis)
        
        if plan:
            return Response(plan)
        else:
            return Response({
                'error': 'No treatment plan available'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update diagnosis status"""
        diagnosis = self.get_object()
        new_status = request.data.get('status')
        notes = request.data.get('notes', '')
        
        try:
            history = DiseaseService.update_diagnosis_status(
                diagnosis, new_status, notes, request.user
            )
            
            serializer = DiagnosisHistorySerializer(history)
            return Response(serializer.data)
        
        except Exception as e:
            logger.error(f"Error updating status: {str(e)}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def report(self, request, pk=None):
        """Export diagnosis report"""
        diagnosis = self.get_object()
        report = DiseaseService.export_diagnosis_report(diagnosis)
        
        if report:
            return Response(report)
        else:
            return Response({
                'error': 'Could not generate report'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def farm_timeline(self, request):
        """Get diagnosis timeline for farm"""
        farm_id = request.query_params.get('farm_id')
        if not farm_id:
            return Response({
                'error': 'farm_id parameter required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        farm = Farm.objects.get(id=farm_id, owner=request.user)
        timeline = DiseaseService.get_disease_timeline(farm)
        
        return Response({'timeline': timeline})


class DiagnosisHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """View diagnosis history"""
    serializer_class = DiagnosisHistorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter history for user's diagnoses"""
        return DiagnosisHistory.objects.filter(
            diagnosis__user=self.request.user
        ).order_by('-changed_at')


class DiseaseAlertViewSet(viewsets.ReadOnlyModelViewSet):
    """Browse disease alerts"""
    queryset = DiseaseAlert.objects.filter(is_active=True)
    serializer_class = DiseaseAlertSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['disease', 'alert_type']
    ordering_fields = ['urgency_level', 'issued_at']
    
    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """Mark alert as acknowledged"""
        alert = self.get_object()
        alert.is_active = False
        alert.save()
        return Response({'status': 'acknowledged', 'alert_id': alert.id})


class DiseaseStatisticsViewSet(viewsets.ReadOnlyModelViewSet):
    """View disease statistics"""
    serializer_class = DiseaseStatisticsSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['farm', 'crop', 'date']
    ordering_fields = ['date']
    
    def get_queryset(self):
        """Filter statistics for user's farms"""
        return DiseaseStatistics.objects.filter(
            farm__owner=self.request.user
        ).order_by('-date')
    
    @action(detail=False, methods=['post'])
    def calculate(self, request):
        """Calculate statistics for a farm"""
        farm_id = request.data.get('farm_id')
        crop_id = request.data.get('crop_id')
        
        try:
            farm = Farm.objects.get(id=farm_id, owner=request.user)
            crop = CropType.objects.get(id=crop_id) if crop_id else None
            
            stats = DiseaseService.calculate_disease_statistics(farm, crop)
            
            if stats:
                serializer = self.get_serializer(stats)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'error': 'Could not calculate statistics'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.error(f"Error calculating statistics: {str(e)}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class DiseaseDashboardView(views.APIView):
    """Disease diagnosis dashboard"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get disease dashboard data"""
        try:
            from django.utils import timezone
            from django.db.models import Count, Q
            
            # Recent diagnoses
            recent_diagnoses = DiagnosisRecord.objects.filter(
                user=request.user
            ).order_by('-detected_at')[:10]
            
            # Active alerts
            active_alerts = DiseaseService.get_active_alerts()[:5]
            
            # Statistics summary
            all_diagnoses = DiagnosisRecord.objects.filter(user=request.user)
            total_confirmed = all_diagnoses.filter(status='confirmed').count()
            total_cured = all_diagnoses.filter(status='cured').count()
            
            # Most common diseases
            disease_counts = all_diagnoses.values('disease__name').annotate(
                count=Count('id')
            ).order_by('-count')[:5]
            
            return Response({
                'total_diagnoses': all_diagnoses.count(),
                'confirmed_diagnoses': total_confirmed,
                'cured_diagnoses': total_cured,
                'pending_diagnoses': all_diagnoses.filter(status='pending').count(),
                'recent_diagnoses': DiagnosisRecordSerializer(recent_diagnoses, many=True).data,
                'active_alerts': DiseaseAlertSerializer(active_alerts, many=True).data,
                'most_common_diseases': list(disease_counts),
                'alerts_count': DiseaseAlert.objects.filter(is_active=True).count()
            })
        
        except Exception as e:
            logger.error(f"Error loading disease dashboard: {str(e)}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
