"""
ML Model Interface for Predictive Crop Storage Management System
Loads and uses the trained XGBoost model for damage predictions

"""

import pickle
import numpy as np
import logging
from typing import Optional
import os
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelPredictor:
    """
    Handles loading and using the trained XGBoost model for predictions
    """
    
    _instance = None
    _model = None
    _model_loaded = False
    
    def __new__(cls, model_path: str = None):
        if cls._instance is None:
            cls._instance = super(ModelPredictor, cls).__new__(cls)
            cls._instance._initialize_model(model_path)
        return cls._instance
    
    def _initialize_model(self, model_path: str):
        """Initialize the model"""
        # If no path provided, construct path relative to this file's location
        if model_path is None:
            # Get the directory containing this file (model.py)
            current_file_dir = Path(__file__).parent
            # models folder is in the SAME directory as model.py (both at root)
            model_path = current_file_dir / "models" / "best_xgb_model.pkl"
        
        self.model_path = Path(model_path)
        self._load_model()
    
    def _load_model(self):
        """Load the trained XGBoost model"""
        try:
            if not self.model_path.exists():
                raise FileNotFoundError(f"Model file not found at {self.model_path}")
            
            with open(self.model_path, 'rb') as f:
                self._model = pickle.load(f)
            
            self._model_loaded = True
            logger.info(f"✓ XGBoost model loaded successfully from {self.model_path}")
            
            # Log model details
            if hasattr(self._model, 'n_estimators'):
                logger.info(f"   Model: XGBoost with {self._model.n_estimators} estimators")
            if hasattr(self._model, 'feature_names_in_'):
                logger.info(f"   Expected features: {len(self._model.feature_names_in_)}")
                
        except Exception as e:
            logger.error(f"✗ Error loading model: {e}")
            raise
    
    def predict(self, features: np.ndarray) -> float:
        """
        Make prediction using the loaded model
        
        Args:
            features: numpy array of shape (1, n_features)
            
        Returns:
            predicted_damage_pct: Predicted final total damage percentage (0-100)
        """
        if not self._model_loaded or self._model is None:
            raise RuntimeError("Model not loaded. Cannot make predictions.")
        
        try:
            # Ensure features are in correct shape
            if len(features.shape) == 1:
                features = features.reshape(1, -1)
            
            # Make prediction
            prediction = self._model.predict(features)[0]
            
            # Clip prediction to valid range [0, 100]%
            prediction = np.clip(prediction, 0.0, 100.0)
            
            logger.info(f"✓ Model prediction: {prediction:.2f}% damage")
            
            return float(prediction)
            
        except Exception as e:
            logger.error(f"✗ Error during prediction: {e}")
            raise
    
    def validate_feature_shape(self, features: np.ndarray) -> bool:
        """
        Validate that features match the model's expected input shape
        
        Args:
            features: numpy array of features
            
        Returns:
            True if features match expected shape
        """
        if not self._model_loaded:
            return False
        
        expected_features = len(self._model.feature_names_in_)
        actual_features = features.shape[1] if len(features.shape) > 1 else features.shape[0]
        
        return expected_features == actual_features
    
    def get_expected_feature_count(self) -> Optional[int]:
        """Get the number of features expected by the model"""
        if self._model_loaded and hasattr(self._model, 'feature_names_in_'):
            return len(self._model.feature_names_in_)
        return None
    
    def get_feature_names(self) -> Optional[list]:
        """Get the feature names the model was trained on"""
        if self._model_loaded and hasattr(self._model, 'feature_names_in_'):
            return list(self._model.feature_names_in_)
        return None

# Model instance
_predictor_instance = None

def get_predictor(model_path: str = None) -> ModelPredictor:
    """
    Get the global model predictor instance (singleton)
    
    Args:
        model_path: Path to the trained model file (optional)
        
    Returns:
        ModelPredictor instance
    """
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = ModelPredictor(model_path)
    return _predictor_instance

def predict_damage(features: np.ndarray, 
                  model_path: str = None) -> float:
    """
    Helper function for making predictions
    
    Args:
        features: numpy array of processed features
        model_path: Optional path to model file 
        
    Returns:
        Predicted damage percentage
    """
    predictor = get_predictor(model_path)
    return predictor.predict(features)

def validate_model_features(features: np.ndarray) -> bool:
    """
    Validate that features match model's expected shape
    
    Args:
        features: numpy array of features
        
    Returns:
        True if features are valid
    """
    predictor = get_predictor()
    return predictor.validate_feature_shape(features)


# unit tests

if __name__ == "__main__" and False:
    pass
#     print("=" * 70)
#     print("Testing model functionality using preprocessing.py as well")
#     print("=" * 70)
    
#     try:
#         # Initialize predictor
#         print("1. Loading model...")
#         predictor = get_predictor()
        
#         # Test with actual preprocessing.py results
#         print("2. Testing with preprocessing pipeline...")
        
#         try:
#             # Import preprocessing module
#             from preprocess import prepare_prediction_features
            
#             # Get database session to find active sessions
#             from database import get_db, get_active_sessions
            
#             db = get_db()
#             active_sessions = get_active_sessions(db)
            
#             if active_sessions:
#                 # Use the first active session for testing
#                 session_id = active_sessions[0].session_id
#                 print(f"   Using active session: {session_id}")
                
#                 # Get real features from preprocessing.py
#                 print("   Calling preprocessing.py...")
#                 features, raw_features = prepare_prediction_features(session_id)
                
#                 print("    Features successfully processed by preprocessing.py")
                
