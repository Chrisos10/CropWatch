"""
Integrated Scheduler Module for FastAPI
This module runs FastAPI application as a background task
"""

import logging
from datetime import datetime
from typing import List
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# Import your modules
from database import (
    get_db,
    get_active_sessions,
    create_daily_prediction,
    create_notification,
    StorageSession
)
from preprocess import FeatureProcessor
from model import get_predictor
from recommendations import get_recommendation

# Configure logging
logger = logging.getLogger(__name__)


class IntegratedPredictionScheduler:
    """
    Integrated scheduler that runs inside FastAPI
    Uses AsyncIOScheduler which is compatible with FastAPI's async event loop
    """
    
    def __init__(self):
        """Initialize scheduler components"""
        self.scheduler = AsyncIOScheduler(timezone='Africa/Kigali')
        self.processor = None
        self.predictor = None
        self.is_running = False
        logger.info(" Integrated scheduler initialized")
    
    def start(self, daily_check_hour: int = 8, daily_check_minute: int = 0):
        """
        Start the scheduler
        Called during FastAPI startup
        
        Args:
            daily_check_hour: Hour to run daily predictions (0-23, default 8)
            daily_check_minute: Minute to run daily predictions (0-59, default 0)
        """
        if self.is_running:
            logger.warning(" Scheduler already running")
            return
        
        # Initialize ML components (lazy loading)
        if not self.processor:
            self.processor = FeatureProcessor()
            logger.info(" Feature processor loaded")
        
        if not self.predictor:
            self.predictor = get_predictor()
            logger.info(" ML model loaded")
        
        # Schedule daily predictions
        self.scheduler.add_job(
            self.run_daily_predictions,
            trigger=CronTrigger(
                hour=daily_check_hour,
                minute=daily_check_minute,
                timezone='Africa/Kigali'
            ),
            id='daily_predictions',
            name='Daily Crop Storage Predictions',
            replace_existing=True,
            max_instances=1
        )
        
        self.scheduler.start()
        self.is_running = True
        
        # Log next run time
        next_run = self.scheduler.get_job('daily_predictions').next_run_time
        logger.info("=" * 70)
        logger.info("SCHEDULER STARTED")
        logger.info(f" Scheduled time: {daily_check_hour:02d}:{daily_check_minute:02d} Rwanda time")
        logger.info(f" Next run: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 70)
    
    def shutdown(self):
        """Shutdown the scheduler gracefully"""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info(" Scheduler stopped")
    
    def run_daily_predictions(self):
        """
        Main job: Run predictions for all active sessions
        This is called automatically by the scheduler
        """
        start_time = datetime.now()
        logger.info("=" * 70)
        logger.info(" STARTING DAILY PREDICTION RUN")
        logger.info(f"   Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 70)
        
        db = get_db()
        
        try:
            # Get all active storage sessions
            active_sessions = get_active_sessions(db)
            
            if not active_sessions:
                logger.info("  No active storage sessions found")
                return
            
            logger.info(f" Found {len(active_sessions)} active session(s)")
            
            success_count = 0
            error_count = 0
            
            # Process each session
            for session in active_sessions:
                try:
                    self._process_single_session(session, db)
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    logger.error(f"Error processing session {session.session_id}: {e}")
                    continue
            
            # Summary
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info("=" * 70)
            logger.info(" DAILY PREDICTION RUN COMPLETE")
            logger.info(f"   Duration: {duration:.2f} seconds")
            logger.info(f"   Successful: {success_count}")
            logger.info(f"   Errors: {error_count}")
            logger.info("=" * 70)
            
        except Exception as e:
            logger.error(f" CRITICAL ERROR in daily prediction run: {e}")
        finally:
            db.close()
    
    def _process_single_session(self, session: StorageSession, db):
        """
        Process a single storage session: predict + recommend + save
        
        Args:
            session: StorageSession object from database
            db: Database session
        """
        logger.info(f"\n Processing session {session.session_id}")
        logger.info(f"   User: {session.user.username}")
        logger.info(f"   District: {session.user.district}")
        
        # Step 1: Prepare features
        feature_array, raw_features = self.processor.prepare_features_for_prediction(
            session_id=session.session_id,
            db_session=db
        )
        
        logger.info(f" Weather: {raw_features['tmax_c']}°C, {raw_features['hrmin_pct']}% humidity")
        logger.info(f" Storage days: {raw_features['storage_time_days']}")
        
        # Step 2: Make prediction
        predicted_damage = self.predictor.predict(feature_array)
        logger.info(f" Predicted damage: {predicted_damage:.2f}%")
        
        # Step 3: Generate recommendation
        recommendation = get_recommendation(
            predicted_damage_pct=predicted_damage,
            tmax_c=raw_features['tmax_c'],
            hrmin_pct=raw_features['hrmin_pct'],
            storage_time_days=raw_features['storage_time_days'],
            grain_impurities_pct=raw_features['grain_impurities_pct'],
            initial_total_damage_pct=raw_features['initial_total_damage_pct'],
            location=raw_features['location'],
            variety=raw_features['variety'],
            storage_technology=raw_features['storage_technology']
        )
        
        logger.info(f" Risk level: {recommendation['risk_level']}")
        
        # Step 4: Save prediction to database
        prediction = create_daily_prediction(
            db=db,
            session_id=session.session_id,
            storage_time_days=raw_features['storage_time_days'],
            tmax_c=raw_features['tmax_c'],
            hrmin_pct=raw_features['hrmin_pct'],
            predicted_total_damage_pct=predicted_damage,
            risk_level=recommendation['risk_level'],
            recommendation_text=recommendation['recommendation_text']
        )
        
        # Step 5: Create notification
        notification = create_notification(
            db=db,
            user_id=session.user_id,
            prediction_id=prediction.prediction_id,
            message_content=recommendation['notification_message']
        )
        
        logger.info(f" Notification created (ID: {notification.notification_id})")
    
    def trigger_manual_run(self):
        """
        Manually trigger predictions (for testing or admin endpoint)
        Returns summary of the run
        """
        logger.info(" Manual prediction run triggered")
        
        db = get_db()
        try:
            active_sessions = get_active_sessions(db)
            
            if not active_sessions:
                return {
                    "status": "no_sessions",
                    "message": "No active storage sessions found",
                    "processed": 0
                }
            
            success_count = 0
            error_count = 0
            errors = []
            
            for session in active_sessions:
                try:
                    self._process_single_session(session, db)
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    errors.append({
                        "session_id": session.session_id,
                        "error": str(e)
                    })
            
            return {
                "status": "success",
                "total_sessions": len(active_sessions),
                "successful": success_count,
                "errors": error_count,
                "error_details": errors if errors else None
            }
            
        except Exception as e:
            logger.error(f" Manual run failed: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
        finally:
            db.close()


# Global scheduler instance
_scheduler_instance = None

def get_scheduler() -> IntegratedPredictionScheduler:
    """Get the global scheduler instance"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = IntegratedPredictionScheduler()
    return _scheduler_instance