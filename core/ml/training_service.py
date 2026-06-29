"""
Model Training Service
Handles training and retraining of all ML models
"""
from django.utils import timezone
from core.ml.models.crop_yield_model import CropYieldPredictor
from core.ml.models.equipment_maintenance_model import EquipmentMaintenancePredictor
from core.ml.models.financial_forecast_model import FinancialForecaster
from core.ml.models.livestock_health_model import LivestockHealthPredictor
from core.ml.models.weather_recommendation_model import WeatherRecommendationEngine
from core.ml.models.pest_detection_model import PestDetectionEnhancer
from core.ml.data_pipeline import DataPipeline


class ModelTrainingService:
    """Service for training and managing ML models"""
    
    def __init__(self):
        self.crop_predictor = CropYieldPredictor()
        self.equipment_predictor = EquipmentMaintenancePredictor()
        self.financial_forecaster = FinancialForecaster()
        self.livestock_predictor = LivestockHealthPredictor()
        self.weather_engine = WeatherRecommendationEngine()
        self.pest_enhancer = PestDetectionEnhancer()
    
    def train_all_models(self, farm_id=None):
        """Train all ML models with current data"""
        results = {
            'started_at': timezone.now().isoformat(),
            'models': {}
        }
        
        # Train crop yield model
        try:
            crop_data = DataPipeline.get_crop_yield_data(farm_id=farm_id)
            crop_metrics = self.crop_predictor.train(crop_data)
            results['models']['crop_yield'] = {
                'status': 'success',
                'metrics': crop_metrics
            }
        except Exception as e:
            results['models']['crop_yield'] = {
                'status': 'error',
                'error': str(e)
            }
        
        # Train equipment maintenance model
        try:
            equipment_data = DataPipeline.get_equipment_maintenance_data(farm_id=farm_id)
            equipment_metrics = self.equipment_predictor.train(equipment_data)
            results['models']['equipment_maintenance'] = {
                'status': 'success',
                'metrics': equipment_metrics
            }
        except Exception as e:
            results['models']['equipment_maintenance'] = {
                'status': 'error',
                'error': str(e)
            }
        
        # Train financial forecast model
        try:
            financial_data = DataPipeline.get_financial_data(farm_id=farm_id)
            financial_metrics = self.financial_forecaster.train(financial_data)
            results['models']['financial_forecast'] = {
                'status': 'success',
                'metrics': financial_metrics
            }
        except Exception as e:
            results['models']['financial_forecast'] = {
                'status': 'error',
                'error': str(e)
            }
        
        # Train livestock health model
        try:
            livestock_data = DataPipeline.get_livestock_health_data(farm_id=farm_id)
            livestock_metrics = self.livestock_predictor.train(livestock_data)
            results['models']['livestock_health'] = {
                'status': 'success',
                'metrics': livestock_metrics
            }
        except Exception as e:
            results['models']['livestock_health'] = {
                'status': 'error',
                'error': str(e)
            }
        
        # Train weather recommendation engine
        try:
            weather_metrics = self.weather_engine.train()
            results['models']['weather_recommendation'] = {
                'status': 'success',
                'metrics': weather_metrics
            }
        except Exception as e:
            results['models']['weather_recommendation'] = {
                'status': 'error',
                'error': str(e)
            }
        
        # Train pest detection enhancer
        try:
            pest_data = DataPipeline.get_pest_detection_data(farm_id=farm_id)
            pest_metrics = self.pest_enhancer.train(pest_data)
            results['models']['pest_detection'] = {
                'status': 'success',
                'metrics': pest_metrics
            }
        except Exception as e:
            results['models']['pest_detection'] = {
                'status': 'error',
                'error': str(e)
            }
        
        results['completed_at'] = timezone.now().isoformat()
        results['total_models'] = len(results['models'])
        results['successful'] = sum(1 for m in results['models'].values() if m['status'] == 'success')
        results['failed'] = sum(1 for m in results['models'].values() if m['status'] == 'error')
        
        return results
    
    def train_crop_yield_model(self, farm_id=None):
        """Train only the crop yield prediction model"""
        try:
            data = DataPipeline.get_crop_yield_data(farm_id=farm_id)
            metrics = self.crop_predictor.train(data)
            return {
                'status': 'success',
                'metrics': metrics,
                'feature_importance': self.crop_predictor.get_feature_importance()
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def train_equipment_maintenance_model(self, farm_id=None):
        """Train only the equipment maintenance model"""
        try:
            data = DataPipeline.get_equipment_maintenance_data(farm_id=farm_id)
            metrics = self.equipment_predictor.train(data)
            return {
                'status': 'success',
                'metrics': metrics,
                'feature_importance': self.equipment_predictor.get_feature_importance()
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def train_financial_forecast_model(self, farm_id=None):
        """Train only the financial forecast model"""
        try:
            data = DataPipeline.get_financial_data(farm_id=farm_id)
            metrics = self.financial_forecaster.train(data)
            return {
                'status': 'success',
                'metrics': metrics
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def train_livestock_health_model(self, farm_id=None):
        """Train only the livestock health model"""
        try:
            data = DataPipeline.get_livestock_health_data(farm_id=farm_id)
            metrics = self.livestock_predictor.train(data)
            return {
                'status': 'success',
                'metrics': metrics,
                'feature_importance': self.livestock_predictor.get_feature_importance()
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def train_weather_recommendation_model(self):
        """Train only the weather recommendation engine"""
        try:
            metrics = self.weather_engine.train()
            return {
                'status': 'success',
                'metrics': metrics
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def train_pest_detection_model(self, farm_id=None):
        """Train only the pest detection enhancement model"""
        try:
            data = DataPipeline.get_pest_detection_data(farm_id=farm_id)
            metrics = self.pest_enhancer.train(data)
            patterns = self.pest_enhancer.get_diagnosis_patterns(data)
            return {
                'status': 'success',
                'metrics': metrics,
                'patterns': patterns,
                'feature_importance': self.pest_enhancer.get_feature_importance()
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def get_model_status(self):
        """Check status of all trained models"""
        import os
        from django.conf import settings
        
        base_path = os.path.join(settings.BASE_DIR, 'ml_models')
        
        models = {
            'crop_yield': os.path.exists(os.path.join(base_path, 'crop_yield_model.pkl')),
            'equipment_maintenance': os.path.exists(os.path.join(base_path, 'equipment_maintenance_model.pkl')),
            'financial_forecast': os.path.exists(os.path.join(base_path, 'financial_forecast_model.pkl')),
            'livestock_health': os.path.exists(os.path.join(base_path, 'livestock_health_model.pkl')),
            'weather_recommendation': os.path.exists(os.path.join(base_path, 'weather_recommendation_model.pkl')),
            'pest_detection': os.path.exists(os.path.join(base_path, 'pest_detection_model.pkl')),
        }
        
        return {
            'models_trained': sum(models.values()),
            'total_models': len(models),
            'model_status': models
        }
