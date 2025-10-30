"""
Weather Data Retrieval Module for Predictive Crop Storage Management System
Retrieves and processes weather data from Open-Meteo API for Rwanda locations
Integrates with database to get user locations automatically
No API key required!
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))


import requests
import logging
from datetime import datetime
from typing import Dict, Optional
from weather_info.locations import RwandaLocations

# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format='%(message)s'
)
logger = logging.getLogger(__name__)

# Completely silence SQLAlchemy
logging.getLogger('sqlalchemy').setLevel(logging.ERROR)
logging.getLogger('sqlalchemy.engine').setLevel(logging.ERROR)


class WeatherDataRetriever:
    """
    Handles weather data retrieval from Open-Meteo API
    Retrieves current weather data for any district in Rwanda
    Integrates with database to automatically fetch user locations
    No API key required!
    """
    
    def __init__(self):
        """
        Initialize weather retriever with Open-Meteo endpoint
        """
        self.base_url = "https://api.open-meteo.com/v1/forecast"
        self.locations = RwandaLocations()
        
        logger.info("WeatherDataRetriever initialized with Open-Meteo API")
    
    def get_current_weather(self, district: str, sector: Optional[str] = None) -> Optional[Dict]:
        """
        Retrieve current weather data for a specific district
        This is the MAIN method - use this in your daily predictions!
        
        Args:
            district: District name (e.g., 'Gasabo', 'Huye', 'Musanze')
            sector: Optional sector name (e.g., 'Bumbogo')
            
        Returns:
            Dictionary containing temperature and humidity, or None if request fails
        """
        # Convert district name to coordinates
        coords = self.locations.get_coordinates(district, sector)
        
        if not coords:
            logger.error(f"Could not find coordinates for {district}" + (f", {sector}" if sector else ""))
            return None
        
        logger.info(f"Retrieved coordinates for {district}" + (f", {sector}" if sector else "") + f": {coords}")
        
        # Fetch weather data from API
        lat, lon = coords['lat'], coords['lon']
        
        params = {
            'latitude': lat,
            'longitude': lon,
            'current': 'temperature_2m,relative_humidity_2m',
            'timezone': 'Africa/Kigali'
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"Successfully retrieved current weather for {district}")
            return self._process_current_weather(data, district, sector)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error retrieving current weather: {e}")
            return None
    
    def get_weather_for_user(self, user) -> Optional[Dict]:
        """
        Retrieve weather data for a user's location from database
        
        Args:
            user: User object from database (must have 'district' attribute)
            
        Returns:
            Dictionary containing temperature and humidity, or None if request fails
            
        Example:
            from database import get_db, User
            db = get_db()
            user = db.query(User).filter(User.username == 'farmer_john').first()
            weather = retriever.get_weather_for_user(user)
        """
        if not user or not hasattr(user, 'district'):
            logger.error("Invalid user object or missing district attribute")
            return None
        
        district = user.district
        logger.info(f"Retrieving weather for user {user.username} in {district}")
        
        return self.get_current_weather(district=district)
    
    def get_weather_for_session(self, session, db) -> Optional[Dict]:
        """
        Retrieve weather data for a storage session's location
        Automatically looks up the user's district from the database
        
        Args:
            session: StorageSession object from database
            db: Database session for querying user data
            
        Returns:
            Dictionary containing temperature and humidity, or None if request fails
            
        Example:
            from database import get_db, get_active_sessions
            db = get_db()
            active_sessions = get_active_sessions(db)
            
            for session in active_sessions:
                weather = retriever.get_weather_for_session(session, db)
                # Use weather data for prediction...
        """
        if not session:
            logger.error("Invalid session object")
            return None
        
        # Get user from session
        user = session.user if hasattr(session, 'user') else None
        
        if not user:
            from database import User
            user = db.query(User).get(session.user_id)
        
        if not user:
            logger.error(f"Could not find user for session {session.session_id}")
            return None
        
        return self.get_weather_for_user(user)
    
    def _process_current_weather(self, raw_data: Dict, district: str, sector: Optional[str] = None) -> Dict:
        """
        Extract and process relevant weather features for ML model
        
        Args:
            raw_data: Raw API response from Open-Meteo
            district: District name for metadata
            sector: Optional sector name for metadata
            
        Returns:
            Processed weather data with temperature and humidity only
        """
        current = raw_data.get('current', {})
        
        location_name = district
        if sector:
            location_name = f"{district}, {sector}"
        
        processed = {
            # Core parameters for ML model
            'temperature': current.get('temperature_2m'),
            'humidity': current.get('relative_humidity_2m'),
            
            # Metadata
            'timestamp': datetime.fromisoformat(current.get('time').replace('Z', '+00:00')),
            'location': location_name,
            'data_source': 'Open-Meteo'
        }
        
        return processed
    
    def validate_weather_data(self, weather_data: Dict) -> bool:
        """
        Validate that weather data meets quality standards
        
        Args:
            weather_data: Weather data to validate
            
        Returns:
            True if data is valid, False otherwise
        """
        required_fields = ['temperature', 'humidity']
        
        # Check required fields exist
        if not all(field in weather_data for field in required_fields):
            logger.warning("Weather data missing required fields")
            return False
        
        # Check for None values
        if weather_data.get('temperature') is None or weather_data.get('humidity') is None:
            logger.warning("Weather data contains None values")
            return False
        
        # Check reasonable value ranges for Rwanda climate
        temp = weather_data.get('temperature')
        humidity = weather_data.get('humidity')
        
        if not (10 <= temp <= 40):
            logger.warning(f"Temperature {temp}°C outside expected range")
            return False
        
        if not (20 <= humidity <= 100):
            logger.warning(f"Humidity {humidity}% outside expected range")
            return False
        
        return True


# Unit tests
if __name__ == "__main__":
    print("=== Weather Module Test ===\n")
    
    # Initialize retriever
    retriever = WeatherDataRetriever()
    
    # Try database integration first
    try:
        from database import get_db, User, get_active_sessions
        
        print(" Database Connection: Connected")
        db = get_db()
        
        # Test with existing user
        user = db.query(User).first()
        if user:
            weather = retriever.get_weather_for_user(user)
            if weather and retriever.validate_weather_data(weather):
                print(f"\n User: {user.username}")
                print(f" Location: {weather['location']}")
                print(f"  Temperature: {weather['temperature']}°C")
                print(f" Humidity: {weather['humidity']}%")
                print(f" Timestamp: {weather['timestamp']}")
                print(f" Data Valid: Yes")
            else:
                print("  Could not retrieve valid weather data")
        else:
            print("  No users found in database")
        
        db.close()
        print("\n Weather module operational and ready for automation!")
        
    except ImportError:
        # Database not available, run basic test
        print(" Database Connection:  Not available")
        print("\n Running basic weather test...\n")
        
        weather = retriever.get_current_weather(district='Gasabo')
        if weather and retriever.validate_weather_data(weather):
            print(f" Location: {weather['location']}")
            print(f" Temperature: {weather['temperature']}°C")
            print(f" Humidity: {weather['humidity']}%")
            print(f" Timestamp: {weather['timestamp']}")
            print(f" Data Valid: Yes")
            print("\n Weather API working correctly!")
        else:
            print(" Weather retrieval failed")
    
    except Exception as e:
        print(f" Error: {e}")
        print("\n Falling back to basic test...\n")
        
        weather = retriever.get_current_weather(district='Gasabo')
        if weather:
            print(f" Location: {weather['location']}")
            print(f" Temperature: {weather['temperature']}°C")
            print(f" Humidity: {weather['humidity']}%")
            print(" Basic weather retrieval working")