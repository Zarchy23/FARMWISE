"""
Enhanced Pest/Disease Detection Model
Custom training for improved pest and disease detection
"""
import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
from sklearn.preprocessing import StandardScaler, LabelEncoder
from django.conf import settings


class PestDetectionEnhancer:
    """Enhance pest detection with custom ML training"""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_columns = None
        self.model_path = os.path.join(settings.BASE_DIR, 'ml_models', 'pest_detection_model.pkl')
        self.scaler_path = os.path.join(settings.BASE_DIR, 'ml_models', 'pest_detection_scaler.pkl')
        
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
    
    def prepare_features(self, df):
        """Prepare and encode features for training/prediction"""
        df = df.copy()
        
        # Encode categorical variables
        categorical_cols = ['crop_type', 'ai_diagnosis', 'verified_diagnosis']
        for col in categorical_cols:
            if col in df.columns:
                if col not in self.label_encoders:
                    self.label_encoders[col] = LabelEncoder()
                    df[col + '_encoded'] = self.label_encoders[col].fit_transform(df[col].astype(str))
                else:
                    df[col + '_encoded'] = self.label_encoders[col].transform(df[col].astype(str))
        
        # Select feature columns
        feature_cols = [
            'severity', 'confidence_score', 'month', 'season',
            'crop_type_encoded', 'ai_diagnosis_encoded'
        ]
        
        self.feature_columns = [col for col in feature_cols if col in df.columns]
        df[self.feature_columns] = df[self.feature_columns].fillna(0)
        
        return df[self.feature_columns]
    
    def train(self, df=None):
        """Train the pest detection enhancement model"""
        from core.ml.data_pipeline import DataPipeline
        
        if df is None or df.empty:
            df = DataPipeline.get_pest_detection_data()
        
        if df.empty:
            raise ValueError("No training data available")
        
        # Filter to verified reports for training
        verified_df = df[df['is_verified'] == True].copy()
        
        if verified_df.empty:
            # Use all data if no verified reports
            verified_df = df.copy()
        
        # Create target: whether AI diagnosis was correct
        verified_df['ai_correct'] = (
            verified_df['ai_diagnosis'] == verified_df['verified_diagnosis']
        ).astype(int)
        
        X = self.prepare_features(verified_df)
        y = verified_df['ai_correct'].values
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Use Random Forest for classification
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
        
        # Get common pest types
        pest_types = df['ai_diagnosis'].value_counts().head(10).to_dict()
        
        metrics = {
            'accuracy': accuracy,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std(),
            'classification_report': classification_report(y_test, y_pred, output_dict=True),
            'common_pest_types': pest_types,
            'total_reports': len(df),
            'verified_reports': len(verified_df)
        }
        
        self.save()
        return metrics
    
    def predict_diagnosis_confidence(self, features):
        """Predict confidence in AI diagnosis"""
        if self.model is None:
            self.load()
        
        if isinstance(features, dict):
            features = pd.DataFrame([features])
        
        X = self.prepare_features(features)
        X_scaled = self.scaler.transform(X)
        
        prediction = self.model.predict(X_scaled)[0]
        probability = self.model.predict_proba(X_scaled)[0]
        
        return {
            'ai_diagnosis_reliable': bool(prediction),
            'confidence': float(probability[1]),
            'recommendation': self._get_recommendation(probability[1])
        }
    
    def _get_recommendation(self, probability):
        """Get recommendation based on confidence"""
        if probability > 0.8:
            return 'High confidence - trust AI diagnosis'
        elif probability > 0.5:
            return 'Medium confidence - recommend verification'
        else:
            return 'Low confidence - manual verification required'
    
    def get_diagnosis_patterns(self, df=None):
        """Analyze patterns in pest detection data"""
        from core.ml.data_pipeline import DataPipeline
        
        if df is None or df.empty:
            df = DataPipeline.get_pest_detection_data()
        
        if df.empty:
            return {'error': 'No data available'}
        
        patterns = {
            'by_crop_type': df['crop_type'].value_counts().to_dict(),
            'by_severity': df['severity'].value_counts().to_dict(),
            'by_season': df.groupby('season').size().to_dict(),
            'verification_rate': df['is_verified'].mean(),
            'accuracy_by_crop': {}
        }
        
        # Calculate accuracy by crop type
        verified_df = df[df['is_verified'] == True]
        if not verified_df.empty:
            for crop in verified_df['crop_type'].unique():
                crop_data = verified_df[verified_df['crop_type'] == crop]
                accuracy = (crop_data['ai_diagnosis'] == crop_data['verified_diagnosis']).mean()
                patterns['accuracy_by_crop'][crop] = accuracy
        
        return patterns
    
    def save(self):
        """Save model and scaler"""
        joblib.dump(self.model, self.model_path)
        joblib.dump(self.scaler, self.scaler_path)
        joblib.dump(self.label_encoders,
                    os.path.join(settings.BASE_DIR, 'ml_models', 'pest_encoders.pkl'))
        joblib.dump(self.feature_columns,
                    os.path.join(settings.BASE_DIR, 'ml_models', 'pest_features.pkl'))
    
    def load(self):
        """Load model and scaler"""
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
            self.scaler = joblib.load(self.scaler_path)
            self.label_encoders = joblib.load(
                os.path.join(settings.BASE_DIR, 'ml_models', 'pest_encoders.pkl')
            )
            self.feature_columns = joblib.load(
                os.path.join(settings.BASE_DIR, 'ml_models', 'pest_features.pkl')
            )
        else:
            raise FileNotFoundError("Model not found. Please train the model first.")
    
    def get_feature_importance(self):
        """Get feature importance"""
        if self.model is None:
            self.load()
        
        importance = dict(zip(self.feature_columns, self.model.feature_importances_))
        return sorted(importance.items(), key=lambda x: x[1], reverse=True)
