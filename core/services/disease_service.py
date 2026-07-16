# core/services/disease_service.py
# Disease diagnosis and treatment recommendation service

from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User
from core.models_disease import (
    Disease, Symptom, DiagnosisRecord, TreatmentOption,
    DiagnosisHistory, DiseaseAlert, DiseaseStatistics, DiseaseCategory
)
from core.models import Farm, CropType
import logging
import json

logger = logging.getLogger(__name__)


class DiseaseService:
    """Service for disease diagnosis and treatment"""
    
    @staticmethod
    def diagnose_from_symptoms(farm: Farm, crop: CropType, symptoms: list, 
                               environmental_factors: dict = None) -> list:
        """Diagnose diseases based on symptoms"""
        try:
            if environmental_factors is None:
                environmental_factors = {}
            
            # Match symptoms to diseases
            disease_matches = {}
            
            for symptom_name in symptoms:
                matching_symptoms = Symptom.objects.filter(
                    name__icontains=symptom_name
                ).select_related('disease')
                
                for symptom in matching_symptoms:
                    disease = symptom.disease
                    if disease.id not in disease_matches:
                        disease_matches[disease.id] = {
                            'disease': disease,
                            'matched_symptoms': [],
                            'confidence': 0.0,
                            'primary_symptoms': 0
                        }
                    
                    disease_matches[disease.id]['matched_symptoms'].append(symptom.name)
                    if symptom.is_primary_symptom:
                        disease_matches[disease.id]['primary_symptoms'] += 1
            
            # Calculate confidence scores
            results = []
            for disease_data in disease_matches.values():
                disease = disease_data['disease']
                matched_count = len(disease_data['matched_symptoms'])
                total_symptoms = disease.symptoms.count()
                primary_count = disease_data['primary_symptoms']
                
                # Confidence calculation
                confidence = (matched_count / total_symptoms * 100) if total_symptoms > 0 else 0
                if primary_count > 0:
                    confidence *= 1.2  # Boost for primary symptoms
                
                confidence = min(100, confidence)  # Cap at 100%
                
                disease_data['confidence'] = confidence
                results.append(disease_data)
            
            # Sort by confidence
            results.sort(key=lambda x: x['confidence'], reverse=True)
            
            return results[:5]  # Return top 5 matches
        
        except Exception as e:
            logger.error(f"Error diagnosing symptoms: {str(e)}")
            return []
    
    @staticmethod
    def create_diagnosis(user: User, farm: Farm, crop: CropType, disease: Disease,
                        symptoms: list, severity: str, description: str,
                        confidence: float = 0.0, environmental_factors: dict = None,
                        location: str = None, image_url: str = None) -> DiagnosisRecord:
        """Create a diagnosis record"""
        try:
            if environmental_factors is None:
                environmental_factors = {}
            
            diagnosis = DiagnosisRecord.objects.create(
                user=user,
                farm=farm,
                crop=crop,
                disease=disease,
                detected_symptoms=symptoms,
                severity_level=severity,
                confidence_score=confidence,
                description=description,
                environmental_factors=environmental_factors,
                location_in_field=location,
                image_url=image_url,
                status='pending'
            )
            
            logger.info(f"Created diagnosis for {disease.name} on {farm.name}")
            return diagnosis
        
        except Exception as e:
            logger.error(f"Error creating diagnosis: {str(e)}")
            raise
    
    @staticmethod
    def recommend_treatment(diagnosis: DiagnosisRecord) -> TreatmentOption:
        """Recommend best treatment based on severity and stage"""
        try:
            # Map severity to stage
            severity_to_stage = {
                'mild': 'prevention',
                'moderate': 'early',
                'severe': 'moderate',
                'critical': 'severe'
            }
            
            stage = severity_to_stage.get(diagnosis.severity_level, 'prevention')
            
            # Get treatments ordered by effectiveness
            treatments = TreatmentOption.objects.filter(
                disease=diagnosis.disease,
                applicable_stage=stage
            ).order_by('-effectiveness_percent')
            
            if treatments.exists():
                recommended = treatments.first()
                diagnosis.recommended_treatment = recommended
                diagnosis.save()
                return recommended
            
            return None
        
        except Exception as e:
            logger.error(f"Error recommending treatment: {str(e)}")
            return None
    
    @staticmethod
    def get_treatment_plan(diagnosis: DiagnosisRecord) -> dict:
        """Get comprehensive treatment plan"""
        try:
            treatment = diagnosis.recommended_treatment
            
            if not treatment:
                treatment = DiseaseService.recommend_treatment(diagnosis)
            
            if not treatment:
                return None
            
            return {
                'treatment_name': treatment.name,
                'treatment_type': treatment.get_treatment_type_display(),
                'description': treatment.description,
                'active_ingredient': treatment.active_ingredient,
                'dosage': treatment.dosage,
                'application_method': treatment.application_method,
                'frequency': treatment.frequency,
                'duration_days': treatment.duration_days,
                'effectiveness': treatment.effectiveness_percent,
                'cost_per_hectare': float(treatment.cost_per_hectare or 0),
                'precautions': treatment.precautions,
                're_entry_hours': treatment.re_entry_hours,
                'harvest_waiting_days': treatment.harvest_waiting_days,
                'is_organic': treatment.is_organic_approved,
                'stage': treatment.get_applicable_stage_display()
            }
        
        except Exception as e:
            logger.error(f"Error getting treatment plan: {str(e)}")
            return None
    
    @staticmethod
    def update_diagnosis_status(diagnosis: DiagnosisRecord, new_status: str,
                               notes: str, changed_by: User = None) -> DiagnosisHistory:
        """Update diagnosis status with history tracking"""
        try:
            old_status = diagnosis.status
            
            # Create history record
            history = DiagnosisHistory.objects.create(
                diagnosis=diagnosis,
                status_before=old_status,
                status_after=new_status,
                notes=notes,
                changed_by=changed_by
            )
            
            # Update diagnosis
            diagnosis.status = new_status
            if new_status == 'cured':
                diagnosis.resolved_at = timezone.now()
            diagnosis.save()
            
            logger.info(f"Updated diagnosis {diagnosis.id} status: {old_status} → {new_status}")
            return history
        
        except Exception as e:
            logger.error(f"Error updating diagnosis: {str(e)}")
            raise
    
    @staticmethod
    def get_similar_diseases(disease: Disease, limit: int = 5) -> list:
        """Get similar diseases based on category and symptoms"""
        try:
            # Get diseases in same category
            similar = Disease.objects.filter(
                category=disease.category
            ).exclude(id=disease.id)[:limit]
            
            return list(similar)
        
        except Exception as e:
            logger.error(f"Error getting similar diseases: {str(e)}")
            return []
    
    @staticmethod
    def check_quarantine_requirements(disease: Disease) -> dict:
        """Check if quarantine is needed"""
        return {
            'is_required': disease.is_quarantine_required,
            'quarantine_days': disease.quarantine_days,
            'procedures': [
                'Isolate affected plants',
                'Disinfect tools and equipment',
                'Monitor nearby plants closely',
                'Implement sanitation protocols'
            ] if disease.is_quarantine_required else []
        }
    
    @staticmethod
    def get_disease_prevention_measures(disease: Disease) -> list:
        """Get prevention measures for a disease"""
        try:
            # Get prevention stage treatments
            prevention_measures = TreatmentOption.objects.filter(
                disease=disease,
                applicable_stage='prevention'
            ).values('name', 'description', 'active_ingredient', 'application_method')
            
            return list(prevention_measures)
        
        except Exception as e:
            logger.error(f"Error getting prevention measures: {str(e)}")
            return []
    
    @staticmethod
    def create_disease_alert(disease: Disease, title: str, description: str,
                            alert_type: str, regions: list, crops: list,
                            recommended_actions: str, urgency: int = 5) -> DiseaseAlert:
        """Create a disease alert"""
        try:
            expires_at = timezone.now() + timedelta(days=30)
            
            alert = DiseaseAlert.objects.create(
                disease=disease,
                title=title,
                description=description,
                alert_type=alert_type,
                affected_regions=regions,
                recommended_actions=recommended_actions,
                urgency_level=urgency,
                expires_at=expires_at
            )
            
            # Add crops to alert
            if crops:
                alert.affected_crops.set(crops)
            
            logger.info(f"Created alert for {disease.name}")
            return alert
        
        except Exception as e:
            logger.error(f"Error creating alert: {str(e)}")
            raise
    
    @staticmethod
    def get_active_alerts() -> list:
        """Get active disease alerts"""
        return DiseaseAlert.objects.filter(
            is_active=True,
            expires_at__gt=timezone.now()
        ).order_by('-urgency_level')
    
    @staticmethod
    def calculate_disease_statistics(farm: Farm, crop: CropType = None) -> DiseaseStatistics:
        """Calculate disease statistics for farm"""
        try:
            today = timezone.now().date()
            
            # Get diagnoses for period
            diagnoses = DiagnosisRecord.objects.filter(
                farm=farm,
                detected_at__date=today
            )
            
            if crop:
                diagnoses = diagnoses.filter(crop=crop)
            
            # Calculate stats
            total = diagnoses.count()
            confirmed = diagnoses.filter(status='confirmed').count()
            cured = diagnoses.filter(status='cured').count()
            
            # Most common disease
            most_common = None
            severity_sum = 0
            
            disease_counts = {}
            for diagnosis in diagnoses:
                disease_id = diagnosis.disease.id
                disease_counts[disease_id] = disease_counts.get(disease_id, 0) + 1
                
                # Convert severity to numeric
                severity_map = {'mild': 1, 'moderate': 2, 'severe': 3, 'critical': 4}
                severity_sum += severity_map.get(diagnosis.severity_level, 0)
            
            if disease_counts:
                most_common_id = max(disease_counts, key=disease_counts.get)
                most_common = Disease.objects.get(id=most_common_id)
            
            avg_severity = (severity_sum / total) if total > 0 else 0
            
            # Treatment success rate
            total_cured = diagnoses.filter(status='cured').count()
            treated = diagnoses.exclude(recommended_treatment=None).count()
            success_rate = (total_cured / treated * 100) if treated > 0 else 0
            
            # Create or update stats
            stats, created = DiseaseStatistics.objects.update_or_create(
                farm=farm,
                crop=crop,
                date=today,
                defaults={
                    'total_diseases_detected': total,
                    'confirmed_diseases': confirmed,
                    'cured_diseases': cured,
                    'most_common_disease': most_common,
                    'average_severity': avg_severity,
                    'treatment_success_rate': success_rate
                }
            )
            
            return stats
        
        except Exception as e:
            logger.error(f"Error calculating statistics: {str(e)}")
            return None
    
    @staticmethod
    def get_disease_timeline(farm: Farm) -> list:
        """Get timeline of diagnoses for farm"""
        diagnoses = DiagnosisRecord.objects.filter(
            farm=farm
        ).order_by('-detected_at')[:20]
        
        timeline = []
        for diagnosis in diagnoses:
            timeline.append({
                'date': diagnosis.detected_at,
                'disease': diagnosis.disease.name,
                'severity': diagnosis.severity_level,
                'status': diagnosis.status,
                'confidence': diagnosis.confidence_score,
                'crop': diagnosis.crop.name if diagnosis.crop else 'Unknown'
            })
        
        return timeline
    
    @staticmethod
    def export_diagnosis_report(diagnosis: DiagnosisRecord) -> dict:
        """Export comprehensive diagnosis report"""
        try:
            treatment_plan = DiseaseService.get_treatment_plan(diagnosis)
            quarantine_info = DiseaseService.check_quarantine_requirements(diagnosis.disease)
            prevention = DiseaseService.get_disease_prevention_measures(diagnosis.disease)
            similar = DiseaseService.get_similar_diseases(diagnosis.disease)
            
            return {
                'diagnosis_id': diagnosis.id,
                'disease': diagnosis.disease.name,
                'farm': diagnosis.farm.name,
                'crop': diagnosis.crop.name if diagnosis.crop else 'N/A',
                'detected_at': diagnosis.detected_at.isoformat(),
                'severity': diagnosis.severity_level,
                'confidence': diagnosis.confidence_score,
                'symptoms': diagnosis.detected_symptoms,
                'status': diagnosis.status,
                'description': diagnosis.description,
                'treatment_plan': treatment_plan,
                'quarantine_required': quarantine_info,
                'prevention_measures': prevention,
                'similar_diseases': [d.name for d in similar],
                'environmental_factors': diagnosis.environmental_factors,
                'expert_verified': diagnosis.verified_by_expert
            }
        
        except Exception as e:
            logger.error(f"Error exporting report: {str(e)}")
            return None
