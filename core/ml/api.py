"""
ML API Endpoints
REST API endpoints for model training and predictions
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from core.ml.training_service import ModelTrainingService
from core.ml.decision_engine import DecisionEngine
from core.ml.models.crop_yield_model import CropYieldPredictor
from core.ml.models.equipment_maintenance_model import EquipmentMaintenancePredictor
from core.ml.models.financial_forecast_model import FinancialForecaster
from core.ml.models.livestock_health_model import LivestockHealthPredictor
from core.ml.models.weather_recommendation_model import WeatherRecommendationEngine
from core.ml.models.pest_detection_model import PestDetectionEnhancer


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def model_status(request):
    """Get status of all trained ML models"""
    service = ModelTrainingService()
    status = service.get_model_status()
    return Response(status)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def train_all_models(request):
    """Train all ML models with current data"""
    farm_id = request.data.get('farm_id')
    service = ModelTrainingService()
    results = service.train_all_models(farm_id=farm_id)
    return Response(results)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def train_crop_model(request):
    """Train crop yield prediction model"""
    farm_id = request.data.get('farm_id')
    service = ModelTrainingService()
    results = service.train_crop_yield_model(farm_id=farm_id)
    return Response(results)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def train_equipment_model(request):
    """Train equipment maintenance model"""
    farm_id = request.data.get('farm_id')
    service = ModelTrainingService()
    results = service.train_equipment_maintenance_model(farm_id=farm_id)
    return Response(results)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def train_financial_model(request):
    """Train financial forecast model"""
    farm_id = request.data.get('farm_id')
    service = ModelTrainingService()
    results = service.train_financial_forecast_model(farm_id=farm_id)
    return Response(results)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def train_livestock_model(request):
    """Train livestock health model"""
    farm_id = request.data.get('farm_id')
    service = ModelTrainingService()
    results = service.train_livestock_health_model(farm_id=farm_id)
    return Response(results)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def train_weather_model(request):
    """Train weather recommendation engine"""
    service = ModelTrainingService()
    results = service.train_weather_recommendation_model()
    return Response(results)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def train_pest_model(request):
    """Train pest detection enhancement model"""
    farm_id = request.data.get('farm_id')
    service = ModelTrainingService()
    results = service.train_pest_detection_model(farm_id=farm_id)
    return Response(results)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_farm_recommendations(request):
    """Get comprehensive AI recommendations for a farm"""
    farm_id = request.GET.get('farm_id')
    if not farm_id:
        return Response(
            {'error': 'farm_id parameter is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if user has access to this farm
    from core.models import Farm
    try:
        farm = Farm.objects.get(id=farm_id)
        if farm.owner != request.user and not request.user.is_superuser:
            return Response(
                {'error': 'You do not have access to this farm'},
                status=status.HTTP_403_FORBIDDEN
            )
    except Farm.DoesNotExist:
        return Response(
            {'error': 'Farm not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    engine = DecisionEngine()
    recommendations = engine.get_farm_recommendations(farm_id)
    return Response(recommendations)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def predict_crop_yield(request):
    """Predict yield for specific crop"""
    features = request.data
    predictor = CropYieldPredictor()
    
    try:
        prediction = predictor.predict(features)
        return Response({
            'predicted_yield_per_hectare': float(prediction[0]),
            'features_used': features
        })
    except FileNotFoundError:
        return Response(
            {'error': 'Model not trained. Please train the model first.'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def predict_equipment_maintenance(request):
    """Predict maintenance need for equipment"""
    features = request.data
    predictor = EquipmentMaintenancePredictor()
    
    try:
        prediction = predictor.predict(features)
        return Response(prediction)
    except FileNotFoundError:
        return Response(
            {'error': 'Model not trained. Please train the model first.'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def forecast_financials(request):
    """Forecast financial metrics"""
    days = int(request.GET.get('days', 30))
    transaction_type = request.GET.get('transaction_type', 'income')
    
    forecaster = FinancialForecaster()
    
    try:
        forecast = forecaster.forecast(days=days, transaction_type=transaction_type)
        return Response({
            'forecast_period_days': days,
            'transaction_type': transaction_type,
            'forecasts': forecast
        })
    except FileNotFoundError:
        return Response(
            {'error': 'Model not trained. Please train the model first.'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def predict_livestock_health(request):
    """Predict health risk for livestock"""
    features = request.data
    predictor = LivestockHealthPredictor()
    
    try:
        prediction = predictor.predict(features)
        return Response(prediction)
    except FileNotFoundError:
        return Response(
            {'error': 'Model not trained. Please train the model first.'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_weather_recommendation(request):
    """Get weather-based farming recommendation"""
    weather_data = request.data.get('weather', {})
    crop_type = request.data.get('crop_type', 'general')
    
    engine = WeatherRecommendationEngine()
    
    try:
        recommendation = engine.get_recommendation(weather_data, crop_type)
        return Response(recommendation)
    except FileNotFoundError:
        return Response(
            {'error': 'Model not trained. Please train the model first.'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
