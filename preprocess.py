"""
Feature Processing Module for Predictive Crop Storage Management System
Handles feature engineering and preprocessing for ML predictions

Fetches data from database, retrieves weather data, applies encoders,
and prepares feature array ready for model prediction.

"""

import sys
import os
from pathlib import Path

# Add the weather folder to Python path
weather_path = Path(__file__).parent / "weather_info"
sys.path.append(str(weather_path))


import logging
import pickle
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Optional, Tuple
from pathlib import Path

# Import local modules
from weather_info.weather import WeatherDataRetriever
from database import get_db, StorageSession, User

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FeatureProcessor:
    """
    Handles all feature processing for ML model predictions
    Fetches data, applies encoders, creates feature arrays
    """
    
    def __init__(self, encoder_path: str = "./models/encoder.pkl"):
        """
        Initialize feature processor
        
        Args:
            encoder_path: Path to saved OneHotEncoder
        """
        self.encoder_path = Path(encoder_path)
        self.encoder = self._load_encoder()
        self.weather_retriever = WeatherDataRetriever()
        
        # Define expected feature order
        # These are the numerical features before encoding
        self.numerical_features = [
            'tmax_c',
            'hrmin_pct',
            'storage_time_days',
            'grain_impurities_pct',
            'initial_total_damage_pct'
        ]
        
        # Categorical features to encode
        self.categorical_features = ['storage_technology', 'variety']
        
        # Define exact categories expected by the model (from your feature list)
        self.expected_varieties = ['Hybrid', 'Native']
        self.expected_storage_techs = [
            'grainpro hermetic supergrainbag farm',
            'grainpro hermetic supergrainbag premium rz with zip',
            'hermetic metal silo',
            'plastic barrel',
            'plastic bottle',
            'polypropylene bag',
            'polypropylene bag with aluminum phosphide',
            'polypropylene bag with deodorized malathion',
            'polypropylene bag with micronized lime',
            'polypropylene bag with standard lime',
            'silage plastic bag'
        ]
        
        logger.info("FeatureProcessor initialized successfully")
    
    def _load_encoder(self):
        """Load the fitted OneHotEncoder from disk"""
        try:
            with open(self.encoder_path, 'rb') as f:
                encoder = pickle.load(f)
            logger.info(f"Encoder loaded from {self.encoder_path}")
            return encoder
        except FileNotFoundError:
            logger.error(f"Encoder file not found at {self.encoder_path}")
            raise
        except Exception as e:
            logger.error(f"Error loading encoder: {e}")
            raise

    def _standardize_categorical_values(self, raw_features: Dict) -> Dict:
        """
        Standardize categorical values to match encoder training data
        
        Args:
            raw_features: Dictionary containing raw feature values
            
        Returns:
            Dictionary with standardized categorical values
        """
        # Standardize variety
        variety_input = raw_features['variety'].strip()
        if variety_input.lower() == 'hybrid':
            variety = 'Hybrid'
        elif variety_input.lower() == 'native':
            variety = 'Native'
        else:
            logger.warning(f"Unknown variety '{variety_input}'. Defaulting to 'Hybrid'")
            variety = 'Hybrid'
        
        # Standardize storage technology
        storage_tech_input = raw_features['storage_technology'].strip().lower()
        
        # Map common inputs to exact training categories
        tech_mapping = {
            'polypropylene': 'polypropylene bag',
            'polypropylene bag': 'polypropylene bag',
            'pp bag': 'polypropylene bag',
            'hermetic': 'hermetic metal silo',
            'metal silo': 'hermetic metal silo',
            'silo': 'hermetic metal silo',
            'grainpro': 'grainpro hermetic supergrainbag farm',
            'grainpro farm': 'grainpro hermetic supergrainbag farm',
            'grainpro premium': 'grainpro hermetic supergrainbag premium rz with zip',
            'plastic barrel': 'plastic barrel',
            'plastic bottle': 'plastic bottle',
            'silage': 'silage plastic bag',
            'silage bag': 'silage plastic bag',
            'aluminum phosphide': 'polypropylene bag with aluminum phosphide',
            'malathion': 'polypropylene bag with deodorized malathion',
            'micronized lime': 'polypropylene bag with micronized lime',
            'standard lime': 'polypropylene bag with standard lime'
        }
        
        # Use mapping
        storage_tech = tech_mapping.get(storage_tech_input, storage_tech_input)
        
        # If it's not one of the exact training categories, use a fallback
        if storage_tech not in self.expected_storage_techs:
            logger.warning(f"Storage technology '{storage_tech_input}' not in exact categories. Using 'polypropylene bag' as fallback.")
            storage_tech = 'polypropylene bag'
        
        logger.info(f"Standardized categorical values - Variety: {variety}, Storage Tech: {storage_tech}")
        
        return {
            'storage_technology': storage_tech,
            'variety': variety
        }
    
    def prepare_features_for_prediction(self, 
                                       session_id: int,
                                       db_session = None) -> Tuple[np.ndarray, Dict]:
        """
        Main function: Prepare features for a storage session
        
        This function:
        1. Fetches session data from database
        2. Retrieves current weather data
        3. Calculates storage duration
        4. Applies OneHotEncoder
        5. Returns feature array ready for model.predict()
        
        Args:
            session_id: Storage session ID
            db_session: Database session
        Returns:
            Tuple of feature_array, and metadata_dict
            - feature_array: numpy array ready for model prediction
            - metadata_dict: raw feature values for logging/debugging
        """
        # Get database session
        if db_session is None:
            db = get_db()
            should_close = True
        else:
            db = db_session
            should_close = False
        
        try:
            # Fetch storage session from database
            session = db.query(StorageSession).filter(
                StorageSession.session_id == session_id
            ).first()
            
            if not session:
                raise ValueError(f"Storage session {session_id} not found")
            
            logger.info(f"Processing features for session {session_id}")
            
            # Get user for location
            user = db.query(User).filter(User.user_id == session.user_id).first()
            if not user:
                raise ValueError(f"User not found for session {session_id}")
            
            # Retrieve weather data
            weather_data = self.weather_retriever.get_weather_for_user(user)
            if not weather_data:
                raise ValueError(f"Could not retrieve weather data for {user.district}")
            
            # Calculate storage duration
            storage_time_days = session.get_storage_duration_days()
            
            # Prepare raw features
            raw_features = {
                # Weather features
                'tmax_c': weather_data['temperature'],
                'hrmin_pct': weather_data['humidity'],
                
                # Session features
                'storage_time_days': storage_time_days,
                'grain_impurities_pct': session.grain_impurities_pct,
                'initial_total_damage_pct': session.initial_total_damage_pct,
                
                # Categorical features
                'storage_technology': session.storage_technology,
                'variety': session.variety,
                
                # Metadata
                'location': user.district,
                'user_id': user.user_id,
                'session_id': session_id
            }
            
            logger.info(f"Raw features collected: {raw_features}")
            
            # Process features into model-ready array
            feature_array = self._encode_features(raw_features)
            
            return feature_array, raw_features
            
        except Exception as e:
            logger.error(f"Error preparing features: {e}")
            raise
        finally:
            if should_close:
                db.close()
    
    def _encode_features(self, raw_features: Dict) -> np.ndarray:
        """
        Encode features using OneHotEncoder and combine with numerical features
        
        Args:
            raw_features: Dictionary of raw feature values
            
        Returns:
            numpy array ready for model prediction
        """
        # Extract numerical features in correct order
        numerical_values = [
            raw_features[feat] for feat in self.numerical_features
        ]
        
        # Standardize categorical values to match training data exactly
        standardized_categorical = self._standardize_categorical_values(raw_features)
        
        # Prepare categorical features for encoding
        categorical_df = pd.DataFrame({
            'storage_technology': [standardized_categorical['storage_technology']],
            'variety': [standardized_categorical['variety']]
        })
        
        logger.info(f"Encoded categorical values: {standardized_categorical}")
        
        # Apply OneHotEncoder
        encoded_categorical = self.encoder.transform(categorical_df)
        
        # Combine numerical and encoded categorical features
        feature_array = np.concatenate([
            np.array(numerical_values).reshape(1, -1),
            encoded_categorical
        ], axis=1)
        
        logger.info(f"Feature array shape: {feature_array.shape}")
        
        return feature_array
    
    def verify_feature_names(self):
        """
        Verify that our feature names match the model's expected features
        """
        print("Verifying feature names against model expectations")
        print("=" * 50)
        
        # Get the feature names from our processor
        our_features = self.get_feature_names()
        
        print("Processor features:")
        for i, feat in enumerate(our_features):
            print(f"  {i:2d}: {feat}")
        
        print(f"\nTotal features: {len(our_features)}")
        
        # Compare with known model features from your list
        model_features_expected = [
            'tmax_c',
            'hrmin_pct', 
            'storage_time_days',
            'grain_impurities_pct',
            'initial_total_damage_pct',
            'storage_technology_grainpro hermetic supergrainbag farm',
            'storage_technology_grainpro hermetic supergrainbag premium rz with zip',
            'storage_technology_hermetic metal silo',
            'storage_technology_plastic barrel',
            'storage_technology_plastic bottle',
            'storage_technology_polypropylene bag',
            'storage_technology_polypropylene bag with aluminum phosphide',
            'storage_technology_polypropylene bag with deodorized malathion',
            'storage_technology_polypropylene bag with micronized lime',
            'storage_technology_polypropylene bag with standard lime',
            'storage_technology_silage plastic bag',
            'variety_Hybrid',
            'variety_Native'
        ]
        
        print("\nExpected model features:")
        for i, feat in enumerate(model_features_expected):
            print(f"  {i:2d}: {feat}")
        
        print(f"\nTotal expected: {len(model_features_expected)}")
        
        # Check if they match
        if len(our_features) == len(model_features_expected):
            print("\n Feature count matches!")
        else:
            print(f"\n Feature count mismatch: {len(our_features)} vs {len(model_features_expected)}")
        
        # Check for missing features
        missing = set(model_features_expected) - set(our_features)
        if missing:
            print(f"\n Missing features: {missing}")
        
        extra = set(our_features) - set(model_features_expected)
        if extra:
            print(f"\n Extra features: {extra}")
            
        return len(our_features) == len(model_features_expected) and not missing and not extra
    
    def validate_features(self, raw_features: Dict) -> bool:
        """
        Validate feature values are within reasonable ranges
        
        Args:
            raw_features: Dictionary of raw feature values
            
        Returns:
            True if all features are valid
        """
        # Temperature
        if not (10 <= raw_features['tmax_c'] <= 40):
            logger.warning(f"Temperature {raw_features['tmax_c']}°C outside expected range")
            return False
        
        # Humidity: 0-100%
        if not (0 <= raw_features['hrmin_pct'] <= 100):
            logger.warning(f"Humidity {raw_features['hrmin_pct']}% outside valid range")
            return False
        
        # Storage time
        if raw_features['storage_time_days'] < 0:
            logger.warning(f"Storage time cannot be negative")
            return False
        
        # Impurities
        if not (0 <= raw_features['grain_impurities_pct'] <= 100):
            logger.warning(f"Impurities {raw_features['grain_impurities_pct']}% outside valid range")
            return False
        
        # Initial damage
        if not (0 <= raw_features['initial_total_damage_pct'] <= 100):
            logger.warning(f"Initial damage {raw_features['initial_total_damage_pct']}% outside valid range")
            return False
        
        return True
    
    def get_feature_names(self) -> list:
        """
        Get all feature names in the correct order
        Useful for debugging and SHAP analysis
        
        Returns:
            List of feature names matching the feature array
        """
        # Numerical features
        features = self.numerical_features.copy()
        
        # Add encoded categorical feature names
        encoded_names = self.encoder.get_feature_names_out(self.categorical_features)
        features.extend(encoded_names)
        
        return features

