"""
Crop Yield Prediction Model
Uses historical crop data to predict future yields
"""
import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from django.conf import settings


class CropYieldPredictor:
    """Predict crop yields based on historical data and environmental factors"""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_columns = None
        self.model_path = os.path.join(settings.BASE_DIR, 'ml_models', 'crop_yield_model.pkl')
        self.scaler_path = os.path.join(settings.BASE_DIR, 'ml_models', 'crop_yield_scaler.pkl')
        
        # Create models directory if it doesn't exist
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
    
    def prepare_features(self, df):
        """Prepare and encode features for training/prediction"""
        df = df.copy()
        
        # Encode categorical variables
        categorical_cols = ['crop_type', 'soil_type', 'irrigation_type']
        for col in categorical_cols:
            if col in df.columns:
                if col not in self.label_encoders:
                    self.label_encoders[col] = LabelEncoder()
                    df[col + '_encoded'] = self.label_encoders[col].fit_transform(df[col].astype(str))
                else:
                    df[col + '_encoded'] = self.label_encoders[col].transform(df[col].astype(str))
        
        # Select feature columns
        feature_cols = [
            'area_hectares', 'planting_month', 'growing_days',
            'fertilizer_amount', 'water_usage',
            'crop_type_encoded', 'soil_type_encoded', 'irrigation_type_encoded'
        ]
        
        # Filter to only available columns
        self.feature_columns = [col for col in feature_cols if col in df.columns]
        
        # Handle missing values
        df[self.feature_columns] = df[self.feature_columns].fillna(0)
        
        return df[self.feature_columns]
    
    def train(self, df, target_column='yield_per_hectare'):
        """Train the crop yield prediction model"""
        from core.ml.data_pipeline import DataPipeline
        
        # Get and prepare data
        if df is None or df.empty:
            df = DataPipeline.get_crop_yield_data()
        
        if df.empty or target_column not in df.columns:
            raise ValueError("No training data available")
        
        # Prepare features
        X = self.prepare_features(df)
        y = df[target_column].values
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model - use Gradient Boosting for better accuracy
        self.model = GradientBoostingRegressor(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=6,
            random_state=42
        )
        
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test_scaled)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)
        
        # Cross-validation
        cv_scores = cross_val_score(self.model, X_train_scaled, y_train, cv=5)
        
        metrics = {
            'mae': mae,
            'rmse': rmse,
            'r2': r2,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std()
        }
        
        # Save model
        self.save()
        
        return metrics
    
    def predict(self, features):
        """Predict yield for given features"""
        if self.model is None:
            self.load()
        
        if isinstance(features, dict):
            features = pd.DataFrame([features])
        
        X = self.prepare_features(features)
        X_scaled = self.scaler.transform(X)
        
        predictions = self.model.predict(X_scaled)
        
        return predictions
    
    def predict_batch(self, df):
        """Predict yields for multiple crops"""
        if self.model is None:
            self.load()
        
        X = self.prepare_features(df)
        X_scaled = self.scaler.transform(X)
        
        predictions = self.model.predict(X_scaled)
        
        return predictions
    
    def save(self):
        """Save model and scaler to disk"""
        joblib.dump(self.model, self.model_path)
        joblib.dump(self.scaler, self.scaler_path)
        joblib.dump(self.label_encoders, 
                    os.path.join(settings.BASE_DIR, 'ml_models', 'crop_yield_encoders.pkl'))
        joblib.dump(self.feature_columns,
                    os.path.join(settings.BASE_DIR, 'ml_models', 'crop_yield_features.pkl'))
    
    def load(self):
        """Load model and scaler from disk"""
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
            self.scaler = joblib.load(self.scaler_path)
            self.label_encoders = joblib.load(
                os.path.join(settings.BASE_DIR, 'ml_models', 'crop_yield_encoders.pkl')
            )
            self.feature_columns = joblib.load(
                os.path.join(settings.BASE_DIR, 'ml_models', 'crop_yield_features.pkl')
            )
        else:
            raise FileNotFoundError("Model not found. Please train the model first.")
    
    def get_feature_importance(self):
        """Get feature importance from the trained model"""
        if self.model is None:
            self.load()
        
        importance = dict(zip(self.feature_columns, self.model.feature_importances_))
        return sorted(importance.items(), key=lambda x: x[1], reverse=True)
