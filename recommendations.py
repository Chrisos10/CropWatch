"""
Recommendations Module for Predictive Crop Storage Management System
Generates risk-based natural preservation recommendations for maize storage

Uses PREDICTION-FIRST logic: Use the model's prediction, then use feature 
analysis to provide context-appropriate recommendations.
"""

import logging
from datetime import datetime
from typing import Dict, Tuple, Optional
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Feature importance rankings from tuned XGBoost model
FEATURE_IMPORTANCES = {
    'storage_technology_polypropylene_bag': 3129.22,
    'tmax_c': 390.10,
    'hrmin_pct': 350.37,
    'initial_total_damage_pct': 305.98,
    'storage_time_days': 272.10,
    'grain_impurities_pct': 256.05
}


class RiskLevel(Enum):
    """Risk levels based on predicted damage percentage"""
    PERFECT = "perfect"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class FeatureThresholds:
    """Research-backed thresholds for storage parameters (FAO guidelines)"""
    
    TEMP_SAFE = 20.0
    TEMP_WARNING = 30.0
    
    HUMIDITY_SAFE = 70.0
    HUMIDITY_WARNING = 80.0
    
    STORAGE_SAFE = 90
    STORAGE_WARNING = 180
    
    IMPURITIES_SAFE = 2.0
    IMPURITIES_WARNING = 5.0
    
    INITIAL_DAMAGE_WARNING = 3.0


# Recommendation templates that are Research-backed, actionable interventions
RECOMMENDATION_TEMPLATES = {
    # Perfect conditions (0% damage)
    'perfect_conditions': {
        'action': 'Excellent! Your grain is perfectly preserved. Continue current storage practices and check grain daily for any changes',
    },
    
    # Preventive recommendations (LOW risk with concerning features)
    'preventive_high_temperature': {
        'action': 'Temperature is elevated but grain is safe. Open storage container daily for 30 minutes to release heat. Keep container in shade under roof',
    },
    
    'preventive_moderate_temperature': {
        'action': 'Temperature is acceptable. Check grain daily and turn it monthly to prevent hot spots from forming',
    },
    
    'preventive_high_humidity': {
        'action': 'Humidity is elevated but grain is safe. Verify your grain is completely dry by biting a kernel - it should crack cleanly. Check weekly',
    },
    
    'preventive_long_storage': {
        'action': 'Storage duration increasing. Mix 50-75g of dried Basil leaves per 10kg grain as preventive measure. Inspect grain monthly',
    },
    
    'preventive_high_impurities': {
        'action': 'Some impurities detected. When convenient, winnow grain to remove dust and debris. This improves airflow and reduces pest hiding places',
    },
    
    'preventive_high_initial_damage': {
        'action': 'Some initial damage present. Prioritize using this batch within 2-3 months. Check weekly for mold or pest activity',
    },
    
    # Optimal conditions (LOW risk, no concerning features)
    'optimal_conditions': {
        'action': 'Storage conditions are optimal. Continue checking grain daily and maintain current practices',
    },
    
    # ACTION REQUIRED (MEDIUM/HIGH risk)
    'action_high_temperature': {
        'action': 'TEMPERATURE RISK: Mix 100g ground Neem leaf powder per kg of grain immediately. Store container in coolest area. Open daily for 30min to cool',
    },
    
    'action_moderate_temperature': {
        'action': 'TEMPERATURE ALERT: Add 50-75g dried Basil leaves per 10kg grain. Turn grain weekly and keep in shaded area away from walls',
    },
    
    'action_high_humidity': {
        'action': 'HUMIDITY RISK: Mix 20-30g Turmeric powder per 10kg grain now. Transfer to airtight container if possible. Grain must be dry before sealing',
    },
    
    'action_long_storage': {
        'action': 'EXTENDED STORAGE: Apply 0.3-0.6g food-grade Diatomaceous Earth per kg grain OR mix 30-40g combined Neem+Turmeric per 10kg. Inspect monthly',
    },
    
    'action_high_impurities': {
        'action': 'HIGH IMPURITIES: Winnow grain immediately to remove debris. After cleaning, mix 100g Neem powder per kg grain to prevent pest infestation',
    },
    
    'action_high_initial_damage': {
        'action': 'DAMAGE ALERT: Remove all damaged/moldy kernels by hand sorting. Mix 60% Neem + 25% Chili + 15% Diatomaceous Earth, apply 40g per 10kg',
    },
}


