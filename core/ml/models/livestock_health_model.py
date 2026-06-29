"""
Livestock Health Monitoring Model
Predicts health risks and issues in livestock
"""
import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, accuracy_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from django.conf import settings


class LivestockHealthPredictor:
    """Predict livestock health risks based on historical data"""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_columns = None
        self.model_path = os.path.join(settings.BASE_DIR, 'ml_models', 'livestock_health_model.pkl')
        self.scaler_path = os.path.join(settings.BASE_DIR, 'ml_models', 'livestock_health_scaler.pkl')
        
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
    
    def prepare_features(self, df):
        """Prepare and encode features for training/prediction"""
        df = df.copy()
        
        # Encode categorical variables
        categorical_cols = ['animal_type', 'gender', 'current_status']
        for col in categorical_cols:
            if col in df.columns:
                if col not in self.label_encoders:
                    self.label_encoders[col] = LabelEncoder()
                    df[col + '_encoded'] = self.label_encoders[col].fit_transform(df[col].astype(str))
                else:
                    df[col + '_encoded'] = self.label_encoders[col].transform(df[col].astype(str))
        
        # Select feature columns
        feature_cols = [
            'age_days', 'avg_weight', 'health_issues_count',
            'animal_type_encoded', 'gender_encoded', 'current_status_encoded'
        ]
        
        self.feature_columns = [col for col in feature_cols if col in df.columns]
        df[self.feature_columns] = df[self.feature_columns].fillna(0)
        
        return df[self.feature_columns]
    
    def train(self, df=None, target_column='health_risk'):
        """Train the livestock health prediction model"""
        from core.ml.data_pipeline import DataPipeline
        
        if df is None or df.empty:
            df = DataPipeline.get_livestock_health_data()
        
        if df.empty or target_column not in df.columns:
            raise ValueError("No training data available")
        
        X = self.prepare_features(df)
        y = df[target_column].values
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            class_weight='balanced'
        )
        
        self.model.fit(X_train_scaled, y_train)
        
        y_pred = self.model.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)
        
        cv_scores = cross_val_score(self.model, X_train_scaled, y_train, cv=5)
        
        metrics = {
            'accuracy': accuracy,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std(),
            'classification_report': classification_report(y_test, y_pred, output_dict=True)
        }
        
        self.save()
        return metrics
    
    def predict(self, features):
        """Predict health risk for given animal"""
        if self.model is None:
            self.load()
        
        if isinstance(features, dict):
            features = pd.DataFrame([features])
        
        X = self.prepare_features(features)
        X_scaled = self.scaler.transform(X)
        
        prediction = self.model.predict(X_scaled)[0]
        probability = self.model.predict_proba(X_scaled)[0]
        
        return {
            'health_risk': bool(prediction),
            'risk_probability': float(probability[1]),
            'risk_level': self._get_risk_level(probability[1])
        }
    
    def predict_batch(self, df):
        """Predict health risks for multiple animals"""
        if self.model is None:
            self.load()
        
        X = self.prepare_features(df)
        X_scaled = self.scaler.transform(X)
        
        predictions = self.model.predict(X_scaled)
        probabilities = self.model.predict_proba(X_scaled)
        
        results = []
        for i, (pred, prob) in enumerate(zip(predictions, probabilities)):
            results.append({
                'health_risk': bool(pred),
                'risk_probability': float(prob[1]),
                'risk_level': self._get_risk_level(prob[1])
            })
        
        return results
    
    def _get_risk_level(self, probability):
        """Categorize risk level based on probability"""
        if probability < 0.3:
            return 'low'
        elif probability < 0.6:
            return 'medium'
        else:
            return 'high'
    
    def save(self):
        """Save model and scaler"""
        joblib.dump(self.model, self.model_path)
        joblib.dump(self.scaler, self.scaler_path)
        joblib.dump(self.label_encoders,
                    os.path.join(settings.BASE_DIR, 'ml_models', 'livestock_encoders.pkl'))
        joblib.dump(self.feature_columns,
                    os.path.join(settings.BASE_DIR, 'ml_models', 'livestock_features.pkl'))
    
    def load(self):
        """Load model and scaler"""
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
            self.scaler = joblib.load(self.scaler_path)
            self.label_encoders = joblib.load(
                os.path.join(settings.BASE_DIR, 'ml_models', 'livestock_encoders.pkl')
            )
            self.feature_columns = joblib.load(
                os.path.join(settings.BASE_DIR, 'ml_models', 'livestock_features.pkl')
            )
        else:
            raise FileNotFoundError("Model not found. Please train the model first.")
    
    def get_feature_importance(self):
        """Get feature importance"""
        if self.model is None:
            self.load()
        
        importance = dict(zip(self.feature_columns, self.model.feature_importances_))
        return sorted(importance.items(), key=lambda x: x[1], reverse=True)
