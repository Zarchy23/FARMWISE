# core/management/commands/populate_disease_data.py
# Populate disease database with sample diseases, symptoms, and treatments

from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models_disease import (
    DiseaseCategory, Disease, Symptom, TreatmentOption,
    DiseaseAlert
)
from core.models import CropType


class Command(BaseCommand):
    help = 'Populate disease database with sample data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sample',
            action='store_true',
            help='Load sample disease data',
        )
        parser.add_argument(
            '--full',
            action='store_true',
            help='Load comprehensive disease data',
        )

    def handle(self, *args, **options):
        sample = options.get('sample', False)
        full = options.get('full', False)

        if not sample and not full:
            sample = True  # Default to sample

        if sample:
            self.load_sample_diseases()
        elif full:
            self.load_full_diseases()

    def load_sample_diseases(self):
        """Load sample diseases for demonstration"""
        self.stdout.write("Loading sample disease data...")

        # Create categories
        fungal, _ = DiseaseCategory.objects.get_or_create(
            name='Fungal',
            category_type='fungal',
            defaults={'description': 'Fungal diseases caused by fungal pathogens'}
        )
        bacterial, _ = DiseaseCategory.objects.get_or_create(
            name='Bacterial',
            category_type='bacterial',
            defaults={'description': 'Bacterial diseases caused by bacterial pathogens'}
        )
        viral, _ = DiseaseCategory.objects.get_or_create(
            name='Viral',
            category_type='viral',
            defaults={'description': 'Viral diseases caused by viral pathogens'}
        )

        # Get crops
        tomato = CropType.objects.filter(name__icontains='tomato').first()
        rice = CropType.objects.filter(name__icontains='rice').first()
        maize = CropType.objects.filter(name__icontains='maize').first()
        bean = CropType.objects.filter(name__icontains='bean').first()

        # Disease 1: Tomato Early Blight (Fungal)
        early_blight, created = Disease.objects.get_or_create(
            name='Early Blight',
            category=fungal,
            defaults={
                'scientific_name': 'Alternaria solani',
                'description': 'Fungal disease affecting tomato and potato causing brown spots on leaves',
                'initial_severity': 'moderate',
                'progression_rate': 7,
                'is_quarantine_required': False,
            }
        )
        if tomato and created:
            early_blight.affected_crops.add(tomato)

        # Symptoms for Early Blight
        symptoms_early_blight = [
            {
                'name': 'Brown spots with rings',
                'affected_body_part': 'leaf',
                'severity_indicator': 'moderate',
                'is_primary_symptom': True,
            },
            {
                'name': 'Yellow halo around spots',
                'affected_body_part': 'leaf',
                'severity_indicator': 'mild',
                'is_primary_symptom': False,
            },
            {
                'name': 'Stem cankers',
                'affected_body_part': 'stem',
                'severity_indicator': 'severe',
                'is_primary_symptom': False,
            }
        ]
        for symptom_data in symptoms_early_blight:
            Symptom.objects.get_or_create(
                disease=early_blight,
                name=symptom_data['name'],
                defaults={
                    'description': f"Symptom: {symptom_data['name']}",
                    'affected_body_part': symptom_data['affected_body_part'],
                    'severity_indicator': symptom_data['severity_indicator'],
                    'is_primary_symptom': symptom_data['is_primary_symptom'],
                    'keywords': symptom_data['name'].lower().split()
                }
            )

        # Treatments for Early Blight
        treatments_early_blight = [
            {
                'name': 'Preventive Fungicide Spray',
                'treatment_type': 'chemical',
                'applicable_stage': 'prevention',
                'description': 'Copper-based spray for prevention',
                'active_ingredient': 'Copper Oxychloride',
                'dosage': '2.5 kg per hectare',
                'application_method': 'spray',
                'frequency': 'Every 10-14 days',
                'duration_days': 14,
                'effectiveness_percent': 85,
                'cost_per_hectare': 2500,
                'harvest_waiting_days': 14,
                'is_organic_approved': True,
            },
            {
                'name': 'Curative Mancozeb Application',
                'treatment_type': 'chemical',
                'applicable_stage': 'early',
                'description': 'Mancozeb spray for early infection',
                'active_ingredient': 'Mancozeb 75%',
                'dosage': '2 kg per hectare',
                'application_method': 'spray',
                'frequency': 'Every 10 days',
                'duration_days': 21,
                'effectiveness_percent': 75,
                'cost_per_hectare': 3000,
                'harvest_waiting_days': 21,
                'is_organic_approved': False,
            },
            {
                'name': 'Severe Infection - Carbendazim',
                'treatment_type': 'chemical',
                'applicable_stage': 'severe',
                'description': 'Strong systemic fungicide for severe cases',
                'active_ingredient': 'Carbendazim 50%',
                'dosage': '0.5 kg per hectare',
                'application_method': 'spray',
                'frequency': 'Every 7 days',
                'duration_days': 30,
                'effectiveness_percent': 95,
                'cost_per_hectare': 5000,
                'harvest_waiting_days': 30,
                'is_organic_approved': False,
            }
        ]
        for treatment_data in treatments_early_blight:
            TreatmentOption.objects.get_or_create(
                disease=early_blight,
                name=treatment_data['name'],
                defaults=treatment_data
            )

        # Disease 2: Rice Blast (Fungal)
        if rice:
            rice_blast, created = Disease.objects.get_or_create(
                name='Rice Blast',
                category=fungal,
                defaults={
                    'scientific_name': 'Magnaporthe grisea',
                    'description': 'Serious fungal disease of rice causing spore-producing lesions',
                    'initial_severity': 'severe',
                    'progression_rate': 5,
                    'is_quarantine_required': True,
                }
            )
            if created:
                rice_blast.affected_crops.add(rice)

            symptoms_rice_blast = [
                {
                    'name': 'Diamond-shaped lesions',
                    'affected_body_part': 'leaf',
                    'severity_indicator': 'severe',
                    'is_primary_symptom': True,
                },
                {
                    'name': 'Grayish center with brown border',
                    'affected_body_part': 'leaf',
                    'severity_indicator': 'moderate',
                    'is_primary_symptom': False,
                },
                {
                    'name': 'Panicle rot',
                    'affected_body_part': 'panicle',
                    'severity_indicator': 'severe',
                    'is_primary_symptom': False,
                }
            ]
            for symptom_data in symptoms_rice_blast:
                Symptom.objects.get_or_create(
                    disease=rice_blast,
                    name=symptom_data['name'],
                    defaults={
                        'description': f"Symptom: {symptom_data['name']}",
                        'affected_body_part': symptom_data['affected_body_part'],
                        'severity_indicator': symptom_data['severity_indicator'],
                        'is_primary_symptom': symptom_data['is_primary_symptom'],
                        'keywords': symptom_data['name'].lower().split()
                    }
                )

        # Disease 3: Bacterial Wilt (Bacterial)
        if maize:
            bacterial_wilt, created = Disease.objects.get_or_create(
                name='Bacterial Wilt',
                category=bacterial,
                defaults={
                    'scientific_name': 'Xanthomonas vasicola',
                    'description': 'Bacterial disease causing wilting and leaf streaking',
                    'initial_severity': 'moderate',
                    'progression_rate': 10,
                    'is_quarantine_required': False,
                }
            )
            if created:
                bacterial_wilt.affected_crops.add(maize)

        # Disease 4: Viral Mosaic (Viral)
        if bean:
            viral_mosaic, created = Disease.objects.get_or_create(
                name='Bean Common Mosaic Virus',
                category=viral,
                defaults={
                    'scientific_name': 'BCMV',
                    'description': 'Viral disease causing mosaic patterns on leaves',
                    'initial_severity': 'mild',
                    'progression_rate': 14,
                    'is_quarantine_required': False,
                }
            )
            if created:
                viral_mosaic.affected_crops.add(bean)

        # Create alerts
        DiseaseAlert.objects.get_or_create(
            disease=early_blight,
            title='Early Blight Outbreak - Region X',
            defaults={
                'description': 'Reports of early blight in tomato fields in Region X',
                'alert_type': 'outbreak',
                'urgency_level': 8,
                'is_active': True,
                'expires_at': timezone.now() + timedelta(days=30),
                'recommended_actions': 'Apply preventive fungicides, remove infected leaves'
            }
        )

        self.stdout.write(self.style.SUCCESS(
            f'Successfully loaded sample disease data: '
            f'{Disease.objects.count()} diseases, '
            f'{Symptom.objects.count()} symptoms, '
            f'{TreatmentOption.objects.count()} treatments'
        ))

    def load_full_diseases(self):
        """Load comprehensive disease database"""
        self.stdout.write("Loading comprehensive disease data...")
        # Extended implementation would go here
        self.load_sample_diseases()
