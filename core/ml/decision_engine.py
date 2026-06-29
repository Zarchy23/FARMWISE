"""
Automated Decision-Making Service
Integrates all ML models to provide comprehensive farming recommendations
"""
from datetime import datetime, timedelta
from django.utils import timezone
from core.ml.models.crop_yield_model import CropYieldPredictor
from core.ml.models.equipment_maintenance_model import EquipmentMaintenancePredictor
from core.ml.models.financial_forecast_model import FinancialForecaster
from core.ml.models.livestock_health_model import LivestockHealthPredictor
from core.ml.models.weather_recommendation_model import WeatherRecommendationEngine
from core.models import CropSeason, Equipment, Animal, Farm


class DecisionEngine:
    """Central decision-making engine that integrates all ML models"""
    
    def __init__(self):
        self.crop_predictor = CropYieldPredictor()
        self.equipment_predictor = EquipmentMaintenancePredictor()
        self.financial_forecaster = FinancialForecaster()
        self.livestock_predictor = LivestockHealthPredictor()
        self.weather_engine = WeatherRecommendationEngine()
    
    def get_farm_recommendations(self, farm_id):
        """Get comprehensive recommendations for a farm"""
        farm = Farm.objects.get(id=farm_id)
        
        recommendations = {
            'farm_id': farm_id,
            'farm_name': farm.name,
            'generated_at': timezone.now().isoformat(),
            'crop_recommendations': self._get_crop_recommendations(farm),
            'equipment_recommendations': self._get_equipment_recommendations(farm),
            'financial_outlook': self._get_financial_outlook(farm),
            'livestock_recommendations': self._get_livestock_recommendations(farm),
            'weather_recommendations': self._get_weather_recommendations(farm),
            'priority_actions': []
        }
        
        # Compile priority actions
        recommendations['priority_actions'] = self._compile_priority_actions(recommendations)
        
        return recommendations
    
    def _get_crop_recommendations(self, farm):
        """Get crop-related recommendations"""
        recommendations = []
        
        # Get active crops
        active_crops = CropSeason.objects.filter(
            field__farm=farm,
            status__in=['planted', 'growing']
        ).select_related('crop_type', 'field')
        
        for crop in active_crops:
            try:
                # Predict yield
                features = {
                    'crop_type': crop.crop_type.name if crop.crop_type else 'unknown',
                    'area_hectares': crop.area_hectares or 0,
                    'planting_month': crop.planting_date.month if crop.planting_date else 0,
                    'growing_days': (timezone.now().date() - crop.planting_date.date()).days if crop.planting_date else 0,
                    'soil_type': crop.field.soil_type if crop.field else 'unknown',
                    'irrigation_type': crop.field.irrigation_type if crop.field else 'unknown',
                    'fertilizer_amount': crop.fertilizer_amount or 0,
                    'water_usage': crop.water_usage or 0,
                }
                
                predicted_yield = self.crop_predictor.predict(features)[0]
                
                rec = {
                    'crop_id': crop.id,
                    'crop_name': crop.crop_type.name if crop.crop_type else 'Unknown',
                    'field_name': crop.field.name if crop.field else 'Unknown',
                    'predicted_yield_per_hectare': round(predicted_yield, 2),
                    'total_predicted_yield': round(predicted_yield * (crop.area_hectares or 1), 2),
                    'status': crop.status,
                    'recommendations': []
                }
                
                # Add specific recommendations based on prediction
                if predicted_yield < (crop.expected_yield or 0) * 0.8:
                    rec['recommendations'].append({
                        'type': 'yield_warning',
                        'message': f'Predicted yield is below expected. Consider increasing fertilizer or irrigation.',
                        'priority': 'high'
                    })
                elif predicted_yield > (crop.expected_yield or 0) * 1.2:
                    rec['recommendations'].append({
                        'type': 'yield_excellent',
                        'message': f'Yield prediction is excellent. Consider planning for additional storage.',
                        'priority': 'medium'
                    })
                
                recommendations.append(rec)
            except Exception as e:
                # Model not trained or error
                recommendations.append({
                    'crop_id': crop.id,
                    'crop_name': crop.crop_type.name if crop.crop_type else 'Unknown',
                    'error': str(e)
                })
        
        return recommendations
    
    def _get_equipment_recommendations(self, farm):
        """Get equipment maintenance recommendations"""
        recommendations = []
        
        equipment = Equipment.objects.filter(farm=farm)
        
        for eq in equipment:
            try:
                # Calculate usage
                from django.db.models import Sum, F
                from core.models import EquipmentBooking
                
                bookings = EquipmentBooking.objects.filter(equipment=eq)
                total_usage = bookings.aggregate(
                    total=Sum(F('end_date') - F('start_date'))
                )['total'] or timedelta(0)
                total_usage_hours = total_usage.total_seconds() / 3600
                
                days_since_maintenance = 0
                if eq.last_maintenance_date:
                    days_since_maintenance = (timezone.now().date() - eq.last_maintenance_date).days
                
                features = {
                    'equipment_type': eq.equipment_type.name if eq.equipment_type else 'unknown',
                    'age_days': (timezone.now().date() - eq.purchase_date.date()).days if eq.purchase_date else 0,
                    'total_usage_hours': total_usage_hours,
                    'days_since_maintenance': days_since_maintenance,
                    'maintenance_interval_days': eq.maintenance_interval or 90,
                    'status': eq.status,
                }
                
                prediction = self.equipment_predictor.predict(features)
                
                rec = {
                    'equipment_id': eq.id,
                    'equipment_name': eq.name,
                    'equipment_type': eq.equipment_type.name if eq.equipment_type else 'Unknown',
                    'needs_maintenance': prediction['needs_maintenance'],
                    'maintenance_probability': round(prediction['probability'], 2),
                    'days_until_maintenance': prediction['days_until_maintenance'],
                    'recommendations': []
                }
                
                if prediction['needs_maintenance']:
                    rec['recommendations'].append({
                        'type': 'maintenance_required',
                        'message': f'Equipment needs maintenance. Schedule within {prediction["days_until_maintenance"]} days.',
                        'priority': 'high'
                    })
                elif prediction['probability'] > 0.7:
                    rec['recommendations'].append({
                        'type': 'maintenance_soon',
                        'message': 'Maintenance will be needed soon. Plan accordingly.',
                        'priority': 'medium'
                    })
                
                recommendations.append(rec)
            except Exception as e:
                recommendations.append({
                    'equipment_id': eq.id,
                    'equipment_name': eq.name,
                    'error': str(e)
                })
        
        return recommendations
    
    def _get_financial_outlook(self, farm):
        """Get financial forecast for the farm"""
        try:
            # Forecast revenue and expenses for next 30 days
            revenue_forecast = self.financial_forecaster.forecast(days=30, transaction_type='income')
            expense_forecast = self.financial_forecaster.forecast(days=30, transaction_type='expense')
            
            total_revenue = sum(f['predicted_amount'] for f in revenue_forecast)
            total_expenses = sum(f['predicted_amount'] for f in expense_forecast)
            net_profit = total_revenue - total_expenses
            
            return {
                'forecast_period_days': 30,
                'predicted_revenue': round(total_revenue, 2),
                'predicted_expenses': round(total_expenses, 2),
                'predicted_net_profit': round(net_profit, 2),
                'profit_margin': round((net_profit / total_revenue * 100) if total_revenue > 0 else 0, 2),
                'daily_breakdown': {
                    'revenue': revenue_forecast,
                    'expenses': expense_forecast
                },
                'recommendations': []
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _get_livestock_recommendations(self, farm):
        """Get livestock health recommendations"""
        recommendations = []
        
        animals = Animal.objects.filter(farm=farm, status='alive').select_related('animal_type')
        
        for animal in animals:
            try:
                from core.models import HealthRecord
                from django.db.models import Avg
                
                health_records = HealthRecord.objects.filter(animal=animal)
                avg_weight = health_records.aggregate(avg=Avg('weight'))['avg'] or 0
                health_issues = health_records.filter(
                    health_status__in=['sick', 'injured']
                ).count()
                
                features = {
                    'animal_type': animal.animal_type if animal.animal_type else 'unknown',
                    'age_days': (timezone.now().date() - animal.birth_date.date()).days if animal.birth_date else 0,
                    'gender': animal.gender,
                    'avg_weight': avg_weight,
                    'health_issues_count': health_issues,
                    'current_status': animal.status,
                }
                
                prediction = self.livestock_predictor.predict(features)
                
                rec = {
                    'animal_id': animal.id,
                    'animal_type': animal.animal_type if animal.animal_type else 'Unknown',
                    'tag_number': animal.tag_number,
                    'health_risk': prediction['health_risk'],
                    'risk_probability': round(prediction['risk_probability'], 2),
                    'risk_level': prediction['risk_level'],
                    'recommendations': []
                }
                
                if prediction['risk_level'] == 'high':
                    rec['recommendations'].append({
                        'type': 'health_alert',
                        'message': 'High health risk detected. Schedule veterinary examination.',
                        'priority': 'high'
                    })
                elif prediction['risk_level'] == 'medium':
                    rec['recommendations'].append({
                        'type': 'health_monitor',
                        'message': 'Medium health risk. Monitor closely.',
                        'priority': 'medium'
                    })
                
                recommendations.append(rec)
            except Exception as e:
                recommendations.append({
                    'animal_id': animal.id,
                    'tag_number': animal.tag_number,
                    'error': str(e)
                })
        
        return recommendations
    
    def _get_weather_recommendations(self, farm):
        """Get weather-based recommendations"""
        try:
            # Get current weather (simplified - would integrate with weather API)
            weather_data = {
                'temperature': 25,  # Would come from weather API
                'humidity': 60,
                'rainfall': 0,
                'wind_speed': 5,
                'soil_moisture': 50,
            }
            
            # Get primary crop type for the farm
            primary_crop = CropSeason.objects.filter(
                field__farm=farm,
                status__in=['planted', 'growing']
            ).first()
            
            crop_type = primary_crop.crop_type.name if primary_crop and primary_crop.crop_type else 'general'
            
            recommendation = self.weather_engine.get_recommendation(weather_data, crop_type)
            
            return {
                'current_weather': weather_data,
                'crop_type': crop_type,
                'recommendation': recommendation['recommendation'],
                'confidence': round(recommendation['confidence'], 2),
                'priority': recommendation['priority'],
                'message': self._format_weather_message(recommendation)
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _format_weather_message(self, recommendation):
        """Format weather recommendation into a readable message"""
        rec_map = {
            'increase_irrigation': 'Increase irrigation due to dry conditions',
            'reduce_irrigation': 'Reduce irrigation due to high moisture',
            'apply_fungicide': 'Apply fungicide due to high humidity/rain',
            'apply_frost_protection': 'Apply frost protection due to cold temperatures',
            'secure_structures': 'Secure structures due to high winds',
            'normal_operations': 'Normal operations - conditions are optimal',
            'apply_fertilizer': 'Good conditions for fertilizer application',
        }
        return rec_map.get(recommendation['recommendation'], 'Monitor conditions')
    
    def _compile_priority_actions(self, recommendations):
        """Compile all high-priority actions from all recommendations"""
        priority_actions = []
        
        # From crops
        for crop in recommendations.get('crop_recommendations', []):
            for rec in crop.get('recommendations', []):
                if rec.get('priority') == 'high':
                    priority_actions.append({
                        'category': 'crop',
                        'item': crop.get('crop_name'),
                        'action': rec.get('message'),
                        'priority': 'high'
                    })
        
        # From equipment
        for eq in recommendations.get('equipment_recommendations', []):
            for rec in eq.get('recommendations', []):
                if rec.get('priority') == 'high':
                    priority_actions.append({
                        'category': 'equipment',
                        'item': eq.get('equipment_name'),
                        'action': rec.get('message'),
                        'priority': 'high'
                    })
        
        # From livestock
        for animal in recommendations.get('livestock_recommendations', []):
            for rec in animal.get('recommendations', []):
                if rec.get('priority') == 'high':
                    priority_actions.append({
                        'category': 'livestock',
                        'item': animal.get('tag_number'),
                        'action': rec.get('message'),
                        'priority': 'high'
                    })
        
        # From weather
        weather = recommendations.get('weather_recommendations', {})
        if weather.get('priority') == 'high':
            priority_actions.append({
                'category': 'weather',
                'item': 'All crops',
                'action': weather.get('message'),
                'priority': 'high'
            })
        
        # Sort by priority
        priority_actions.sort(key=lambda x: x['priority'], reverse=True)
        
        return priority_actions[:10]  # Return top 10 priority actions
