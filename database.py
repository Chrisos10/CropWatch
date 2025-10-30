"""
Database Schema for Predictive Crop Storage Management System
PostgreSQL database with SQLAlchemy ORM
Handles users, storage sessions, predictions, and notifications
"""

import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, Date, Enum, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from werkzeug.security import generate_password_hash, check_password_hash
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
Base = declarative_base()

# Get database URL from environment variable
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///crop_storage.db')

if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

# Create engine with connection pooling and retry logic
engine = create_engine(
    DATABASE_URL, 
    echo=False,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=5,
    max_overflow=10,
    connect_args={
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
    }
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Model Definitions

class User(Base):
    """
    Users/Farmers table
    Stores registration and authentication details
    """
    __tablename__ = 'users'
    
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    telephone = Column(String(20), unique=True, nullable=False)
    district = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    storage_sessions = relationship('StorageSession', back_populates='user', cascade='all, delete-orphan')
    notifications = relationship('Notification', back_populates='user', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set user password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify user password"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f"<User(id={self.user_id}, username='{self.username}', district='{self.district}')>"


class StorageSession(Base):
    """
    Storage Sessions table
    One session per active storage period
    Only one active session per user at a time
    """
    __tablename__ = 'storage_sessions'
    
    session_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    
    # Model features (user-provided at session start)
    variety = Column(String(50), nullable=False)
    storage_technology = Column(String(150), nullable=False)
    grain_impurities_pct = Column(Float, nullable=False)
    initial_total_damage_pct = Column(Float, nullable=False)
    initial_storage_time_days = Column(Integer, nullable=False, default=0)
    
    # Session timing
    start_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    end_date = Column(DateTime, nullable=True)
    status = Column(Enum('active', 'completed', name='session_status'), nullable=False, default='active')
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='storage_sessions')
    predictions = relationship('DailyPrediction', back_populates='session', cascade='all, delete-orphan')
    
    def get_storage_duration_days(self):
        """Calculate how many days the session has been running"""
        if self.status == 'active':
            return (datetime.utcnow() - self.start_date).days
        else:
            return (self.end_date - self.start_date).days if self.end_date else 0
    
    def __repr__(self):
        return f"<StorageSession(id={self.session_id}, user_id={self.user_id}, status='{self.status}', variety='{self.variety}')>"


class DailyPrediction(Base):
    """
    Daily Predictions table
    Stores daily ML predictions with weather data and recommendations
    One record per day per active session
    """
    __tablename__ = 'daily_predictions'
    
    prediction_id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('storage_sessions.session_id', ondelete='CASCADE'), nullable=False)
    
    # Prediction metadata
    prediction_date = Column(Date, nullable=False, default=datetime.utcnow().date)
    storage_time_days = Column(Integer, nullable=False)
    
    # Weather data retrieved from API
    tmax_c = Column(Float, nullable=False)
    hrmin_pct = Column(Float, nullable=False)
    
    # Model output
    predicted_total_damage_pct = Column(Float, nullable=False)
    
    # Recommendation from recommendations.py module
    risk_level = Column(Enum('low', 'medium', 'high', name='risk_levels'), nullable=False)
    recommendation_text = Column(Text, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship('StorageSession', back_populates='predictions')
    notifications = relationship('Notification', back_populates='prediction')
    
    def __repr__(self):
        return f"<DailyPrediction(id={self.prediction_id}, session_id={self.session_id}, risk='{self.risk_level}', damage={self.predicted_total_damage_pct:.2f}%)>"


class Notification(Base):
    """
    Notifications table
    Stores notification history (web notifications only)
    """
    __tablename__ = 'notifications'
    
    notification_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    prediction_id = Column(Integer, ForeignKey('daily_predictions.prediction_id', ondelete='CASCADE'), nullable=True)
    
    # Notification content
    message_content = Column(Text, nullable=False)
    notification_type = Column(Enum('daily_alert', 'warning', 'critical', 'info', name='notification_types'), 
                               nullable=False, default='daily_alert')
    
    # Delivery tracking
    sent_at = Column(DateTime, default=datetime.utcnow)
    delivery_status = Column(Enum('pending', 'sent', 'failed', name='delivery_status'), 
                            nullable=False, default='sent')  # Default to 'sent' for web notifications
    
    # Relationships
    user = relationship('User', back_populates='notifications')
    prediction = relationship('DailyPrediction', back_populates='notifications')
    
    def __repr__(self):
        return f"<Notification(id={self.notification_id}, user_id={self.user_id}, status='{self.delivery_status}')>"


# Database helper functions

def init_db():
    """
    Initialize database - create all tables
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info(" Database tables created successfully!")
    except Exception as e:
        logger.error(f" Error creating database tables: {e}")
        raise


def get_db():
    """
    Get database session with connection verification
    """
    db = SessionLocal()
    try:
        # Test the connection with text() wrapper for SQLAlchemy 2.0
        db.execute(text("SELECT 1"))
        return db
    except Exception as e:
        logger.error(f"Database connection error, attempting to reconnect: {e}")
        db.close()
        # Try to get a fresh connection
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            return db
        except Exception as retry_error:
            logger.error(f"Failed to reconnect to database: {retry_error}")
            raise


def drop_all_tables():
    """
    DROP ALL TABLES
    """
    logger.warning(" Dropping all database tables...")
    Base.metadata.drop_all(bind=engine)
    logger.info(" All tables dropped")


# Query helper functions

def get_user_by_username(db, username: str):
    """Get user by username"""
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db, email: str):
    """Get user by email"""
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db, user_id: int):
    """Get user by ID"""
    return db.query(User).filter(User.user_id == user_id).first()


def get_active_sessions(db):
    """Get all active storage sessions"""
    return db.query(StorageSession).filter(StorageSession.status == 'active').all()


def get_user_active_session(db, user_id: int):
    """Get user's active session if exists"""
    return db.query(StorageSession).filter(
        StorageSession.user_id == user_id,
        StorageSession.status == 'active'
    ).first()


def get_session_predictions(db, session_id: int, limit: int = 30):
    """Get recent predictions for a session"""
    return db.query(DailyPrediction).filter(
        DailyPrediction.session_id == session_id
    ).order_by(DailyPrediction.prediction_date.desc()).limit(limit).all()


def get_user_notifications(db, user_id: int, limit: int = None):
    """
    Get notifications for a user
    If limit is None, return all notifications
    """
    query = db.query(Notification).filter(
        Notification.user_id == user_id
    ).order_by(Notification.sent_at.desc())
    
    if limit:
        query = query.limit(limit)
    
    return query.all()


def create_storage_session(db, user_id: int, variety: str, storage_technology: str, 
                          grain_impurities_pct: float, initial_total_damage_pct: float,
                          initial_storage_time_days: int = 0):
    """
    Create new storage session
    Ensures user doesn't have an active session already
    
    Args:
        db: Database session
        user_id: User ID
        variety: 'native' or 'hybrid' (user types this)
        storage_technology: Storage method (user types this)
        grain_impurities_pct: Grain impurities percentage
        initial_total_damage_pct: Initial damage percentage
        initial_storage_time_days: Initial storage time in days (default 0)
        
    Returns:
        Created StorageSession object
        
    Raises:
        ValueError: If user already has an active session
    """
    # Check for existing active session
    existing = get_user_active_session(db, user_id)
    if existing:
        raise ValueError("You already have an active storage session. Please end it first.")
    
    # Create new session
    new_session = StorageSession(
        user_id=user_id,
        variety=variety.lower(),
        storage_technology=storage_technology.lower(),
        grain_impurities_pct=grain_impurities_pct,
        initial_total_damage_pct=initial_total_damage_pct,
        initial_storage_time_days=initial_storage_time_days,
        status='active',
        start_date=datetime.utcnow()
    )
    
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    
    logger.info(f" Created storage session {new_session.session_id} for user {user_id}")
    return new_session


def end_user_active_session(db, user_id: int):
    """
    End user's active session (user clicks "End Session" button)
    Stops daily predictions but keeps all notification history
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        Updated StorageSession object or None if no active session
    """
    active_session = get_user_active_session(db, user_id)
    
    if not active_session:
        return None
    
    # Update session
    active_session.status = 'completed'
    active_session.end_date = datetime.utcnow()
    
    db.commit()
    db.refresh(active_session)
    
    logger.info(f" Ended storage session {active_session.session_id} for user {user_id}")
    return active_session


def terminate_storage_session(db, session_id: int):
    """
    Terminate an active storage session by session ID
    
    Args:
        db: Database session
        session_id: Session ID to terminate
        
    Returns:
        Updated StorageSession object
        
    Raises:
        ValueError: If session not found or already completed
    """
    session = db.query(StorageSession).get(session_id)
    
    if not session:
        raise ValueError("Storage session not found")
    
    if session.status == 'completed':
        raise ValueError("Storage session is already completed")
    
    # Update session
    session.status = 'completed'
    session.end_date = datetime.utcnow()
    
    db.commit()
    db.refresh(session)
    
    logger.info(f" Terminated storage session {session_id}")
    return session


def create_daily_prediction(db, session_id: int, storage_time_days: int, 
                           tmax_c: float, hrmin_pct: float, 
                           predicted_total_damage_pct: float,
                           risk_level: str, recommendation_text: str):
    """
    Create a daily prediction record
    
    Args:
        db: Database session
        session_id: Storage session ID
        storage_time_days: Current storage duration in days
        tmax_c: Temperature in Celsius
        hrmin_pct: Minimum relative humidity percentage
        predicted_total_damage_pct: ML model prediction
        risk_level: 'low', 'medium', or 'high'
        recommendation_text: Generated recommendation
        
    Returns:
        Created DailyPrediction object
    """
    prediction = DailyPrediction(
        session_id=session_id,
        storage_time_days=storage_time_days,
        tmax_c=tmax_c,
        hrmin_pct=hrmin_pct,
        predicted_total_damage_pct=predicted_total_damage_pct,
        risk_level=risk_level,
        recommendation_text=recommendation_text,
        prediction_date=datetime.utcnow().date()
    )
    
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    
    logger.info(f"Created daily prediction {prediction.prediction_id} for session {session_id}")
    return prediction


def create_notification(db, user_id: int, prediction_id: int, message_content: str):
    """
    Create a notification record
    
    Args:
        db: Database session
        user_id: User ID
        prediction_id: Associated prediction ID
        message_content: Notification message
        
    Returns:
        Created Notification object
    """
    notification = Notification(
        user_id=user_id,
        prediction_id=prediction_id,
        message_content=message_content,
        notification_type='daily_alert',
        delivery_status='sent'
    )
    
    db.add(notification)
    db.commit()
    db.refresh(notification)
    
    logger.info(f" Created notification {notification.notification_id} for user {user_id}")
    return notification


# Unit tests

if __name__ == "__main__":
    print("=== Crop Storage Database Schema ===\n")
    
    # Initialize database (create tables)
    print("1. Initializing database...")
    init_db()
    
    # Get database session
    db = get_db()
    
    try:
        # Example 1: Create a user
        print("\n2. Creating test user...")
        test_user = User(
            username='farmer_test',
            email='farmer@example.com',
            first_name='Jean',
            last_name='Mugisha',
            telephone='+250788123456',
            district='Gasabo'
        )
        test_user.set_password('securepassword123')
        db.add(test_user)
        db.commit()
        print(f" Created: {test_user}")
        
        # Example 2: Create a storage session
        print("\n3. Creating storage session...")
        test_session = create_storage_session(
            db=db,
            user_id=test_user.user_id,
            variety='hybrid',
            storage_technology='hermetic metal silo',
            grain_impurities_pct=2.0,
            initial_total_damage_pct=1.0,
            initial_storage_time_days=0
        )
        print(f" Created: {test_session}")
        
        # Example 3: Create a prediction
        print("\n4. Creating daily prediction...")
        test_prediction = create_daily_prediction(
            db=db,
            session_id=test_session.session_id,
            storage_time_days=10,
            tmax_c=25.5,
            hrmin_pct=65.0,
            predicted_total_damage_pct=2.3,
            risk_level='low',
            recommendation_text='Storage conditions are optimal. No action needed.'
        )
        print(f"Created: {test_prediction}")
        
        # Example 4: Create a notification
        print("\n5. Creating notification...")
        notification_message = f"""Notification_01
Date: {datetime.now().strftime('%d-%m-%Y')} Time: {datetime.now().strftime('%H:%M:%S')}
Location: Gasabo
Potential 2.3% spoilage detected.
Recommendation: Storage conditions are optimal. No action needed. Keep monitoring regularly."""
        
        test_notification = create_notification(
            db=db,
            user_id=test_user.user_id,
            prediction_id=test_prediction.prediction_id,
            message_content=notification_message
        )
        print(f" Created: {test_notification}")
        
        # Example 5: Query active sessions
        print("\n6. Querying active sessions...")
        active_sessions = get_active_sessions(db)
        print(f" Found {len(active_sessions)} active session(s)")
        
        # Example 6: Verify password
        print("\n7. Testing password verification...")
        print(f" Correct password: {test_user.check_password('securepassword123')}")
        print(f" Wrong password: {test_user.check_password('wrongpassword')}")
        
        # Example 7: Get user notifications
        print("\n8. Querying user notifications...")
        notifications = get_user_notifications(db, test_user.user_id)
        print(f" Found {len(notifications)} notification(s)")
        
        # Example 8: End session
        print("\n9. Ending storage session...")
        ended_session = end_user_active_session(db, test_user.user_id)
        print(f" Ended: {ended_session}")
        
        print("\n Database schema test completed successfully!")
        
    except Exception as e:
        print(f"\n Error during testing: {e}")
        db.rollback()
    finally:
        db.close()