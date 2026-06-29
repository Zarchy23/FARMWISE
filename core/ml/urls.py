"""
ML API URL Configuration
"""
from django.urls import path
from . import api

app_name = 'ml'

urlpatterns = [
    # Model Training Endpoints (Admin only)
    path('status/', api.model_status, name='model_status'),
    path('train/all/', api.train_all_models, name='train_all_models'),
    path('train/crop/', api.train_crop_model, name='train_crop_model'),
    path('train/equipment/', api.train_equipment_model, name='train_equipment_model'),
    path('train/financial/', api.train_financial_model, name='train_financial_model'),
    path('train/livestock/', api.train_livestock_model, name='train_livestock_model'),
    path('train/weather/', api.train_weather_model, name='train_weather_model'),
    path('train/pest/', api.train_pest_model, name='train_pest_model'),
    
    # Prediction Endpoints (Authenticated users)
    path('recommendations/farm/', api.get_farm_recommendations, name='farm_recommendations'),
    path('predict/crop-yield/', api.predict_crop_yield, name='predict_crop_yield'),
    path('predict/equipment-maintenance/', api.predict_equipment_maintenance, name='predict_equipment_maintenance'),
    path('forecast/financials/', api.forecast_financials, name='forecast_financials'),
    path('predict/livestock-health/', api.predict_livestock_health, name='predict_livestock_health'),
    path('recommendation/weather/', api.get_weather_recommendation, name='weather_recommendation'),
]
