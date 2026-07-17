"""
Management command to schedule automated ML model retraining
Run: python manage.py schedule_ml_retraining
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models_analytics import YieldPrediction
from core.ml.data_pipeline import DataPipeline
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Schedule automated ML model retraining based on data availability'

    def handle(self, *args, **options):
        self.stdout.write('Checking ML model retraining schedule...')
        
        # Check if we have enough new data for retraining
        crop_data = DataPipeline.get_crop_yield_data()
        
        if len(crop_data) < 10:
            self.stdout.write('✗ Insufficient data for retraining. Need at least 10 records.')
            return
        
        # Check last training time
        last_prediction = YieldPrediction.objects.filter(
            status='completed'
        ).order_by('-created_at').first()
        
        if last_prediction:
            days_since_last_training = (timezone.now() - last_prediction.created_at).days
            self.stdout.write(f'Last training was {days_since_last_training} days ago')
            
            # Only retrain if it's been at least 7 days
            if days_since_last_training < 7:
                self.stdout.write('✗ Retraining not needed yet. Minimum interval is 7 days.')
                return
        else:
            self.stdout.write('No previous training found. Will train new model.')
        
        # Check if we have significantly more data than last training
        if last_prediction and 'training_samples' in last_prediction.factors:
            last_training_samples = last_prediction.factors['training_samples']
            current_samples = len(crop_data)
            
            # Only retrain if we have at least 20% more data
            if current_samples < last_training_samples * 1.2:
                self.stdout.write(f'✗ Not enough new data for retraining. Current: {current_samples}, Last: {last_training_samples}')
                return
        
        self.stdout.write('✓ Conditions met for automated retraining')
        self.stdout.write('Triggering model training...')
        
        # Import and run the training function
        try:
            from core.views_ml_dashboard import train_ml_model
            from django.test import RequestFactory
            
            # Create a mock request
            factory = RequestFactory()
            request = factory.post('/ml/train-model/')
            
            # Get a user for the request (admin user)
            from django.contrib.auth import get_user_model
            User = get_user_model()
            admin_user = User.objects.filter(is_superuser=True).first()
            
            if admin_user:
                request.user = admin_user
                
                # Call the training function
                response = train_ml_model(request)
                
                if response.status_code == 200:
                    import json
                    response_data = json.loads(response.content)
                    self.stdout.write(f'✓ Automated retraining successful!')
                    self.stdout.write(f'  Accuracy: {response_data["metrics"]["accuracy"]:.2f}%')
                    self.stdout.write(f'  R²: {response_data["metrics"]["r2"]:.2f}')
                else:
                    self.stdout.write('✗ Automated retraining failed')
            else:
                self.stdout.write('✗ No admin user found for training')
                
        except Exception as e:
            logger.error(f"Error in automated retraining: {str(e)}")
            self.stdout.write(f'✗ Error during automated retraining: {str(e)}')
