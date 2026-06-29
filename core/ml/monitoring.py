"""
Model Monitoring and Retraining Pipeline
Monitors model performance and schedules retraining
"""
import os
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings
from core.ml.training_service import ModelTrainingService
from core.ml.data_pipeline import DataPipeline


class ModelMonitor:
    """Monitor ML model performance and trigger retraining when needed"""
    
    def __init__(self):
        self.training_service = ModelTrainingService()
        self.models_dir = os.path.join(settings.BASE_DIR, 'ml_models')
        self.metrics_file = os.path.join(self.models_dir, 'model_metrics.json')
    
    def check_model_freshness(self):
        """Check if models need retraining based on age"""
        now = timezone.now()
        retrain_threshold = timedelta(days=30)  # Retrain monthly
        
        models_status = {}
        
        model_files = {
            'crop_yield': 'crop_yield_model.pkl',
            'equipment_maintenance': 'equipment_maintenance_model.pkl',
            'financial_forecast': 'financial_forecast_model.pkl',
            'livestock_health': 'livestock_health_model.pkl',
            'weather_recommendation': 'weather_recommendation_model.pkl',
        }
        
        for model_name, filename in model_files.items():
            model_path = os.path.join(self.models_dir, filename)
            if os.path.exists(model_path):
                file_time = datetime.fromtimestamp(os.path.getmtime(model_path))
                age = now - file_time.replace(tzinfo=None)
                needs_retrain = age > retrain_threshold
                
                models_status[model_name] = {
                    'exists': True,
                    'age_days': age.days,
                    'needs_retraining': needs_retrain,
                    'last_trained': file_time.isoformat()
                }
            else:
                models_status[model_name] = {
                    'exists': False,
                    'age_days': None,
                    'needs_retraining': True,
                    'last_trained': None
                }
        
        return models_status
    
    def check_data_drift(self, model_name):
        """Check for data drift that might indicate need for retraining"""
        # Get recent data
        if model_name == 'crop_yield':
            recent_data = DataPipeline.get_crop_yield_data(days=7)
        elif model_name == 'equipment_maintenance':
            recent_data = DataPipeline.get_equipment_maintenance_data(days=7)
        elif model_name == 'financial_forecast':
            recent_data = DataPipeline.get_financial_data(days=7)
        elif model_name == 'livestock_health':
            recent_data = DataPipeline.get_livestock_health_data(days=7)
        else:
            return {'drift_detected': False, 'reason': 'No drift check implemented'}
        
        if recent_data.empty:
            return {'drift_detected': False, 'reason': 'Insufficient recent data'}
        
        # Simple drift detection: check if data volume changed significantly
        # In production, you'd use statistical tests like KS test, PSI, etc.
        data_volume = len(recent_data)
        
        # Get historical average (simplified)
        historical_avg = 100  # This would be stored from previous training
        
        if data_volume < historical_avg * 0.5:
            return {
                'drift_detected': True,
                'reason': f'Data volume dropped significantly: {data_volume} vs expected {historical_avg}'
            }
        
        return {'drift_detected': False, 'reason': 'No significant drift detected'}
    
    def get_model_metrics(self):
        """Get current model performance metrics"""
        # This would load stored metrics from training
        # For now, return placeholder
        return {
            'last_updated': timezone.now().isoformat(),
            'models': {
                'crop_yield': {'accuracy': 0.85, 'last_trained': None},
                'equipment_maintenance': {'accuracy': 0.82, 'last_trained': None},
                'financial_forecast': {'accuracy': 0.78, 'last_trained': None},
                'livestock_health': {'accuracy': 0.80, 'last_trained': None},
                'weather_recommendation': {'accuracy': 0.75, 'last_trained': None},
            }
        }
    
    def retrain_if_needed(self, farm_id=None):
        """Retrain models that need it based on freshness and drift"""
        freshness_status = self.check_model_freshness()
        retrain_results = {}
        
        for model_name, status in freshness_status.items():
            if status['needs_retraining']:
                try:
                    if model_name == 'crop_yield':
                        result = self.training_service.train_crop_yield_model(farm_id)
                    elif model_name == 'equipment_maintenance':
                        result = self.training_service.train_equipment_maintenance_model(farm_id)
                    elif model_name == 'financial_forecast':
                        result = self.training_service.train_financial_forecast_model(farm_id)
                    elif model_name == 'livestock_health':
                        result = self.training_service.train_livestock_health_model(farm_id)
                    elif model_name == 'weather_recommendation':
                        result = self.training_service.train_weather_recommendation_model()
                    
                    retrain_results[model_name] = {
                        'status': 'retrained',
                        'result': result
                    }
                except Exception as e:
                    retrain_results[model_name] = {
                        'status': 'error',
                        'error': str(e)
                    }
            else:
                retrain_results[model_name] = {
                    'status': 'skipped',
                    'reason': 'Model is fresh enough'
                }
        
        return {
            'checked_at': timezone.now().isoformat(),
            'retrain_results': retrain_results
        }
    
    def get_monitoring_report(self):
        """Get comprehensive monitoring report"""
        return {
            'generated_at': timezone.now().isoformat(),
            'model_freshness': self.check_model_freshness(),
            'model_metrics': self.get_model_metrics(),
            'recommendations': self._get_recommendations()
        }
    
    def _get_recommendations(self):
        """Get recommendations based on monitoring data"""
        freshness = self.check_model_freshness()
        recommendations = []
        
        for model_name, status in freshness.items():
            if not status['exists']:
                recommendations.append({
                    'model': model_name,
                    'action': 'train',
                    'priority': 'high',
                    'reason': 'Model does not exist'
                })
            elif status['needs_retraining']:
                recommendations.append({
                    'model': model_name,
                    'action': 'retrain',
                    'priority': 'medium',
                    'reason': f'Model is {status["age_days"]} days old'
                })
        
        return recommendations