# Helper function forapi integration

def prepare_prediction_features(session_id: int) -> Tuple[np.ndarray, Dict]:
    """
    Convenience function for API endpoints
    Prepares features for a single session
    
    Args:
        session_id: Storage session ID
        
    Returns:
        Tuple of (feature_array, raw_features)
    """
    processor = FeatureProcessor()
    return processor.prepare_features_for_prediction(session_id)


def validate_session_features(session_id: int) -> bool:
    """
    Validate that a session has valid feature values
    
    Args:
        session_id: Storage session ID
        
    Returns:
        True if features are valid
    """
    processor = FeatureProcessor()
    _, raw_features = processor.prepare_features_for_prediction(session_id)
    return processor.validate_features(raw_features)

# Unit tests

if __name__ == "__main__":
    print("=" * 70)
    print("TESTING FEATURE PROCESSOR")
    print("=" * 70)
    
    try:
        # Test with database
        from database import get_db, get_active_sessions
        
        db = get_db()
        active_sessions = get_active_sessions(db)
        
        if not active_sessions:
            print("\n  No active sessions found in database")
            print("Create a test session first using database.py")
        else:
            session = active_sessions[0]
            print(f"\n Testing with session {session.session_id}")
            
            # Initialize processor
            processor = FeatureProcessor()
            
            # First, verify feature names match
            print("\n Verifying feature name matching...")
            feature_match_success = processor.verify_feature_names()
            
            if not feature_match_success:
                print("\n WARNING: Feature names don't match model expectations!")
                print("   Predictions may be inaccurate!")
            else:
                print("\n Feature names match model expectations!")
            
            # Prepare features
            feature_array, raw_features = processor.prepare_features_for_prediction(
                session.session_id,
                db_session=db
            )
            
            print("\n Raw Features:")
            for key, value in raw_features.items():
                if key not in ['user_id', 'session_id']:
                    print(f"  {key}: {value}")
            
            print(f"\n Feature Array Shape: {feature_array.shape}")
            print(f" Feature Processing Successful!")
            
            # Validate features
            is_valid = processor.validate_features(raw_features)
            print(f"\n✓ Features Valid: {is_valid}")
            
            # Show feature names
            feature_names = processor.get_feature_names()
            print(f"\n Total Features: {len(feature_names)}")
            print(f"   Numerical: {len(processor.numerical_features)}")
            print(f"   Encoded: {len(feature_names) - len(processor.numerical_features)}")
            
            # Show first few actual feature values
            print(f"\n First 10 feature values:")
            for i in range(min(10, len(feature_names))):
                print(f"  {feature_names[i]}: {feature_array[0][i]:.4f}")
        
        db.close()
        print("\n" + "=" * 70)
        print(" FEATURE PROCESSOR TEST COMPLETE")
        print("=" * 70)
        
    except ImportError:
        print("\n  Database module not available")
        print("Run this test after setting up database.py")
    except Exception as e:
        print(f"\n Error during testing: {e}")
        import traceback
        traceback.print_exc()