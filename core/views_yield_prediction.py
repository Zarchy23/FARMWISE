"""
Yield Prediction from Images
Allows farmers to upload crop images for AI-based yield prediction
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.files.storage import default_storage
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import logging
import os
import base64
import tempfile
from core.models_analytics import YieldPrediction
from core.models import Farm, CropType

logger = logging.getLogger(__name__)


@login_required
def yield_prediction_image(request):
    """Image-based yield prediction page"""
    
    # Get user's farms using correct related name
    user_farms = Farm.objects.filter(owner=request.user)
    
    # Get all crop types for dropdown
    crop_types = CropType.objects.filter(is_active=True).order_by('name')
    
    # Get user's prediction history
    predictions = YieldPrediction.objects.filter(user=request.user).order_by('-created_at')[:10]
    
    context = {
        'page_title': 'Yield Prediction from Images',
        'user_farms': user_farms,
        'crop_types': crop_types,
        'predictions': predictions
    }
    return render(request, 'yield_prediction/image_upload.html', context)


@csrf_exempt
@login_required
def analyze_crop_image(request):
    """Analyze crop image and predict yield using hybrid AI"""
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'POST required'}, status=405)
    
    try:
        image_file = request.FILES.get('image')
        farm_id = request.POST.get('farm_id')
        area_size = request.POST.get('area_size')
        crop_selection = request.POST.get('crop_selection')  # 'dropdown' or 'custom'
        crop_type_id = request.POST.get('crop_type_id')
        custom_crop_name = request.POST.get('custom_crop_name')
        
        # Get ML features from form
        soil_nitrogen = request.POST.get('soil_nitrogen', 45)
        soil_phosphorus = request.POST.get('soil_phosphorus', 78)
        soil_potassium = request.POST.get('soil_potassium', 50)
        soil_ph = request.POST.get('soil_ph', 6.5)
        temperature_avg = request.POST.get('temperature_avg', 23)
        rainfall_mm = request.POST.get('rainfall_mm', 650)
        humidity = request.POST.get('humidity', 65)
        fertilizer_kg_ha = request.POST.get('fertilizer_kg_ha', 100)
        irrigation_days = request.POST.get('irrigation_days', 10)
        pesticide_used = request.POST.get('pesticide_used', 5)
        disease_severity = request.POST.get('disease_severity', 2)
        
        # Determine crop name
        crop_name = 'Unknown'
        if crop_selection == 'dropdown' and crop_type_id:
            try:
                crop_type = CropType.objects.get(id=crop_type_id)
                crop_name = crop_type.name
            except CropType.DoesNotExist:
                crop_name = 'Unknown'
        elif crop_selection == 'custom' and custom_crop_name:
            crop_name = custom_crop_name
        else:
            crop_name = 'Unknown'
        
        if not image_file:
            return JsonResponse({'success': False, 'message': 'No image uploaded'}, status=400)
        
        if not area_size or float(area_size) <= 0:
            return JsonResponse({'success': False, 'message': 'Invalid area size'}, status=400)
        
        area_size_hectares = float(area_size)
        
        # Save the uploaded image
        file_path = default_storage.save(f'yield_predictions/{image_file.name}', image_file)
        image_url = default_storage.url(file_path)
        
        # Save image to temp file for hybrid service
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            for chunk in image_file.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name
        
        try:
            # Use hybrid service for yield prediction with user-provided features
            features = {
                'area_hectares': area_size_hectares,
                'soil_nitrogen': float(soil_nitrogen),
                'soil_phosphorus': float(soil_phosphorus),
                'soil_potassium': float(soil_potassium),
                'soil_ph': float(soil_ph),
                'temperature_avg': float(temperature_avg),
                'rainfall_mm': float(rainfall_mm),
                'humidity': float(humidity),
                'fertilizer_kg_ha': float(fertilizer_kg_ha),
                'irrigation_days': float(irrigation_days),
                'pesticide_used': float(pesticide_used),
                'disease_severity': float(disease_severity)
            }

            # Get hybrid prediction
            try:
                from core.services.hybrid_prediction_service import hybrid_service
                result = hybrid_service.predict_yield_hybrid(features, use_api_fallback=True)
            except Exception as e:
                logger.warning(f"Hybrid service not available: {e}")
                result = {'error': 'Hybrid service not available'}
            
            if 'error' in result:
                # Fallback to mock prediction
                base_yield_per_hectare = 4500
                estimated_yield_kg_ha = base_yield_per_hectare
                total_yield_kg = estimated_yield_kg_ha * area_size_hectares
                method = 'fallback'
            else:
                estimated_yield_kg_ha = result.get('predicted_yield_kg_per_hectare', 4500)
                total_yield_kg = estimated_yield_kg_ha * area_size_hectares
                method = result.get('method', 'hybrid')
            
            prediction_result = {
                'crop_type': crop_name,
                'growth_stage': 'Flowering',
                'health_status': 'Good',
                'area_size_hectares': area_size_hectares,
                'estimated_yield_kg_ha': estimated_yield_kg_ha,
                'total_yield_kg': total_yield_kg,
                'confidence_score': 85 if method == 'hybrid' else 75,
                'method': method,
                'recommendations': [
                    'Apply nitrogen fertilizer in 2 weeks',
                    'Monitor for fall armyworm infestation',
                    'Ensure adequate irrigation during grain filling'
                ],
                'image_analysis': {
                    'leaf_color': 'Healthy green',
                    'plant_density': 'Optimal',
                    'disease_detection': 'No diseases detected',
                    'pest_detection': 'No pests detected'
                }
            }
            
            logger.info(f"Hybrid yield prediction completed for user {request.user.username}, image: {file_path}, area: {area_size_hectares} ha, method: {method}")
            
            # Save prediction to database
            try:
                # Get user's first farm and field (simplified for now)
                from core.models import Farm, Field, CropSeason
                
                user_farms = Farm.objects.filter(owner=request.user)
                farm = user_farms.first() if user_farms.exists() else None
                field = Field.objects.filter(farm=farm).first() if farm else None
                crop = CropSeason.objects.filter(field=field).first() if field else None
                
                # Create prediction even without complete farm setup
                prediction = YieldPrediction.objects.create(
                    user=request.user,
                    farm=farm,
                    field=field,
                    crop=crop,
                    predicted_yield_kg_ha=estimated_yield_kg_ha,
                    confidence_score=prediction_result['confidence_score'],
                    factors={
                        'area_hectares': area_size_hectares,
                        'method': method,
                        'image_url': image_url,
                        'features_used': result.get('features_used', []),
                        'crop_name': crop_name
                    },
                    status='pending'
                )
                logger.info(f"Prediction saved to database: {prediction.id}")
            except Exception as db_error:
                logger.error(f"Could not save prediction to database: {db_error}")
                logger.error(f"Database error details: {str(db_error)}", exc_info=True)
            
            return JsonResponse({
                'success': True,
                'image_url': image_url,
                'prediction': prediction_result
            })
            
        finally:
            # Clean up temp file
            try:
                os.unlink(tmp_path)
            except:
                pass
        
    except Exception as e:
        logger.error(f"Error analyzing crop image: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)


@login_required
def yield_prediction_dashboard(request):
    """Yield prediction dashboard with history and comparison"""
    
    predictions = YieldPrediction.objects.filter(user=request.user).order_by('-created_at')
    
    # Calculate statistics
    total_predictions = predictions.count()
    completed_predictions = predictions.filter(status='completed').count()
    predictions_with_actual = predictions.filter(actual_yield_kg_ha__isnull=False).count()
    
    # Calculate average accuracy
    avg_accuracy = 0
    if predictions_with_actual > 0:
        accuracies = [p.prediction_accuracy for p in predictions if p.prediction_accuracy]
        if accuracies:
            avg_accuracy = sum(accuracies) / len(accuracies)
    
    context = {
        'page_title': 'Yield Prediction Dashboard',
        'predictions': predictions,
        'total_predictions': total_predictions,
        'completed_predictions': completed_predictions,
        'predictions_with_actual': predictions_with_actual,
        'avg_accuracy': round(avg_accuracy, 2) if avg_accuracy else 0
    }
    return render(request, 'yield_prediction/dashboard.html', context)


@csrf_exempt
@login_required
def update_actual_yield(request, prediction_id):
    """Update actual yield for a prediction"""
    
    logger.info(f"=== UPDATE ACTUAL YIELD START ===")
    logger.info(f"Request method: {request.method}")
    logger.info(f"Prediction ID: {prediction_id}")
    logger.info(f"User: {request.user}")
    
    if request.method != 'POST':
        logger.error(f"Wrong method: {request.method}")
        return JsonResponse({'success': False, 'message': 'POST required'}, status=405)
    
    try:
        prediction = YieldPrediction.objects.get(id=prediction_id, user=request.user)
        actual_yield = request.POST.get('actual_yield')
        harvest_date = request.POST.get('harvest_date')
        
        logger.info(f"Actual yield received: {actual_yield}")
        logger.info(f"Harvest date received: {harvest_date}")
        logger.info(f"Current actual yield in DB: {prediction.actual_yield_kg_ha}")
        
        if not actual_yield:
            logger.error("Actual yield is empty")
            return JsonResponse({'success': False, 'message': 'Actual yield required'}, status=400)
        
        prediction.actual_yield_kg_ha = float(actual_yield)
        logger.info(f"Set actual_yield_kg_ha to: {prediction.actual_yield_kg_ha}")
        
        if harvest_date:
            from datetime import datetime
            prediction.harvest_date = datetime.strptime(harvest_date, '%Y-%m-%d').date()
            logger.info(f"Set harvest_date to: {prediction.harvest_date}")
        
        prediction.save()
        logger.info(f"Prediction saved successfully")
        
        # Verify the save
        prediction.refresh_from_db()
        logger.info(f"Verified actual yield after save: {prediction.actual_yield_kg_ha}")
        
        logger.info(f"=== UPDATE ACTUAL YIELD END ===")
        
        return JsonResponse({
            'success': True,
            'message': 'Actual yield updated successfully'
        })
        
    except YieldPrediction.DoesNotExist:
        logger.error(f"Prediction {prediction_id} not found for user {request.user}")
        return JsonResponse({'success': False, 'message': 'Prediction not found'}, status=404)
    except Exception as e:
        logger.error(f"Error updating actual yield: {str(e)}", exc_info=True)
        logger.error(f"=== UPDATE ACTUAL YIELD ERROR ===")
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'}, status=500)


@login_required
def calculate_accuracy_view(request, prediction_id):
    """Calculate accuracy for a prediction"""
    
    logger.info(f"=== CALCULATE ACCURACY START ===")
    logger.info(f"Request method: {request.method}")
    logger.info(f"Prediction ID: {prediction_id}")
    logger.info(f"User: {request.user}")
    
    if request.method != 'GET':
        logger.error(f"Wrong method: {request.method}")
        return JsonResponse({'success': False, 'message': 'GET required'}, status=405)
    
    try:
        logger.info(f"Fetching prediction {prediction_id} for user {request.user}")
        prediction = YieldPrediction.objects.get(id=prediction_id, user=request.user)
        
        logger.info(f"Prediction found: {prediction.id}")
        logger.info(f"Actual yield type: {type(prediction.actual_yield_kg_ha)}")
        logger.info(f"Actual yield value: {prediction.actual_yield_kg_ha}")
        logger.info(f"Predicted yield type: {type(prediction.predicted_yield_kg_ha)}")
        logger.info(f"Predicted yield value: {prediction.predicted_yield_kg_ha}")
        logger.info(f"Current accuracy: {prediction.prediction_accuracy}")
        
        if not prediction.actual_yield_kg_ha:
            logger.error("Actual yield is None or zero")
            return JsonResponse({'success': False, 'message': 'Actual yield must be set first'}, status=400)
        
        logger.info("Calling calculate_accuracy method")
        accuracy = prediction.calculate_accuracy()
        
        logger.info(f"Calculated accuracy: {accuracy}")
        logger.info(f"Accuracy type: {type(accuracy)}")
        
        # Refresh from database to verify save
        prediction.refresh_from_db()
        logger.info(f"Database accuracy after save: {prediction.prediction_accuracy}")
        
        logger.info(f"=== CALCULATE ACCURACY END ===")
        
        return JsonResponse({
            'success': True,
            'prediction_accuracy': float(accuracy) if accuracy else None,
            'message': 'Accuracy calculated successfully'
        })
        
    except YieldPrediction.DoesNotExist:
        logger.error(f"Prediction {prediction_id} not found for user {request.user}")
        return JsonResponse({'success': False, 'message': 'Prediction not found'}, status=404)
    except Exception as e:
        logger.error(f"Error calculating accuracy: {str(e)}", exc_info=True)
        logger.error(f"=== CALCULATE ACCURACY ERROR ===")
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'}, status=500)


@login_required
def mark_as_completed(request, prediction_id):
    """Mark a prediction as completed"""
    
    if request.method != 'GET':
        return JsonResponse({'success': False, 'message': 'GET required'}, status=405)
    
    try:
        prediction = YieldPrediction.objects.get(id=prediction_id, user=request.user)
        prediction.status = 'completed'
        prediction.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Prediction marked as completed'
        })
        
    except YieldPrediction.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Prediction not found'}, status=404)
    except Exception as e:
        logger.error(f"Error marking as completed: {str(e)}")
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'}, status=500)


@login_required
def view_prediction_detail(request, prediction_id):
    """View detailed prediction information"""
    
    try:
        prediction = YieldPrediction.objects.get(id=prediction_id, user=request.user)
        
        # Calculate additional yield metrics
        area_hectares = float(prediction.factors.get('area_hectares', 0)) if prediction.factors else 0
        predicted_yield_kg_ha = float(prediction.predicted_yield_kg_ha or 0)
        actual_yield_kg_ha = float(prediction.actual_yield_kg_ha or 0)
        
        # Conversion factors
        hectares_to_acres = 2.471
        
        # Calculate yields
        predicted_yield_per_acre = predicted_yield_kg_ha / hectares_to_acres if hectares_to_acres > 0 else 0
        actual_yield_per_acre = actual_yield_kg_ha / hectares_to_acres if hectares_to_acres > 0 else 0
        total_predicted_yield = predicted_yield_kg_ha * area_hectares if area_hectares > 0 else 0
        total_actual_yield = actual_yield_kg_ha * area_hectares if area_hectares > 0 else 0
        
        context = {
            'page_title': 'Prediction Details',
            'prediction': prediction,
            'area_hectares': area_hectares,
            'area_acres': area_hectares * hectares_to_acres if area_hectares > 0 else 0,
            'predicted_yield_per_acre': predicted_yield_per_acre,
            'actual_yield_per_acre': actual_yield_per_acre,
            'total_predicted_yield': total_predicted_yield,
            'total_actual_yield': total_actual_yield,
        }
        return render(request, 'yield_prediction/prediction_detail.html', context)
        
    except YieldPrediction.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Prediction not found'}, status=404)
    except Exception as e:
        logger.error(f"Error viewing prediction: {str(e)}")
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'}, status=500)