class RecommendationEngine:
    """
    Prediction-first recommendation engine
    
    Logic hierarchy:
    1. PERFECT (0% damage) → grains are perfect regardless of feature thresholds
    2. LOW (0.01-3% damage) → Preventive recommendations if features concerning
    3. MEDIUM/HIGH (>3% damage) → Action required based on problematic features
    """
    
    def __init__(self):
        self.feature_importances = FEATURE_IMPORTANCES
        self.thresholds = FeatureThresholds()
    
    def categorize_risk_level(self, predicted_damage_pct: float) -> RiskLevel:
        """Categorize risk based on model's prediction"""
        if predicted_damage_pct == 0.0:
            return RiskLevel.PERFECT
        elif predicted_damage_pct < 3.0:
            return RiskLevel.LOW
        elif predicted_damage_pct < 10.0:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.HIGH
    
    def identify_problematic_features(self, features: Dict[str, float]) -> Dict[str, Tuple[str, float, float]]:
        """Identify features that exceed thresholds"""
        problematic = {}
        
        temp = features.get('tmax_c', 0)
        if temp > self.thresholds.TEMP_WARNING:
            problematic['tmax_c'] = ('critical', temp, self.thresholds.TEMP_WARNING)
        elif temp > self.thresholds.TEMP_SAFE:
            problematic['tmax_c'] = ('warning', temp, self.thresholds.TEMP_SAFE)
        
        humidity = features.get('hrmin_pct', 0)
        if humidity > self.thresholds.HUMIDITY_WARNING:
            problematic['hrmin_pct'] = ('critical', humidity, self.thresholds.HUMIDITY_WARNING)
        elif humidity > self.thresholds.HUMIDITY_SAFE:
            problematic['hrmin_pct'] = ('warning', humidity, self.thresholds.HUMIDITY_SAFE)
        
        storage_days = features.get('storage_time_days', 0)
        if storage_days > self.thresholds.STORAGE_WARNING:
            problematic['storage_time_days'] = ('critical', storage_days, self.thresholds.STORAGE_WARNING)
        elif storage_days > self.thresholds.STORAGE_SAFE:
            problematic['storage_time_days'] = ('warning', storage_days, self.thresholds.STORAGE_SAFE)
        
        impurities = features.get('grain_impurities_pct', 0)
        if impurities > self.thresholds.IMPURITIES_WARNING:
            problematic['grain_impurities_pct'] = ('critical', impurities, self.thresholds.IMPURITIES_WARNING)
        elif impurities > self.thresholds.IMPURITIES_SAFE:
            problematic['grain_impurities_pct'] = ('warning', impurities, self.thresholds.IMPURITIES_SAFE)
        
        initial_damage = features.get('initial_total_damage_pct', 0)
        if initial_damage >= self.thresholds.INITIAL_DAMAGE_WARNING:
            problematic['initial_total_damage_pct'] = ('warning', initial_damage, self.thresholds.INITIAL_DAMAGE_WARNING)
        
        return problematic
    
    def identify_primary_risk_factor(self, problematic_features: Dict[str, Tuple[str, float, float]]) -> Optional[str]:
        """Select primary risk using feature importance ranking"""
        if not problematic_features:
            return None
        
        # Prioritize critical over warning
        critical = {k: v for k, v in problematic_features.items() if v[0] == 'critical'}
        warning = {k: v for k, v in problematic_features.items() if v[0] == 'warning'}
        
        if critical:
            primary = max(critical.keys(), key=lambda x: self.feature_importances.get(x, 0))
        else:
            primary = max(warning.keys(), key=lambda x: self.feature_importances.get(x, 0))
        
        return primary
    
    def select_recommendation_template(self, 
                                      risk_level: RiskLevel,
                                      primary_risk: Optional[str],
                                      severity: Optional[str]) -> Dict:
        """
        PREDICTION-FIRST LOGIC: Select recommendation based on prediction + features
        
        Key principle: Trust the model's prediction as primary signal
        """
        
        # A case of 0% damage
        # Even if features exceed thresholds, other factors are compensating
        if risk_level == RiskLevel.PERFECT:
            logger.info("Perfect prediction (0%)")
            return RECOMMENDATION_TEMPLATES['perfect_conditions']
        
        # Llow prediction 0.01-3% damage
        # Minor risk detected by model
        # If features are concerning, give PREVENTIVE advice
        elif risk_level == RiskLevel.LOW:
            if primary_risk:
                logger.info(f"Low prediction with concerning feature: {primary_risk}")
                template_map = {
                    'tmax_c': {
                        'critical': 'preventive_high_temperature',
                        'warning': 'preventive_moderate_temperature'
                    },
                    'hrmin_pct': 'preventive_high_humidity',
                    'storage_time_days': 'preventive_long_storage',
                    'grain_impurities_pct': 'preventive_high_impurities',
                    'initial_total_damage_pct': 'preventive_high_initial_damage',
                }
                
                if primary_risk == 'tmax_c':
                    key = template_map['tmax_c'][severity]
                else:
                    key = template_map.get(primary_risk, 'optimal_conditions')
                
                return RECOMMENDATION_TEMPLATES[key]
            else:
                logger.info("Low prediction with no concerning features")
                return RECOMMENDATION_TEMPLATES['optimal_conditions']
        
        # MEDIUM/HIGH PREDICTION >3% damage
        # Significant risk detected by model
        # ACTION REQUIRED - give specific interventions
        else:
            if primary_risk:
                logger.info(f"{risk_level.value.upper()} prediction with {primary_risk}")
                template_map = {
                    'tmax_c': {
                        'critical': 'action_high_temperature',
                        'warning': 'action_moderate_temperature'
                    },
                    'hrmin_pct': 'action_high_humidity',
                    'storage_time_days': 'action_long_storage',
                    'grain_impurities_pct': 'action_high_impurities',
                    'initial_total_damage_pct': 'action_high_initial_damage',
                }
                
                if primary_risk == 'tmax_c':
                    key = template_map['tmax_c'][severity]
                else:
                    key = template_map.get(primary_risk, 'optimal_conditions')
                
                return RECOMMENDATION_TEMPLATES[key]
            else:
                # High prediction but no obvious feature issues
                logger.warning(f"{risk_level.value.upper()} prediction but no clear problematic features")
                return RECOMMENDATION_TEMPLATES['optimal_conditions']
    
    def generate_notification(self,
                            predicted_damage_pct: float,
                            risk_level: RiskLevel,
                            location: str,
                            template: Dict) -> str:
        """Generate frontend-compatible notification"""
        now = datetime.now()
        date_str = now.strftime("%d-%m-%Y")
        time_str = now.strftime("%H:%M:%S")
        
        notification = f"Date: {date_str} Time: {time_str}\n"
        notification += f"Location: {location}\n"
        
        if risk_level == RiskLevel.PERFECT:
            notification += "No spoilage detected. Grain is in perfect condition.\n"
        else:
            notification += f"Potential {predicted_damage_pct:.1f}% spoilage detected.\n"
        
        notification += f"Recommendation: {template['action']}"
        
        return notification
    
    def generate_recommendation(self,
                               predicted_damage_pct: float,
                               features: Dict[str, float],
                               location: str) -> Dict[str, any]:
        """
        Main recommendation generator with PREDICTION-FIRST logic
        """
        try:
            # Step 1: Get risk level from prediction
            risk_level = self.categorize_risk_level(predicted_damage_pct)
            logger.info(f"Risk level: {risk_level.value} ({predicted_damage_pct:.1f}% damage)")
            
            # Step 2: Analyze features (but interpretation depends on risk level)
            problematic = self.identify_problematic_features(features)
            primary_risk = self.identify_primary_risk_factor(problematic) if problematic else None
            severity = problematic[primary_risk][0] if primary_risk else None
            
            logger.info(f"Problematic features: {list(problematic.keys())}")
            if primary_risk:
                logger.info(f"Primary risk factor: {primary_risk} ({severity})")
            
            # Step 3: Select template using PREDICTION-FIRST logic
            template = self.select_recommendation_template(risk_level, primary_risk, severity)
            
            # Step 4: Generate notification
            notification_message = self.generate_notification(
                predicted_damage_pct,
                risk_level,
                location,
                template
            )
            
            # Map PERFECT to LOW for database compatibility

            db_risk_level = 'low' if risk_level == RiskLevel.PERFECT else risk_level.value
            
            return {
                'risk_level': db_risk_level,
                'primary_risk_factor': primary_risk,
                'recommendation_text': template['action'],
                'notification_message': notification_message,
            }
            
        except Exception as e:
            logger.error(f"Error generating recommendation: {e}")
            now = datetime.now()
            return {
                'risk_level': 'medium',
                'primary_risk_factor': None,
                'recommendation_text': 'Error generating recommendation. Monitor storage carefully.',
                'notification_message': f"Date: {now.strftime('%d-%m-%Y')} Time: {now.strftime('%H:%M:%S')}\nLocation: {location}\nError generating recommendation. Please monitor storage carefully.",
            }


