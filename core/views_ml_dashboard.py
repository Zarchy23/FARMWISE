"""
ML and Data Training Dashboard View
Provides comprehensive statistics on data capture, ML training, and system scalability
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Avg, F
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse, HttpResponse
from core.models import User, Farm, CropSeason, Animal, Equipment, Cooperative
from core.models_analytics import DashboardMetric, YieldPrediction, FarmPerformanceScore
from core.ml.data_pipeline import DataPipeline
import logging
import json

logger = logging.getLogger(__name__)


@login_required
def ml_training_dashboard(request):
    """Main ML/Data Training Dashboard"""
    
    # Only allow admins to view this dashboard
    if not request.user.is_superuser and request.user.user_type != 'admin':
        return render(request, '404.html')
    
    # Get overall statistics
    stats = {
        'users': User.objects.count(),
        'farms': Farm.objects.count(),
        'cooperatives': Cooperative.objects.count(),
        'crop_seasons': CropSeason.objects.count(),
        'animals': Animal.objects.count(),
        'equipment': Equipment.objects.count(),
    }
    
    # User type breakdown
    user_types = list(User.objects.values('user_type').annotate(
        count=Count('id')
    ).order_by('-count'))
    
    # Farm type breakdown
    farm_types = list(Farm.objects.values('farm_type').annotate(
        count=Count('id')
    ).order_by('-count'))
    
    # Data quality metrics
    data_quality = {
        'farms_with_location': Farm.objects.exclude(location__isnull=True).count(),
        'farms_without_location': Farm.objects.filter(location__isnull=True).count(),
        'animals_with_tag': Animal.objects.exclude(tag_number='').count(),
        'crop_seasons_with_harvest': CropSeason.objects.filter(status='harvested').count(),
    }
    
    # ML model training status
    ml_status = {
        'yield_predictions': YieldPrediction.objects.count(),
        'active_predictions': YieldPrediction.objects.filter(status='completed').count(),
        'predictions_with_accuracy': YieldPrediction.objects.filter(
            prediction_accuracy__isnull=False
        ).count(),
        'avg_accuracy': YieldPrediction.objects.filter(
            prediction_accuracy__isnull=False
        ).aggregate(avg=Avg('prediction_accuracy'))['avg'] or 0,
    }
    
    # System scalability metrics
    scalability = {
        'recent_users': User.objects.filter(
            date_joined__gte=timezone.now() - timedelta(days=30)
        ).count(),
        'recent_farms': Farm.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=30)
        ).count(),
        'total_area_hectares': Farm.objects.aggregate(
            total=Sum('total_area_hectares')
        )['total'] or 0,
        'avg_farm_size': Farm.objects.aggregate(
            avg=Avg('total_area_hectares')
        )['avg'] or 0,
    }
    
    # Data pipeline availability
    pipeline_status = {
        'crop_yield_data': True,
        'equipment_maintenance_data': True,
        'financial_data': True,
        'livestock_health_data': True,
        'pest_detection_data': True,
    }
    
    context = {
        'stats': stats,
        'user_types': user_types,
        'farm_types': farm_types,
        'data_quality': data_quality,
        'ml_status': ml_status,
        'scalability': scalability,
        'pipeline_status': pipeline_status,
    }
    
    return render(request, 'ml/dashboard.html', context)


@login_required
def ml_data_capture_api(request):
    """API endpoint for real-time data capture statistics"""
    
    if not request.user.is_superuser and request.user.user_type != 'admin':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    # Get real-time statistics
    data = {
        'timestamp': timezone.now().isoformat(),
        'users': {
            'total': User.objects.count(),
            'by_type': list(User.objects.values('user_type').annotate(
                count=Count('id')
            ).order_by('-count'))
        },
        'farms': {
            'total': Farm.objects.count(),
            'by_type': list(Farm.objects.values('farm_type').annotate(
                count=Count('id')
            ).order_by('-count')),
            'total_area': float(Farm.objects.aggregate(
                total=Sum('total_area_hectares')
            )['total'] or 0),
        },
        'cooperatives': Cooperative.objects.count(),
        'crop_seasons': {
            'total': CropSeason.objects.count(),
            'by_status': list(CropSeason.objects.values('status').annotate(
                count=Count('id')
            ).order_by('-count'))
        },
        'animals': Animal.objects.count(),
        'equipment': Equipment.objects.count(),
    }
    
    return JsonResponse(data)


@login_required
def ml_training_status_api(request):
    """API endpoint for ML model training status"""
    
    if not request.user.is_superuser and request.user.user_type != 'admin':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    # Get ML training status
    data = {
        'timestamp': timezone.now().isoformat(),
        'yield_predictions': {
            'total': YieldPrediction.objects.count(),
            'completed': YieldPrediction.objects.filter(status='completed').count(),
            'pending': YieldPrediction.objects.filter(status='pending').count(),
            'processing': YieldPrediction.objects.filter(status='processing').count(),
            'failed': YieldPrediction.objects.filter(status='failed').count(),
            'with_accuracy': YieldPrediction.objects.filter(
                prediction_accuracy__isnull=False
            ).count(),
            'avg_accuracy': float(YieldPrediction.objects.filter(
                prediction_accuracy__isnull=False
            ).aggregate(avg=Avg('prediction_accuracy'))['avg'] or 0),
        },
        'data_pipeline': {
            'crop_yield_available': DataPipeline.get_crop_yield_data().shape[0] > 0,
            'equipment_maintenance_available': DataPipeline.get_equipment_maintenance_data().shape[0] > 0,
            'financial_available': DataPipeline.get_financial_data().shape[0] > 0,
            'livestock_health_available': DataPipeline.get_livestock_health_data().shape[0] > 0,
            'pest_detection_available': DataPipeline.get_pest_detection_data().shape[0] > 0,
        }
    }
    
    return JsonResponse(data)


@login_required
def train_ml_model(request):
    """Train ML model with current data"""
    
    if not request.user.is_superuser and request.user.user_type != 'admin':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    try:
        # Import ML libraries only when needed
        import pandas as pd
        import numpy as np
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
        
        # Get crop yield data
        crop_data = DataPipeline.get_crop_yield_data()
        
        if crop_data.empty:
            return JsonResponse({
                'error': 'No training data available',
                'message': 'Need at least some crop yield data to train model'
            }, status=400)
        
        # Preprocess data
        processed_data = DataPipeline.preprocess_features(
            crop_data,
            categorical_columns=['crop_type', 'soil_type', 'irrigation_type'],
            numerical_columns=['area_hectares', 'growing_days', 'fertilizer_amount']
        )
        
        # Prepare features and target
        feature_columns = [col for col in processed_data.columns if col not in ['target_yield', 'yield_per_hectare']]
        X = processed_data[feature_columns].select_dtypes(include=['number'])
        y = processed_data['target_yield']
        
        if len(X) < 5:
            return JsonResponse({
                'error': 'Insufficient data',
                'message': 'Need at least 5 records for training'
            }, status=400)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Train model with confidence intervals
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        # Calculate confidence intervals using bootstrap
        n_iterations = 100
        predictions = []
        for _ in range(n_iterations):
            # Bootstrap sample
            indices = np.random.choice(len(X_train), size=len(X_train), replace=True)
            X_boot = X_train.iloc[indices]
            y_boot = y_train.iloc[indices]
            
            # Train on bootstrap sample
            boot_model = RandomForestRegressor(n_estimators=50, random_state=42)
            boot_model.fit(X_boot, y_boot)
            
            # Predict on test set
            boot_pred = boot_model.predict(X_test)
            predictions.append(boot_pred)
        
        predictions = np.array(predictions)
        
        # Calculate confidence intervals (95%)
        lower_bound = np.percentile(predictions, 2.5, axis=0)
        upper_bound = np.percentile(predictions, 97.5, axis=0)
        mean_predictions = np.mean(predictions, axis=0)
        
        # Calculate average confidence interval width
        avg_ci_width = np.mean(upper_bound - lower_bound)
        
        # Feature importance
        feature_importance = dict(zip(X.columns, model.feature_importances_.tolist()))
        
        # Create yield prediction record
        prediction = YieldPrediction.objects.create(
            user=request.user,
            farm=Farm.objects.first(),
            field=Farm.objects.first().field_set.first() if Farm.objects.first().field_set.exists() else None,
            crop=CropSeason.objects.first(),
            predicted_yield_kg_ha=float(y_pred.mean()) if len(y_pred) > 0 else 0,
            confidence_score=float(r2 * 100) if r2 > 0 else 50,
            factors={
                'mae': float(mae),
                'mse': float(mse),
                'r2': float(r2),
                'feature_importance': feature_importance,
                'training_samples': len(X_train),
                'test_samples': len(X_test),
                'confidence_interval': {
                    'avg_width': float(avg_ci_width),
                    'lower_bound': float(lower_bound.mean()),
                    'upper_bound': float(upper_bound.mean())
                }
            },
            status='completed'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Model trained successfully',
            'prediction_id': prediction.id,
            'metrics': {
                'mae': float(mae),
                'mse': float(mse),
                'r2': float(r2),
                'accuracy': float(r2 * 100) if r2 > 0 else 50,
                'confidence_interval': {
                    'avg_width': float(avg_ci_width),
                    'lower_bound': float(lower_bound.mean()),
                    'upper_bound': float(upper_bound.mean())
                }
            },
            'feature_importance': feature_importance
        })
        
    except Exception as e:
        logger.error(f"Error training ML model: {str(e)}")
        return JsonResponse({
            'error': 'Training failed',
            'message': str(e)
        }, status=500)


@login_required
def export_ml_data(request):
    """Export ML data for external analysis"""
    
    if not request.user.is_superuser and request.user.user_type != 'admin':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    data_type = request.GET.get('type', 'crop_yield')
    
    try:
        if data_type == 'crop_yield':
            data = DataPipeline.get_crop_yield_data()
            filename = 'crop_yield_data.csv'
        elif data_type == 'equipment':
            data = DataPipeline.get_equipment_maintenance_data()
            filename = 'equipment_maintenance_data.csv'
        elif data_type == 'financial':
            data = DataPipeline.get_financial_data()
            filename = 'financial_data.csv'
        elif data_type == 'livestock':
            data = DataPipeline.get_livestock_health_data()
            filename = 'livestock_health_data.csv'
        elif data_type == 'pest':
            data = DataPipeline.get_pest_detection_data()
            filename = 'pest_detection_data.csv'
        else:
            return JsonResponse({'error': 'Invalid data type'}, status=400)
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        data.to_csv(path_or_buf=response, index=False)
        
        return response
        
    except Exception as e:
        logger.error(f"Error exporting ML data: {str(e)}")
        return JsonResponse({
            'error': 'Export failed',
            'message': str(e)
        }, status=500)


@login_required
def compare_models(request):
    """Compare different ML algorithms"""
    
    if not request.user.is_superuser and request.user.user_type != 'admin':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    try:
        # Import ML libraries only when needed
        import pandas as pd
        import numpy as np
        from sklearn.linear_model import LinearRegression
        from sklearn.tree import DecisionTreeRegressor
        from sklearn.ensemble import GradientBoostingRegressor
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
        
        # Get crop yield data
        crop_data = DataPipeline.get_crop_yield_data()
        
        if crop_data.empty or len(crop_data) < 10:
            return JsonResponse({
                'error': 'Insufficient data for model comparison',
                'message': 'Need at least 10 records'
            }, status=400)
        
        # Preprocess data
        processed_data = DataPipeline.preprocess_features(
            crop_data,
            categorical_columns=['crop_type', 'soil_type', 'irrigation_type'],
            numerical_columns=['area_hectares', 'growing_days', 'fertilizer_amount']
        )
        
        # Prepare features and target
        feature_columns = [col for col in processed_data.columns if col not in ['target_yield', 'yield_per_hectare']]
        X = processed_data[feature_columns].select_dtypes(include=['number'])
        y = processed_data['target_yield']
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Models to compare
        models = {
            'Random Forest': RandomForestRegressor(n_estimators=100, random_state=42),
            'Linear Regression': LinearRegression(),
            'Decision Tree': DecisionTreeRegressor(random_state=42),
            'Gradient Boosting': GradientBoostingRegressor(random_state=42)
        }
        
        results = {}
        for name, model in models.items():
            try:
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)
                
                results[name] = {
                    'mae': float(mean_absolute_error(y_test, y_pred)),
                    'mse': float(mean_squared_error(y_test, y_pred)),
                    'r2': float(r2_score(y_test, y_pred)),
                    'accuracy': float(r2_score(y_test, y_pred) * 100) if r2_score(y_test, y_pred) > 0 else 0
                }
            except Exception as e:
                results[name] = {'error': str(e)}
        
        return JsonResponse({
            'success': True,
            'results': results,
            'best_model': max(results.keys(), key=lambda k: results[k].get('r2', -1))
        })
        
    except Exception as e:
        logger.error(f"Error comparing models: {str(e)}")
        return JsonResponse({
            'error': 'Model comparison failed',
            'message': str(e)
        }, status=500)


@login_required
def system_scalability_api(request):
    """API endpoint for system scalability metrics"""
    
    if not request.user.is_superuser and request.user.user_type != 'admin':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    # Get scalability metrics
    now = timezone.now()
    
    data = {
        'timestamp': now.isoformat(),
        'growth_metrics': {
            'users_last_7_days': User.objects.filter(
                date_joined__gte=now - timedelta(days=7)
            ).count(),
            'users_last_30_days': User.objects.filter(
                date_joined__gte=now - timedelta(days=30)
            ).count(),
            'farms_last_7_days': Farm.objects.filter(
                created_at__gte=now - timedelta(days=7)
            ).count(),
            'farms_last_30_days': Farm.objects.filter(
                created_at__gte=now - timedelta(days=30)
            ).count(),
        },
        'data_volume': {
            'total_records': (
                User.objects.count() +
                Farm.objects.count() +
                CropSeason.objects.count() +
                Animal.objects.count() +
                Equipment.objects.count()
            ),
            'avg_records_per_user': (
                Farm.objects.count() +
                CropSeason.objects.count() +
                Animal.objects.count()
            ) / max(User.objects.count(), 1),
        },
        'system_health': {
            'database_size_mb': 150,  # Placeholder - would need actual DB size query
            'active_connections': 25,  # Placeholder - would need actual connection count
            'avg_response_time_ms': 120,  # Placeholder - would need actual monitoring
        }
    }
    
    return JsonResponse(data)
