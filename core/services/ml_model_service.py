"""
ML Model Integration Service
Integrates trained models with the core FarmWise application
"""

import json
import joblib
import warnings
from pathlib import Path
import numpy as np
from PIL import Image
import torch
import torchvision.transforms as transforms
from django.conf import settings
import logging

# Suppress torchvision deprecation warnings
warnings.filterwarnings('ignore', message='.*pretrained.*')

logger = logging.getLogger(__name__)


class MLModelService:
    """Service for loading and using trained ML models"""
    
    def __init__(self):
        self.models_dir = Path(settings.BASE_DIR) / 'ml_models'
        self.disease_model = None
        self.pest_model = None
        self.yield_model = None
        self.yield_scaler = None
        self.yield_features = None
        
        # Load models on initialization
        self._load_models()
    
    def _load_models(self):
        """Load all trained models"""
        try:
            # Load yield prediction model (simpler, no torch issues)
            yield_model_path = self.models_dir / 'yield' / 'model.pkl'
            yield_scaler_path = self.models_dir / 'yield' / 'scaler.pkl'
            yield_features_path = self.models_dir / 'yield' / 'features.json'
            
            if yield_model_path.exists():
                try:
                    self.yield_model = joblib.load(yield_model_path)
                    self.yield_scaler = joblib.load(yield_scaler_path)
                    
                    with open(yield_features_path, 'r') as f:
                        self.yield_features = json.load(f)
                    
                    logger.info("Yield prediction model loaded")
                except Exception as e:
                    logger.warning(f"Could not load yield model: {e}")
            
            # Load disease detection model
            disease_path = self.models_dir / 'disease_detection_model.pth'
            if disease_path.exists():
                try:
                    from torchvision.models import resnet50
                    self.disease_model = resnet50(weights=None)
                    self.disease_model.fc = torch.nn.Linear(self.disease_model.fc.in_features, 15)
                    state_dict = torch.load(disease_path, map_location='cpu')
                    
                    # Handle checkpoint format (may contain extra keys)
                    if isinstance(state_dict, dict) and 'model_state_dict' in state_dict:
                        state_dict = state_dict['model_state_dict']
                    
                    self.disease_model.load_state_dict(state_dict, strict=False)
                    self.disease_model.eval()
                    logger.info("Disease detection model loaded")
                except Exception as e:
                    logger.warning(f"Could not load disease model: {e}")
            
            # Load pest detection model
            pest_path = self.models_dir / 'pest_model' / 'best_pest_model.pth'
            if pest_path.exists():
                try:
                    from torchvision.models import resnet50
                    self.pest_model = resnet50(weights=None)
                    self.pest_model.fc = torch.nn.Linear(self.pest_model.fc.in_features, 27)
                    state_dict = torch.load(pest_path, map_location='cpu')
                    
                    # Handle checkpoint format (may contain extra keys)
                    if isinstance(state_dict, dict) and 'model_state_dict' in state_dict:
                        state_dict = state_dict['model_state_dict']
                    
                    self.pest_model.load_state_dict(state_dict, strict=False)
                    self.pest_model.eval()
                    logger.info("Pest detection model loaded")
                except Exception as e:
                    logger.warning(f"Could not load pest model: {e}")
                
        except Exception as e:
            logger.error(f"Error loading models: {e}")
    
    def predict_disease(self, image_path):
        """
        Predict disease from plant image
        
        Args:
            image_path: Path to image file
        
        Returns:
            Dict with predicted disease and confidence
        """
        if self.disease_model is None:
            return {'error': 'Disease model not available'}
        
        try:
            # Load and preprocess image
            image = Image.open(image_path).convert('RGB')
            transform = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])
            image_tensor = transform(image).unsqueeze(0)
            
            # Predict
            with torch.no_grad():
                outputs = self.disease_model(image_tensor)
                probabilities = torch.nn.functional.softmax(outputs[0], dim=0)
                predicted_class = torch.argmax(probabilities).item()
                confidence = probabilities[predicted_class].item()
            
            # Disease class names (from training)
            disease_classes = [
                'Pepper__bell___Bacterial_spot', 'Pepper__bell___healthy',
                'Potato___Early_blight', 'Potato___healthy', 'Potato___Late_blight',
                'Tomato__Target_Spot', 'Tomato__Tomato_mosaic_virus',
                'Tomato__Tomato_YellowLeaf__Curl_Virus', 'Tomato_Bacterial_spot',
                'Tomato_Early_blight', 'Tomato_healthy', 'Tomato_Late_blight',
                'Tomato_Leaf_Mold', 'Tomato_Septoria_leaf_spot',
                'Tomato_Spider_mites_Two_spotted_spider_mite'
            ]
            
            predicted_disease = disease_classes[predicted_class] if predicted_class < len(disease_classes) else 'Unknown'
            
            return {
                'disease': predicted_disease,
                'confidence': confidence,
                'class_index': predicted_class
            }
            
        except Exception as e:
            logger.error(f"Disease prediction error: {e}")
            return {'error': str(e)}
    
    def predict_pest(self, image_path):
        """
        Predict pest from image
        
        Args:
            image_path: Path to image file
        
        Returns:
            Dict with predicted pest and confidence
        """
        if self.pest_model is None:
            return {'error': 'Pest model not available'}
        
        try:
            # Load and preprocess image
            image = Image.open(image_path).convert('RGB')
            transform = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])
            image_tensor = transform(image).unsqueeze(0)
            
            # Predict
            with torch.no_grad():
                outputs = self.pest_model(image_tensor)
                probabilities = torch.nn.functional.softmax(outputs[0], dim=0)
                predicted_class = torch.argmax(probabilities).item()
                confidence = probabilities[predicted_class].item()
            
            # Pest class names (from training)
            pest_classes = [
                'ant', 'bee', 'bee_apis', 'bee_bombus', 'beetle', 'beetle_cocci',
                'beetle_oedem', 'bug', 'bug_grapho', 'fly', 'fly_empi', 'fly_sarco',
                'fly_small', 'hfly_episyr', 'hfly_eristal', 'hfly_eupeo', 'hfly_myathr',
                'hfly_sphaero', 'hfly_syrphus', 'lepi', 'none_bg', 'none_bird',
                'none_dirt', 'none_shadow', 'other', 'scorpionfly', 'wasp'
            ]
            
            predicted_pest = pest_classes[predicted_class] if predicted_class < len(pest_classes) else 'Unknown'
            
            return {
                'pest': predicted_pest,
                'confidence': confidence,
                'class_index': predicted_class
            }
            
        except Exception as e:
            logger.error(f"Pest prediction error: {e}")
            return {'error': str(e)}
    
    def predict_yield(self, features):
        """
        Predict crop yield from features
        
        Args:
            features: Dict with feature values
        
        Returns:
            Dict with predicted yield in kg/ha
        """
        if self.yield_model is None or self.yield_scaler is None:
            return {'error': 'Yield model not available'}
        
        try:
            import pandas as pd
            
            # Convert to DataFrame
            df = pd.DataFrame([features])
            
            # Ensure all features exist
            for feat in self.yield_features:
                if feat not in df.columns:
                    df[feat] = 0
            
            # Select only required features
            df = df[self.yield_features]
            
            # Scale features
            X_scaled = self.yield_scaler.transform(df)
            
            # Predict
            prediction = self.yield_model.predict(X_scaled)[0]
            
            return {
                'predicted_yield_kg_per_hectare': float(prediction),
                'features_used': self.yield_features
            }
            
        except Exception as e:
            logger.error(f"Yield prediction error: {e}")
            return {'error': str(e)}
    
    def get_model_status(self):
        """Get status of all loaded models"""
        return {
            'disease_model': self.disease_model is not None,
            'pest_model': self.pest_model is not None,
            'yield_model': self.yield_model is not None,
            'models_dir': str(self.models_dir)
        }


# Singleton instance
ml_service = MLModelService()