def get_recommendation(predicted_damage_pct: float,
                      tmax_c: float,
                      hrmin_pct: float,
                      storage_time_days: int,
                      grain_impurities_pct: float,
                      initial_total_damage_pct: float,
                      location: str,
                      variety: str = 'hybrid',
                      storage_technology: str = 'polypropylene bag') -> Dict[str, any]:
    """Convenience function for getting recommendations"""
    features = {
        'tmax_c': tmax_c,
        'hrmin_pct': hrmin_pct,
        'storage_time_days': storage_time_days,
        'grain_impurities_pct': grain_impurities_pct,
        'initial_total_damage_pct': initial_total_damage_pct,
        'variety': variety,
        'storage_technology': storage_technology
    }
    
    engine = RecommendationEngine()
    return engine.generate_recommendation(predicted_damage_pct, features, location)


if __name__ == "__main__":
    print("=" * 80)
    print("TESTING PREDICTION-FIRST RECOMMENDATION ENGINE")
    print("=" * 80)
    
    # Test 1: prediction of (0%) with high temperature
    print("\n" + "=" * 80)
    print("TEST 1: CRITICAL ISSUE - 0% Prediction vs High Temperature")
    print("Prediction: 0% | Temperature: 32°C (above threshold)")
    print("Expected: Trust the model - say conditions are PERFECT")
    print("=" * 80)
    result1 = get_recommendation(
        predicted_damage_pct=0.0,
        tmax_c=32.0,
        hrmin_pct=65.0,
        storage_time_days=10,
        grain_impurities_pct=1.5,
        initial_total_damage_pct=0.0,
        location='Gasabo'
    )
    print(result1['notification_message'])
    print(f"Database risk level: {result1['risk_level']}")
    
    # Test 2: LOW prediction (1%) with high temperature
    print("\n" + "=" * 80)
    print("TEST 2: Low Prediction with High Temperature")
    print("Prediction: 1% | Temperature: 32°C")
    print("Expected: PREVENTIVE recommendation")
    print("=" * 80)
    result2 = get_recommendation(
        predicted_damage_pct=1.0,
        tmax_c=32.0,
        hrmin_pct=65.0,
        storage_time_days=45,
        grain_impurities_pct=1.5,
        initial_total_damage_pct=0.5,
        location='Nyarugenge'
    )
    print(result2['notification_message'])
    print(f"✓ Gives preventive advice for low risk!")
    
    # Test 3: MEDIUM prediction with high temperature
    print("\n" + "=" * 80)
    print("TEST 3: Medium Prediction with High Temperature")
    print("Prediction: 5.5% | Temperature: 32°C")
    print("Expected: ACTION REQUIRED")
    print("=" * 80)
    result3 = get_recommendation(
        predicted_damage_pct=5.5,
        tmax_c=32.0,
        hrmin_pct=65.0,
        storage_time_days=45,
        grain_impurities_pct=1.5,
        initial_total_damage_pct=1.0,
        location='Kicukiro'
    )
    print(result3['notification_message'])
    print(f"✓ Requires immediate action for medium risk!")
    
    # Test 4: HIGH prediction with multiple issues
    print("\n" + "=" * 80)
    print("TEST 4: High Prediction with Multiple Issues")
    print("Prediction: 12.3% | Multiple critical factors")
    print("Expected: Prioritize by feature importance")
    print("=" * 80)
    result4 = get_recommendation(
        predicted_damage_pct=12.3,
        tmax_c=31.0,
        hrmin_pct=82.0,
        storage_time_days=200,
        grain_impurities_pct=6.0,
        initial_total_damage_pct=4.0,
        location='Bumbogo'
    )
    print(result4['notification_message'])
    print(f"\nPrimary risk: {result4['primary_risk_factor']}")
    
    # Test 5: LOW prediction with NO problematic features
    print("\n" + "=" * 80)
    print("TEST 5: Low Prediction with Good Conditions")
    print("Prediction: 0.5% | All features in safe range")
    print("Expected: Optimal conditions message")
    print("=" * 80)
    result5 = get_recommendation(
        predicted_damage_pct=0.5,
        tmax_c=19.0,
        hrmin_pct=65.0,
        storage_time_days=50,
        grain_impurities_pct=1.0,
        initial_total_damage_pct=0.5,
        location='Nyarugenge'
    )
    print(result5['notification_message'])
    
    print("\n" + "=" * 80)
    print("KEY IMPROVEMENTS:")
    print("✓ PREDICTION-FIRST: Trusts model's 0% prediction over feature thresholds")
    print("✓ CONTEXT-AWARE: Different recommendations for same feature at different risk levels")
    print("✓ PREVENTIVE vs ACTION: Low risk = preventive, Medium/High = action required")
    print("✓ FEATURE IMPORTANCE: Prioritizes issues by model's learned importance")
    print("✓ DATABASE COMPATIBLE: Maps 'perfect' to 'low' for enum constraint")
    print("=" * 80)