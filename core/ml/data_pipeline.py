"""
Data Collection and Preprocessing Pipeline
Handles data extraction, cleaning, and feature engineering for ML models
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from django.db.models import Sum, Avg, Count, F
from core.models import CropSeason, Harvest, Animal, HealthRecord, Equipment, EquipmentBooking, Transaction, PestReport


class DataPipeline:
    """Central data pipeline for ML model training and inference"""
    
    @staticmethod
    def get_crop_yield_data(farm_id=None, days=365):
        """
        Collect crop yield data with features for prediction
        Returns DataFrame with features and target (yield)
        """
        from django.utils import timezone
        
        cutoff_date = timezone.now() - timedelta(days=days)
        
        queryset = CropSeason.objects.filter(
            planting_date__gte=cutoff_date
        ).select_related('crop_type', 'field', 'field__farm')
        
        if farm_id:
            queryset = queryset.filter(field__farm_id=farm_id)
        
        data = []
        for crop in queryset:
            # Get harvest data if available
            harvest = Harvest.objects.filter(crop_season=crop).first()
            yield_kg = harvest.quantity_kg if harvest else 0
            
            # Calculate growing season length
            growing_days = 0
            if crop.harvest_date and crop.planting_date:
                growing_days = (crop.harvest_date - crop.planting_date).days
            
            # Get weather data (simplified - would integrate with weather API)
            # For now, use seasonal averages
            
            feature = {
                'crop_type': crop.crop_type.name if crop.crop_type else 'unknown',
                'area_hectares': crop.area_hectares or 0,
                'planting_month': crop.planting_date.month if crop.planting_date else 0,
                'growing_days': growing_days,
                'soil_type': crop.field.soil_type if crop.field else 'unknown',
                'irrigation_type': crop.field.irrigation_type if crop.field else 'unknown',
                'fertilizer_amount': crop.fertilizer_amount or 0,
                'water_usage': crop.water_usage or 0,
                'target_yield': yield_kg,
                'yield_per_hectare': yield_kg / (crop.area_hectares or 1),
            }
            data.append(feature)
        
        return pd.DataFrame(data)
    
    @staticmethod
    def get_equipment_maintenance_data(farm_id=None, days=365):
        """
        Collect equipment usage and maintenance data for predictive maintenance
        """
        from django.utils import timezone
        
        cutoff_date = timezone.now() - timedelta(days=days)
        
        equipment = Equipment.objects.filter(
            created_at__gte=cutoff_date
        ).select_related('equipment_type')
        
        if farm_id:
            equipment = equipment.filter(farm_id=farm_id)
        
        data = []
        for eq in equipment:
            bookings = EquipmentBooking.objects.filter(
                equipment=eq,
                start_date__gte=cutoff_date
            )
            
            total_usage_hours = bookings.aggregate(
                total=Sum(F('end_date') - F('start_date'))
            )['total'] or timedelta(0)
            total_usage_hours = total_usage_hours.total_seconds() / 3600
            
            # Calculate days since last maintenance
            days_since_maintenance = 0
            if eq.last_maintenance_date:
                days_since_maintenance = (timezone.now().date() - eq.last_maintenance_date).days
            
            feature = {
                'equipment_type': eq.equipment_type.name if eq.equipment_type else 'unknown',
                'age_days': (timezone.now().date() - eq.purchase_date.date()).days if eq.purchase_date else 0,
                'total_usage_hours': total_usage_hours,
                'days_since_maintenance': days_since_maintenance,
                'maintenance_interval_days': eq.maintenance_interval or 90,
                'status': eq.status,
                'needs_maintenance': 1 if eq.status == 'maintenance_due' else 0,
            }
            data.append(feature)
        
        return pd.DataFrame(data)
    
    @staticmethod
    def get_financial_data(farm_id=None, days=365):
        """
        Collect financial transaction data for forecasting
        """
        from django.utils import timezone
        
        cutoff_date = timezone.now() - timedelta(days=days)
        
        transactions = Transaction.objects.filter(
            date__gte=cutoff_date
        )
        
        if farm_id:
            transactions = transactions.filter(farm_id=farm_id)
        
        data = []
        for txn in transactions:
            feature = {
                'date': txn.date,
                'transaction_type': txn.transaction_type,
                'category': txn.category,
                'amount': float(txn.amount),
                'month': txn.date.month,
                'day_of_week': txn.date.weekday(),
                'day_of_month': txn.date.day,
                'is_weekend': 1 if txn.date.weekday() >= 5 else 0,
            }
            data.append(feature)
        
        df = pd.DataFrame(data)
        if not df.empty:
            df['cumulative_sum'] = df.groupby('transaction_type')['amount'].cumsum()
            df['rolling_avg_7'] = df.groupby('transaction_type')['amount'].transform(
                lambda x: x.rolling(7, min_periods=1).mean()
            )
        
        return df
    
    @staticmethod
    def get_livestock_health_data(farm_id=None, days=365):
        """
        Collect livestock health data for health monitoring
        """
        from django.utils import timezone
        
        cutoff_date = timezone.now() - timedelta(days=days)
        
        animals = Animal.objects.filter(
            birth_date__gte=cutoff_date
        ).select_related('animal_type')
        
        if farm_id:
            animals = animals.filter(farm_id=farm_id)
        
        data = []
        for animal in animals:
            health_records = HealthRecord.objects.filter(
                animal=animal,
                date__gte=cutoff_date
            )
            
            avg_weight = health_records.aggregate(avg=Avg('weight'))['avg'] or 0
            health_issues_count = health_records.filter(
                health_status__in=['sick', 'injured']
            ).count()
            
            feature = {
                'animal_type': animal.animal_type if animal.animal_type else 'unknown',
                'age_days': (timezone.now().date() - animal.birth_date.date()).days if animal.birth_date else 0,
                'gender': animal.gender,
                'avg_weight': avg_weight,
                'health_issues_count': health_issues_count,
                'current_status': animal.status,
                'health_risk': 1 if animal.status != 'alive' else 0,
            }
            data.append(feature)
        
        return pd.DataFrame(data)
    
    @staticmethod
    def get_iot_sensor_data(farm_id=None, days=30):
        """
        Collect IoT sensor data for various predictions
        """
        from django.utils import timezone
        
        cutoff_date = timezone.now() - timedelta(days=days)
        
        try:
            from core.models_iot import SensorDataPoint, IoTDevice
            
            data_points = SensorDataPoint.objects.filter(
                server_timestamp__gte=cutoff_date
            ).select_related('device', 'sensor_config')
            
            if farm_id:
                data_points = data_points.filter(device__farm_id=farm_id)
            
            data = []
            for dp in data_points:
                feature = {
                    'device_id': dp.device.id,
                    'sensor_type': dp.sensor_config.sensor_type if dp.sensor_config else 'unknown',
                    'value': float(dp.value),
                    'signal_strength': dp.signal_strength,
                    'is_valid': 1 if dp.is_valid else 0,
                    'timestamp': dp.server_timestamp,
                    'hour': dp.server_timestamp.hour,
                    'day_of_week': dp.server_timestamp.weekday(),
                }
                data.append(feature)
            
            return pd.DataFrame(data)
        except:
            return pd.DataFrame()
    
    @staticmethod
    def get_pest_detection_data(farm_id=None, days=365):
        """
        Collect pest detection data for training/improving detection models
        """
        from django.utils import timezone
        
        cutoff_date = timezone.now() - timedelta(days=days)
        
        reports = PestReport.objects.filter(
            created_at__gte=cutoff_date
        ).select_related('crop_season', 'crop_season__crop_type')
        
        if farm_id:
            reports = reports.filter(crop_season__field__farm_id=farm_id)
        
        data = []
        for report in reports:
            feature = {
                'crop_type': report.crop_season.crop_type.name if report.crop_season and report.crop_season.crop_type else 'unknown',
                'severity': report.severity,
                'ai_diagnosis': report.ai_diagnosis,
                'verified_diagnosis': report.verified_diagnosis,
                'is_verified': report.is_verified,
                'confidence_score': report.confidence_score or 0,
                'month': report.created_at.month,
                'season': report.created_at.month % 12 // 3 + 1,  # 1-4 seasons
            }
            data.append(feature)
        
        return pd.DataFrame(data)
    
    @staticmethod
    def preprocess_features(df, categorical_columns=None, numerical_columns=None):
        """
        Preprocess features: handle missing values, encode categoricals, scale numericals
        """
        from sklearn.preprocessing import StandardScaler, LabelEncoder
        
        df_processed = df.copy()
        
        # Handle missing values
        df_processed = df_processed.fillna(0)
        
        # Encode categorical columns
        if categorical_columns:
            for col in categorical_columns:
                if col in df_processed.columns:
                    le = LabelEncoder()
                    df_processed[col + '_encoded'] = le.fit_transform(df_processed[col].astype(str))
        
        # Scale numerical columns
        if numerical_columns:
            scaler = StandardScaler()
            for col in numerical_columns:
                if col in df_processed.columns:
                    df_processed[col + '_scaled'] = scaler.fit_transform(
                        df_processed[[col]]
                    )
        
        return df_processed
    
    @staticmethod
    def create_time_series_features(df, date_column='date', target_column='amount'):
        """
        Create time series features for forecasting models
        """
        df = df.copy()
        df[date_column] = pd.to_datetime(df[date_column])
        df = df.sort_values(date_column)
        
        # Lag features
        for lag in [1, 7, 30]:
            df[f'{target_column}_lag_{lag}'] = df[target_column].shift(lag)
        
        # Rolling statistics
        df[f'{target_column}_rolling_mean_7'] = df[target_column].rolling(7).mean()
        df[f'{target_column}_rolling_std_7'] = df[target_column].rolling(7).std()
        
        # Date features
        df['year'] = df[date_column].dt.year
        df['month'] = df[date_column].dt.month
        df['day'] = df[date_column].dt.day
        df['day_of_week'] = df[date_column].dt.dayofweek
        df['is_month_start'] = df[date_column].dt.is_month_start.astype(int)
        df['is_month_end'] = df[date_column].dt.is_month_end.astype(int)
        
        return df.fillna(0)
