"""
Weather-Based Recommendation Engine
Provides farming recommendations based on weather patterns
"""
import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from django.conf import settings


class WeatherRecommendationEngine:
    """Generate farming recommendations based on weather data"""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_columns = None
        self.model_path = os.path.join(settings.BASE_DIR, 'ml_models', 'weather_recommendation_model.pkl')
        self.scaler_path = os.path.join(settings.BASE_DIR, 'ml_models', 'weather_recommendation_scaler.pkl')
        
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
    
    def prepare_features(self, df):
        """Prepare weather features for recommendation"""
        df = df.copy()
        
        # Encode categorical variables
        categorical_cols = ['season', 'crop_type']
        for col in categorical_cols:
            if col in df.columns:
                if col not in self.label_encoders:
                    self.label_encoders[col] = LabelEncoder()
                    df[col + '_encoded'] = self.label_encoders[col].fit_transform(df[col].astype(str))
                else:
                    df[col + '_encoded'] = self.label_encoders[col].transform(df[col].astype(str))
        
        # Select feature columns
        feature_cols = [
            'temperature', 'humidity', 'rainfall', 'wind_speed',
            'soil_moisture', 'season_encoded', 'crop_type_encoded'
        ]
        
        self.feature_columns = [col for col in feature_cols if col in df.columns]
        df[self.feature_columns] = df[self.feature_columns].fillna(0)
        
        return df[self.feature_columns]
    
    def train(self, df=None):
        """Train the recommendation engine with historical data"""
        # For this model, we'll use a rule-based approach combined with ML
        # since weather recommendations often follow agricultural best practices
        
        # Create synthetic training data based on agricultural rules
        if df is None or df.empty:
            df = self._create_synthetic_training_data()
        
        X = self.prepare_features(df)
        y = df['recommendation'].values
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        
        self.model.fit(X_train_scaled, y_train)
        
        y_pred = self.model.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)
        
        self.save()
        return {'accuracy': accuracy}
    
    def _create_synthetic_training_data(self):
        """Create synthetic training data based on agricultural best practices"""
        data = []
        
        # Define weather conditions and corresponding recommendations
        scenarios = [
            # Hot, dry conditions
            {'temperature': 35, 'humidity': 30, 'rainfall': 0, 'wind_speed': 10, 'soil_moisture': 20, 'season': 'summer', 'crop_type': 'maize', 'recommendation': 'increase_irrigation'},
            {'temperature': 38, 'humidity': 25, 'rainfall': 0, 'wind_speed': 15, 'soil_moisture': 15, 'season': 'summer', 'crop_type': 'wheat', 'recommendation': 'increase_irrigation'},
            
            # Heavy rain conditions
            {'temperature': 22, 'humidity': 90, 'rainfall': 50, 'wind_speed': 5, 'soil_moisture': 80, 'season': 'rainy', 'crop_type': 'rice', 'recommendation': 'reduce_irrigation'},
            {'temperature': 20, 'humidity': 95, 'rainfall': 80, 'wind_speed': 8, 'soil_moisture': 90, 'season': 'rainy', 'crop_type': 'maize', 'recommendation': 'apply_fungicide'},
            
            # Optimal conditions
            {'temperature': 25, 'humidity': 60, 'rainfall': 10, 'wind_speed': 5, 'soil_moisture': 50, 'season': 'spring', 'crop_type': 'tomato', 'recommendation': 'normal_operations'},
            {'temperature': 24, 'humidity': 65, 'rainfall': 15, 'wind_speed': 6, 'soil_moisture': 55, 'season': 'spring', 'crop_type': 'potato', 'recommendation': 'normal_operations'},
            
            # Cold conditions
            {'temperature': 10, 'humidity': 70, 'rainfall': 5, 'wind_speed': 12, 'soil_moisture': 40, 'season': 'winter', 'crop_type': 'wheat', 'recommendation': 'apply_frost_protection'},
            {'temperature': 5, 'humidity': 80, 'rainfall': 2, 'wind_speed': 15, 'soil_moisture': 35, 'season': 'winter', 'crop_type': 'barley', 'recommendation': 'apply_frost_protection'},
            
            # High wind conditions
            {'temperature': 28, 'humidity': 50, 'rainfall': 5, 'wind_speed': 25, 'soil_moisture': 45, 'season': 'autumn', 'crop_type': 'maize', 'recommendation': 'secure_structures'},
            {'temperature': 26, 'humidity': 55, 'rainfall': 8, 'wind_speed': 30, 'soil_moisture': 48, 'season': 'autumn', 'crop_type': 'sugarcane', 'recommendation': 'secure_structures'},
        ]
        
        # Add variations to create more training data
        for scenario in scenarios:
            for i in range(10):
                data.append({
                    **scenario,
                    'temperature': scenario['temperature'] + np.random.uniform(-3, 3),
                    'humidity': max(0, min(100, scenario['humidity'] + np.random.uniform(-10, 10))),
                    'rainfall': max(0, scenario['rainfall'] + np.random.uniform(-5, 5)),
                    'wind_speed': max(0, scenario['wind_speed'] + np.random.uniform(-3, 3)),
                    'soil_moisture': max(0, min(100, scenario['soil_moisture'] + np.random.uniform(-5, 5))),
                })
        
        return pd.DataFrame(data)
    
    def get_recommendation(self, weather_data, crop_type):
        """Get farming recommendation based on weather and crop type"""
        if self.model is None:
            self.load()
        
        # Determine season from month
        from datetime import datetime
        month = datetime.now().month
        if month in [12, 1, 2]:
            season = 'winter'
        elif month in [3, 4, 5]:
            season = 'spring'
        elif month in [6, 7, 8]:
            season = 'summer'
        else:
            season = 'autumn'
        
        features = {
            'temperature': weather_data.get('temperature', 25),
            'humidity': weather_data.get('humidity', 60),
            'rainfall': weather_data.get('rainfall', 0),
            'wind_speed': weather_data.get('wind_speed', 5),
            'soil_moisture': weather_data.get('soil_moisture', 50),
            'season': season,
            'crop_type': crop_type
        }
        
        df = pd.DataFrame([features])
        X = self.prepare_features(df)
        X_scaled = self.scaler.transform(X)
        
        recommendation = self.model.predict(X_scaled)[0]
        probability = self.model.predict_proba(X_scaled)[0]
        confidence = float(max(probability))
        
        return {
            'recommendation': recommendation,
            'confidence': confidence,
            'weather_conditions': weather_data,
            'priority': self._get_priority(recommendation)
        }
    
    def _get_priority(self, recommendation):
        """Determine priority level for recommendation"""
        high_priority = ['increase_irrigation', 'apply_fungicide', 'apply_frost_protection', 'secure_structures']
        medium_priority = ['reduce_irrigation', 'apply_fertilizer']
        
        if recommendation in high_priority:
            return 'high'
        elif recommendation in medium_priority:
            return 'medium'
        else:
            return 'low'
    
    def save(self):
        """Save model and scaler"""
        joblib.dump(self.model, self.model_path)
        joblib.dump(self.scaler, self.scaler_path)
        joblib.dump(self.label_encoders,
                    os.path.join(settings.BASE_DIR, 'ml_models', 'weather_encoders.pkl'))
        joblib.dump(self.feature_columns,
                    os.path.join(settings.BASE_DIR, 'ml_models', 'weather_features.pkl'))
    
    def load(self):
        """Load model and scaler"""
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
            self.scaler = joblib.load(self.scaler_path)
            self.label_encoders = joblib.load(
                os.path.join(settings.BASE_DIR, 'ml_models', 'weather_encoders.pkl')
            )
            self.feature_columns = joblib.load(
                os.path.join(settings.BASE_DIR, 'ml_models', 'weather_features.pkl')
            )
        else:
            raise FileNotFoundError("Model not found. Please train the model first.")