#                 # Show what preprocessing.py returned
#                 print(f"\n    Raw Features from preprocessing:")
#                 for key, value in raw_features.items():
#                     if key not in ['user_id', 'session_id']:
#                         print(f"      {key}: {value}")
                
#                 print(f"\n    Processed Feature Array Shape: {features.shape}")
                
#                 # Validate feature shape
#                 is_valid = predictor.validate_feature_shape(features)
#                 print(f"\n   Feature validation: {' Valid' if is_valid else ' Invalid'}")
                
#                 if is_valid:
#                     # Make prediction
#                     print("   Making prediction...")
#                     predicted_damage = predictor.predict(features)
                    
#                     print(f"\n    PREDICTION RESULT:")
#                     print(f"      Predicted Damage: {predicted_damage:.2f}%")
#                     print(f"      Location: {raw_features['location']}")
#                     print(f"      Temperature: {raw_features['tmax_c']}°C")
#                     print(f"      Humidity: {raw_features['hrmin_pct']}%")
#                     print(f"      Storage Days: {raw_features['storage_time_days']}")
#                     print(f"      Variety: {raw_features['variety']}")
#                     print(f"      Storage Technology: {raw_features['storage_technology']}")
                    
#                     print("\n   PREPROCESSING + MODEL PIPELINE WORKING!")
                    
#                 else:
#                     print("  Feature shape mismatch!")
#                     expected = predictor.get_expected_feature_count()
#                     actual = features.shape[1] if len(features.shape) > 1 else features.shape[0]
#                     print(f"      Expected: {expected}, Got: {actual}")
                    
#                     # Show feature names for debugging
#                     feature_names = predictor.get_feature_names()
#                     if feature_names:
#                         print(f"\n      Expected feature names:")
#                         for i, name in enumerate(feature_names):
#                             print(f"        {i:2d}: {name}")
                    
#             else:
#                 print("   No active sessions found in database")
#                 print("   Create a test session first using database.py")
#                 print("   Falling back to preprocessing test only...")
                
#                 # Test preprocessing.py directly
#                 print("\n   Testing preprocessing.py feature generation...")
#                 from preprocess import FeatureProcessor
#                 processor = FeatureProcessor()
                
#                 # Show expected feature names
#                 feature_names = processor.get_feature_names()
#                 print(f"   Preprocessing features: {len(feature_names)} total")
#                 for i, name in enumerate(feature_names[:8]):
#                     print(f"     {i:2d}: {name}")
#                 if len(feature_names) > 8:
#                     print(f"     ... and {len(feature_names) - 8} more")
                
#             db.close()
            
#         except ImportError as e:
#             print(f"    Could not import preprocessing module: {e}")
#             print("   Make sure preprocessing.py is in the same directory")
            
#         except Exception as e:
#             print(f"    Error in preprocessing pipeline: {e}")
#             import traceback
#             traceback.print_exc()
        
#         # Show model info
#         print("\n3. Model information:")
#         expected_features = predictor.get_expected_feature_count()
#         print(f"   Expected features: {expected_features}")
        
#         feature_names = predictor.get_feature_names()
#         if feature_names:
#             print(f"   Model was trained on {len(feature_names)} features")
        
#         print(" Model Testing complete")
#         print("=" * 70)
        
#     except FileNotFoundError as e:
#         print(f"\n Model file not found: {e}")
#         print("   Please ensure your trained model is at: ./models/best_xgb_model.pkl")
#     except Exception as e:
#         print(f"\n Error during testing: {e}")
#         import traceback
#         traceback.print_exc()



# print("\n4. Testing full pipeline with recommendations")
# try:
#     # Use the original prediction from the real session
#     sample_prediction = 0.00 
    
#     print("   Connecting to recommendations.py...")
#     from recommendations import get_recommendation
    
#     # Generate recommendation with real data
#     recommendation = get_recommendation(
#         predicted_damage_pct=sample_prediction,
#         tmax_c=raw_features['tmax_c'],
#         hrmin_pct=raw_features['hrmin_pct'],
#         storage_time_days=raw_features['storage_time_days'],
#         grain_impurities_pct=raw_features['grain_impurities_pct'],
#         initial_total_damage_pct=raw_features['initial_total_damage_pct'],
#         location=raw_features['location'],
#         variety=raw_features['variety'],
#         storage_technology=raw_features['storage_technology']
#     )
    
#     print(f"  Risk Level: {recommendation['risk_level']}")
#     print(f"  Primary Risk: {recommendation['primary_risk_factor']}")
#     print(f"  Recommendation: {recommendation['recommendation_text']}")
#     print(f"\n  Full Notification:")
#     print(f"   {recommendation['notification_message'].replace(chr(10), chr(10) + '   ')}")
    
#     print("\n  FULL PIPELINE TEST SUCCESSFUL!")
    
#     # Also test with the worse conditions prediction
#     print("\n5. Testing recommendations with worse scenario...")
#     worse_recommendation = get_recommendation(
#         predicted_damage_pct=2.53,
#         tmax_c=35.0,
#         hrmin_pct=raw_features['hrmin_pct'],
#         storage_time_days=120,
#         grain_impurities_pct=raw_features['grain_impurities_pct'],
#         initial_total_damage_pct=15.0,
#         location=raw_features['location'],
#         variety=raw_features['variety'],
#         storage_technology=raw_features['storage_technology']
#     )
    
#     print(f" Worse Scenario Risk: {worse_recommendation['risk_level']}")
#     print(f" Recommendation: {worse_recommendation['recommendation_text']}")
    
# except Exception as e:
#     print(f" Recommendations test failed: {e}")
#     import traceback
#     traceback.print_exc()