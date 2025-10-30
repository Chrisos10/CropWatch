"""
FastAPI Application for Predictive Crop Storage Management System
Handles authentication, sessions, predictions, and notifications
WITH INTEGRATED SCHEDULER
"""
import sys
import os
from pathlib import Path
from dotenv import load_dotenv  # ← Move here with other standard library imports
import warnings

load_dotenv() 

warnings.filterwarnings("ignore", category=DeprecationWarning)
# parent directory to Python path to import modules
sys.path.append(str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime, timedelta
import jwt
import logging
import numpy as np
import sys
from pathlib import Path
from automation import get_scheduler
from sqlalchemy import text


# Import local modules
from database import (
    get_db, init_db,
    User, StorageSession, DailyPrediction, Notification,
    get_user_by_username, get_user_by_email, get_user_by_id,
    get_user_active_session, get_user_notifications,
    create_storage_session, end_user_active_session,
)
from preprocess import FeatureProcessor
from model import get_predictor
from recommendations import get_recommendation

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Crop Storage Management API",
    description="API for predictive crop storage management",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()
# Get SECRET_KEY from environment variable
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is not set!")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Start up and shutdown events with scheduler/automation integration

@app.on_event("startup")
async def startup_event():
    logger.info(" Starting Crop Storage Management API...")
    init_db()
    logger.info(" Database initialized")
    
   
    scheduler = get_scheduler()
    scheduler.start(daily_check_hour=15, daily_check_minute=0)  # 3:00 PM daily
    logger.info("Scheduler started - Daily predictions at 3:00 PM")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Crop Storage Management API...")
    scheduler = get_scheduler()
    scheduler.shutdown()
    logger.info(" Scheduler stopped")

# PYDANTIC MODELS (Request/Response Schemas)

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    telephone: str
    district: str
    password: str
    
    @validator('username')
    def username_alphanumeric(cls, v):
        if not v.replace('_', '').isalnum():
            raise ValueError('Username must be alphanumeric')
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters')
        return v
    
    @validator('telephone')
    def validate_phone(cls, v):
        # Basic Rwanda phone validation
        if not v.startswith('+250') and not v.startswith('250'):
            raise ValueError('Phone must be Rwanda number (+250...)')
        return v

class UserLogin(BaseModel):
    username: str
    password: str

class UserProfile(BaseModel):
    user_id: int
    username: str
    email: str
    first_name: str
    last_name: str
    telephone: str
    district: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserProfileUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    telephone: Optional[str] = None
    district: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserProfile

class SessionCreate(BaseModel):
    variety: str
    storage_technology: str
    grain_impurities_pct: float
    initial_total_damage_pct: float
    initial_storage_time_days: int = 0
    
    @validator('variety')
    def validate_variety(cls, v):
        v = v.lower().strip()
        if v not in ['native', 'hybrid']:
            raise ValueError('Variety must be "native" or "hybrid"')
        return v
    
    @validator('grain_impurities_pct', 'initial_total_damage_pct')
    def validate_percentage(cls, v):
        if not 0 <= v <= 100:
            raise ValueError('Percentage must be between 0 and 100')
        return v

class SessionResponse(BaseModel):
    session_id: int
    user_id: int
    variety: str
    storage_technology: str
    grain_impurities_pct: float
    initial_total_damage_pct: float
    initial_storage_time_days: int
    start_date: datetime
    status: str
    storage_duration_days: int
    
    class Config:
        from_attributes = True

class ManualPredictionRequest(BaseModel):
    variety: str
    storage_technology: str
    grain_impurities_pct: float
    initial_total_damage_pct: float
    temperature: float
    humidity: float
    storage_time_days: int
    
    @validator('variety')
    def validate_variety(cls, v):
        v = v.lower().strip()
        if v not in ['native', 'hybrid']:
            raise ValueError('Variety must be "native" or "hybrid"')
        return v
    
    @validator('grain_impurities_pct', 'initial_total_damage_pct', 'humidity')
    def validate_percentage(cls, v):
        if not 0 <= v <= 100:
            raise ValueError('Percentage must be between 0 and 100')
        return v
    
    @validator('temperature')
    def validate_temperature(cls, v):
        if not 10 <= v <= 40:
            raise ValueError('Temperature must be between 10°C and 40°C')
        return v
    
    @validator('storage_time_days')
    def validate_storage_days(cls, v):
        if v < 0:
            raise ValueError('Storage time cannot be negative')
        return v

class ManualPredictionResponse(BaseModel):
    predicted_damage_pct: float
    risk_level: str
    recommendation_text: str

class NotificationResponse(BaseModel):
    notification_id: int
    message_content: str
    sent_at: datetime
    notification_type: str
    
    class Config:
        from_attributes = True

class UpcomingCheckInResponse(BaseModel):
    """Response model for upcoming check-in info"""
    next_check_time: str
    next_check_date: str
    location: str
    current_temperature: float
    current_humidity: float
    weather_description: str

# AUTHENTICATION UTILITIES

def create_access_token(data: dict):
    """Create JWT token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token and return user_id"""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

def get_current_user(user_id: int = Depends(verify_token)):
    """Get current authenticated user"""
    db = get_db()
    try:
        user = get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user
    finally:
        db.close()

# AUTHENTICATION ENDPOINTS

@app.post("/api/auth/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister):
    """Register a new user"""
    db = get_db()
    try:
        if get_user_by_username(db, user_data.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        if get_user_by_email(db, user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            telephone=user_data.telephone,
            district=user_data.district
        )
        new_user.set_password(user_data.password)
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        logger.info(f" New user registered: {new_user.username}")
        
        access_token = create_access_token({"user_id": new_user.user_id})
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            user=UserProfile.from_orm(new_user)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f" Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )
    finally:
        db.close()

@app.post("/api/auth/login", response_model=Token)
async def login(credentials: UserLogin):
    """Login user"""
    db = get_db()
    try:
        user = get_user_by_username(db, credentials.username)
        
        if not user or not user.check_password(credentials.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        
        user.last_login = datetime.utcnow()
        db.commit()
        
        access_token = create_access_token({"user_id": user.user_id})
        
        logger.info(f" User logged in: {user.username}")
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            user=UserProfile.from_orm(user)
        )
        
    finally:
        db.close()

@app.get("/api/auth/profile", response_model=UserProfile)
async def get_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return UserProfile.from_orm(current_user)

@app.put("/api/auth/profile", response_model=UserProfile)
async def update_profile(
    updates: UserProfileUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update user profile"""
    db = get_db()
    try:
        user = db.query(User).get(current_user.user_id)
        
        if updates.email:
            existing = get_user_by_email(db, updates.email)
            if existing and existing.user_id != user.user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already in use"
                )
            user.email = updates.email
        
        if updates.first_name:
            user.first_name = updates.first_name
        if updates.last_name:
            user.last_name = updates.last_name
        if updates.telephone:
            user.telephone = updates.telephone
        if updates.district:
            user.district = updates.district
        
        db.commit()
        db.refresh(user)
        
        logger.info(f" Profile updated: {user.username}")
        
        return UserProfile.from_orm(user)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f" Profile update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed"
        )
    finally:
        db.close()

@app.post("/api/auth/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Logout user """
    logger.info(f" User logged out: {current_user.username}")
    return {"message": "Logged out successfully"}

# SESSION MANAGEMENT ENDPOINTS

@app.post("/api/sessions/start", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def start_session(
    session_data: SessionCreate,
    current_user: User = Depends(get_current_user)
):
    """Start new automated storage session"""
    db = get_db()
    try:
        new_session = create_storage_session(
            db=db,
            user_id=current_user.user_id,
            variety=session_data.variety,
            storage_technology=session_data.storage_technology,
            grain_impurities_pct=session_data.grain_impurities_pct,
            initial_total_damage_pct=session_data.initial_total_damage_pct,
            initial_storage_time_days=session_data.initial_storage_time_days
        )
        
        logger.info(f" Session started: {new_session.session_id} for user {current_user.username}")
        
        response = SessionResponse(
            session_id=new_session.session_id,
            user_id=new_session.user_id,
            variety=new_session.variety,
            storage_technology=new_session.storage_technology,
            grain_impurities_pct=new_session.grain_impurities_pct,
            initial_total_damage_pct=new_session.initial_total_damage_pct,
            initial_storage_time_days=new_session.initial_storage_time_days,
            start_date=new_session.start_date,
            status=new_session.status,
            storage_duration_days=new_session.get_storage_duration_days()
        )
        
        return response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Session creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create session"
        )
    finally:
        db.close()

@app.get("/api/sessions/check")
async def check_active_session(current_user: User = Depends(get_current_user)):
    """Check if user has an active session"""
    db = get_db()
    try:
        active_session = get_user_active_session(db, current_user.user_id)
        
        if not active_session:
            return {
                "has_active_session": False,
                "session": None
            }
        
        return {
            "has_active_session": True,
            "session": SessionResponse(
                session_id=active_session.session_id,
                user_id=active_session.user_id,
                variety=active_session.variety,
                storage_technology=active_session.storage_technology,
                grain_impurities_pct=active_session.grain_impurities_pct,
                initial_total_damage_pct=active_session.initial_total_damage_pct,
                initial_storage_time_days=active_session.initial_storage_time_days,
                start_date=active_session.start_date,
                status=active_session.status,
                storage_duration_days=active_session.get_storage_duration_days()
            )
        }
        
    finally:
        db.close()

@app.post("/api/sessions/end")
async def end_session(current_user: User = Depends(get_current_user)):
    """End user's active session"""
    db = get_db()
    try:
        ended_session = end_user_active_session(db, current_user.user_id)
        
        if not ended_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active session found"
            )
        
        logger.info(f"Session ended: {ended_session.session_id} for user {current_user.username}")
        
        return {
            "message": "Session ended successfully",
            "session_id": ended_session.session_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Session end error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to end session"
        )
    finally:
        db.close()

# PREDICTION ENDPOINTS

@app.post("/api/predict/manual", response_model=ManualPredictionResponse)
async def manual_prediction(
    prediction_data: ManualPredictionRequest,
    current_user: User = Depends(get_current_user)
):
    """Manual prediction - one-time prediction with all inputs provided"""
    try:
        processor = FeatureProcessor()
        predictor = get_predictor()
  
        raw_features = {
            'tmax_c': prediction_data.temperature,
            'hrmin_pct': prediction_data.humidity,
            'storage_time_days': prediction_data.storage_time_days,
            'grain_impurities_pct': prediction_data.grain_impurities_pct,
            'initial_total_damage_pct': prediction_data.initial_total_damage_pct,
            'storage_technology': prediction_data.storage_technology,
            'variety': prediction_data.variety
        }
        
        feature_array = processor._encode_features(raw_features)
        predicted_damage = predictor.predict(feature_array)
        
        recommendation = get_recommendation(
            predicted_damage_pct=predicted_damage,
            tmax_c=prediction_data.temperature,
            hrmin_pct=prediction_data.humidity,
            storage_time_days=prediction_data.storage_time_days,
            grain_impurities_pct=prediction_data.grain_impurities_pct,
            initial_total_damage_pct=prediction_data.initial_total_damage_pct,
            location=current_user.district,
            variety=prediction_data.variety,
            storage_technology=prediction_data.storage_technology
        )
        
        logger.info(f"Manual prediction: {predicted_damage:.2f}% for user {current_user.username}")
        
        return ManualPredictionResponse(
            predicted_damage_pct=round(predicted_damage, 2),
            risk_level=recommendation['risk_level'],
            recommendation_text=recommendation['recommendation_text']
        )
        
    except Exception as e:
        logger.error(f"Manual prediction error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )

# NOTIFICATION ENDPOINTS

@app.get("/api/notifications", response_model=List[NotificationResponse])
async def get_notifications(current_user: User = Depends(get_current_user)):
    """Get all notifications for current user"""
    db = get_db()
    try:
        notifications = get_user_notifications(db, current_user.user_id, limit=None)
        
        return [
            NotificationResponse(
                notification_id=notif.notification_id,
                message_content=notif.message_content,
                sent_at=notif.sent_at,
                notification_type=notif.notification_type
            )
            for notif in notifications
        ]
        
    finally:
        db.close()

# UPCOMING CHECK-IN ENDPOINT

@app.get("/api/sessions/upcoming-checkin", response_model=UpcomingCheckInResponse)
async def get_upcoming_checkin(current_user: User = Depends(get_current_user)):
    """Get information for the upcoming automated check-in"""
    db = get_db()
    try:
        active_session = get_user_active_session(db, current_user.user_id)
        
        if not active_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active session found. Start a session to see upcoming check-in."
            )
        
        from weather_info.weather import WeatherDataRetriever
        weather_retriever = WeatherDataRetriever()
        weather_data = weather_retriever.get_weather_for_user(current_user)
        
        if not weather_data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not retrieve weather data"
            )
        
        DAILY_CHECK_HOUR = 15  # 3:00 PM
        now = datetime.now()
        
        if now.hour < DAILY_CHECK_HOUR:
            next_check = now.replace(hour=DAILY_CHECK_HOUR, minute=0, second=0, microsecond=0)
            next_check_date_str = "Today"
        else:
            next_check = (now + timedelta(days=1)).replace(hour=DAILY_CHECK_HOUR, minute=0, second=0, microsecond=0)
            next_check_date_str = "Tomorrow"
        
        next_check_time_str = next_check.strftime("%I:%M %p")
        temp = weather_data['temperature']
        humidity = weather_data['humidity']
        
        if temp > 30:
            weather_desc = "Hot and humid" if humidity > 70 else "Hot and dry"
        elif temp > 25:
            weather_desc = "Warm and humid" if humidity > 70 else "Warm and pleasant"
        elif temp > 20:
            weather_desc = "Mild and humid" if humidity > 70 else "Mild and comfortable"
        else:
            weather_desc = "Cool and humid" if humidity > 70 else "Cool and dry"
        
        logger.info(f"Upcoming check-in info retrieved for user {current_user.username}")
        
        return UpcomingCheckInResponse(
            next_check_time=next_check_time_str,
            next_check_date=next_check_date_str,
            location=current_user.district,
            current_temperature=round(weather_data['temperature'], 1),
            current_humidity=round(weather_data['humidity'], 1),
            weather_description=weather_desc
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upcoming check-in error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve upcoming check-in information"
        )
    finally:
        db.close()

# SCHEDULER ADMIN ENDPOINTS

@app.post("/api/admin/trigger-predictions")
async def trigger_predictions_manually(current_user: User = Depends(get_current_user)):
    """
    Manually trigger daily predictions (for testing/admin)
    """
    logger.info(f" Manual prediction triggered by {current_user.username}")
    
    scheduler = get_scheduler()
    result = scheduler.trigger_manual_run()
    
    return result

@app.get("/api/admin/scheduler-status")
async def get_scheduler_status(current_user: User = Depends(get_current_user)):
    """Get current scheduler status"""
    scheduler = get_scheduler()
    
    if not scheduler.is_running:
        return {
            "status": "stopped",
            "next_run": None
        }
    
    job = scheduler.scheduler.get_job('daily_predictions')
    if job and job.next_run_time:
        next_run = job.next_run_time.strftime('%Y-%m-%d %H:%M:%S')
    else:
        next_run = None
    
    return {
        "status": "running",
        "next_run": next_run,
        "scheduled_time": "15:00 (3:00 PM) Rwanda Time"
    }

# HEALTH CHECK ENDPOINTS

@app.get("/")
async def root():
    """Root endpoint - API health check"""
    return {
        "status": "online",
        "service": "Crop Storage Management API",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Detailed health check including scheduler status"""
    db = get_db()
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except:
        db_status = "disconnected"
    finally:
        db.close()
    
    # Check scheduler status
    scheduler = get_scheduler()
    scheduler_status = "running" if scheduler.is_running else "stopped"
    
    next_run = None
    if scheduler.is_running:
        job = scheduler.scheduler.get_job('daily_predictions')
        if job:
            next_run = job.next_run_time.isoformat() if job.next_run_time else None
    
    return {
        "status": "healthy",
        "database": db_status,
        "scheduler": scheduler_status,
        "next_scheduled_run": next_run,
        "timestamp": datetime.utcnow().isoformat()
    }

# RUN APPLICATION

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)