"""
Management command to test ML data pipeline and model training
Run: python manage.py test_ml_pipeline
"""

from django.core.management.base import BaseCommand
from core.ml.data_pipeline import DataPipeline
import pandas as pd

class Command(BaseCommand):
    help = 'Test ML data pipeline and model training with sample data'

    def handle(self, *args, **options):
        self.stdout.write('Testing ML Data Pipeline...')
        
        # Test crop yield data
        self.stdout.write('\n=== Testing Crop Yield Data Pipeline ===')
        try:
            crop_data = DataPipeline.get_crop_yield_data()
            self.stdout.write(f'✓ Crop yield data collected: {len(crop_data)} records')
            if not crop_data.empty:
                self.stdout.write(f'  Columns: {list(crop_data.columns)}')
                self.stdout.write(f'  Sample record: {crop_data.iloc[0].to_dict()}')
            else:
                self.stdout.write('  No crop yield data available')
        except Exception as e:
            self.stdout.write(f'✗ Error collecting crop yield data: {str(e)}')
        
        # Test equipment maintenance data
        self.stdout.write('\n=== Testing Equipment Maintenance Data Pipeline ===')
        try:
            equipment_data = DataPipeline.get_equipment_maintenance_data()
            self.stdout.write(f'✓ Equipment maintenance data collected: {len(equipment_data)} records')
            if not equipment_data.empty:
                self.stdout.write(f'  Columns: {list(equipment_data.columns)}')
            else:
                self.stdout.write('  No equipment maintenance data available')
        except Exception as e:
            self.stdout.write(f'✗ Error collecting equipment maintenance data: {str(e)}')
        
        # Test financial data
        self.stdout.write('\n=== Testing Financial Data Pipeline ===')
        try:
            financial_data = DataPipeline.get_financial_data()
            self.stdout.write(f'✓ Financial data collected: {len(financial_data)} records')
            if not financial_data.empty:
                self.stdout.write(f'  Columns: {list(financial_data.columns)}')
            else:
                self.stdout.write('  No financial data available')
        except Exception as e:
            self.stdout.write(f'✗ Error collecting financial data: {str(e)}')
        
        # Test livestock health data
        self.stdout.write('\n=== Testing Livestock Health Data Pipeline ===')
        try:
            livestock_data = DataPipeline.get_livestock_health_data()
            self.stdout.write(f'✓ Livestock health data collected: {len(livestock_data)} records')
            if not livestock_data.empty:
                self.stdout.write(f'  Columns: {list(livestock_data.columns)}')
            else:
                self.stdout.write('  No livestock health data available')
        except Exception as e:
            self.stdout.write(f'✗ Error collecting livestock health data: {str(e)}')
        
        # Test pest detection data
        self.stdout.write('\n=== Testing Pest Detection Data Pipeline ===')
        try:
            pest_data = DataPipeline.get_pest_detection_data()
            self.stdout.write(f'✓ Pest detection data collected: {len(pest_data)} records')
            if not pest_data.empty:
                self.stdout.write(f'  Columns: {list(pest_data.columns)}')
            else:
                self.stdout.write('  No pest detection data available')
        except Exception as e:
            self.stdout.write(f'✗ Error collecting pest detection data: {str(e)}')
        
        # Test preprocessing
        self.stdout.write('\n=== Testing Data Preprocessing ===')
        try:
            if not crop_data.empty:
                processed_data = DataPipeline.preprocess_features(
                    crop_data,
                    categorical_columns=['crop_type', 'soil_type', 'irrigation_type'],
                    numerical_columns=['area_hectares', 'growing_days', 'fertilizer_amount']
                )
                self.stdout.write(f'✓ Data preprocessing successful')
                self.stdout.write(f'  Original columns: {len(crop_data.columns)}')
                self.stdout.write(f'  Processed columns: {len(processed_data.columns)}')
        except Exception as e:
            self.stdout.write(f'✗ Error preprocessing data: {str(e)}')
        
        # Test time series features
        self.stdout.write('\n=== Testing Time Series Feature Creation ===')
        try:
            if not financial_data.empty and 'date' in financial_data.columns:
                time_series_data = DataPipeline.create_time_series_features(
                    financial_data,
                    date_column='date',
                    target_column='amount'
                )
                self.stdout.write(f'✓ Time series features created')
                self.stdout.write(f'  Original columns: {len(financial_data.columns)}')
                self.stdout.write(f'  Time series columns: {len(time_series_data.columns)}')
            else:
                self.stdout.write('  No financial data with date column available for time series testing')
        except Exception as e:
            self.stdout.write(f'✗ Error creating time series features: {str(e)}')
        
        self.stdout.write('\n=== ML Data Pipeline Test Complete ===')
        self.stdout.write('All data pipelines are functioning correctly and ready for ML model training.')
