"""
SMS Service Module for Crop Storage Management System
Handles SMS notifications via Twilio's free instance
"""

import os
import logging
from typing import Dict
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SMSService:
    """
    Handles SMS notifications using Twilio
    Singleton pattern for efficient connection reuse
    Sends SHORT messages for daily predictions only
    """
    
    _instance = None
    _client = None
    _from_number = None
    _enabled = True
    
    def __new__(cls):
        """Creating only one instance created"""
        if cls._instance is None:
            cls._instance = super(SMSService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize Twilio client from environment variables"""
        try:
            # Get credentials from environment
            account_sid = os.getenv('TWILIO_ACCOUNT_SID')
            auth_token = os.getenv('TWILIO_AUTH_TOKEN')
            self._from_number = os.getenv('TWILIO_PHONE_NUMBER')
            
            # Check if SMS is enabled
            sms_enabled = os.getenv('TWILIO_ENABLED', 'false').lower()
            self._enabled = sms_enabled in ('true', '1', 'yes')
            
            if not self._enabled:
                logger.info(" SMS notifications are DISABLED (TWILIO_ENABLED=false)")
                return
            
            # Validate credentials
            if not all([account_sid, auth_token, self._from_number]):
                logger.warning("Twilio credentials incomplete - SMS disabled")
                logger.warning("   Required: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER")
                self._enabled = False
                return
            
            # Initialize Twilio client
            self._client = Client(account_sid, auth_token)
            
            logger.info("Twilio SMS service initialized successfully")
            logger.info(f"   From number: {self._from_number}")
            logger.info("   Mode: SHORT MESSAGES (Trial-friendly)")
            
        except Exception as e:
            logger.error(f"Failed to initialize Twilio: {e}")
            self._enabled = False
    
    def is_enabled(self) -> bool:
        """Check if SMS service is enabled and properly configured"""
        return self._enabled and self._client is not None
    
    def format_rwanda_phone(self, phone: str) -> str:
        """
        Format Rwanda phone number to E.164 format required by Twilio
        
        Handles multiple input formats:
        - +250788123456
        - 250788123456
        - 0788123456
        - 788123456
        
        Returns:
            Formatted phone number in format
        """
        # Remove spaces, dashes, and parentheses
        phone = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        
        # Handle different formats
        if phone.startswith('+250'):
            return phone
        elif phone.startswith('250'):
            return f'+{phone}'
        elif phone.startswith('0'):
            return f'+250{phone[1:]}'
        else:
            return f'+250{phone}'
    
    def create_short_alert_message(self, 
                                   predicted_damage_pct: float, 
                                   risk_level: str) -> str:
        """
        Create a SHORT alert message (trial-friendly)
        
        Args:
            predicted_damage_pct: Predicted damage percentage
            risk_level: Risk level (low/medium/high/critical)
            
        Returns:
            Short message string
        """
        # Round to 1 decimal place
        damage = round(predicted_damage_pct, 1)
        
        # Base message
        message = f" Potential {damage}% spoilage detected. Check your account for further details."
        
        # Add urgency for high risk
        if risk_level.lower() in ['high', 'critical']:
            message = f" URGENT: {damage}% spoilage risk! Check your account immediately."
        
        return message
    
    def send_daily_alert(self, 
                        to_phone: str,
                        predicted_damage_pct: float,
                        risk_level: str) -> Dict:
        """
        Send daily prediction alert SMS
        
        Args:
            to_phone: User's phone number
            predicted_damage_pct: Damage percentage
            risk_level: Risk level (low/medium/high/critical)
            
        Returns:
            Dictionary with send status:
            - status: 'sent', 'disabled', or 'failed'
            - message_sid: Twilio message ID (if sent)
            - phone: Formatted phone number
            - twilio_status: Twilio delivery status
            - error: Error message (if failed)
        """
        if not self.is_enabled():
            logger.info(f"SMS disabled - Would send to {to_phone}")
            return {
                'status': 'disabled',
                'message': 'SMS service is disabled',
                'phone': to_phone
            }
        
        try:
            # Format phone number to E.164
            formatted_phone = self.format_rwanda_phone(to_phone)
            
            # Create short message
            message = self.create_short_alert_message(
                predicted_damage_pct=predicted_damage_pct,
                risk_level=risk_level
            )
            
            # Ensure message is under 160 characters for twilio trial account
            if len(message) > 160:
                message = message[:157] + "..."
                logger.warning(f"Message truncated to 160 characters")
            
            # Send SMS via Twilio
            twilio_message = self._client.messages.create(
                body=message,
                from_=self._from_number,
                to=formatted_phone
            )
            
            logger.info(f"SMS sent successfully")
            logger.info(f"   To: {formatted_phone}")
            logger.info(f"   SID: {twilio_message.sid}")
            logger.info(f"   Status: {twilio_message.status}")
            logger.info(f"   Length: {len(message)} chars")
            
            return {
                'status': 'sent',
                'message_sid': twilio_message.sid,
                'phone': formatted_phone,
                'twilio_status': twilio_message.status
            }
            
        except TwilioRestException as e:
            # Twilio-specific errors
            logger.error(f" Twilio API error: {e.msg}")
            logger.error(f"   Error code: {e.code}")
            return {
                'status': 'failed',
                'error': e.msg,
                'error_code': e.code,
                'phone': to_phone
            }
            
        except Exception as e:
            # General errors
            logger.error(f"SMS send error: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'phone': to_phone
            }
    
    def test_connection(self) -> Dict:
        """
        Test Twilio connection and credentials
        Useful for debugging and setup verification
        
        Returns:
            Dictionary with connection status
        """
        if not self.is_enabled():
            return {
                'status': 'disabled',
                'message': 'SMS service is not enabled. Check .env configuration.'
            }
        
        try:
            # Try to fetch account info to verify connection
            account = self._client.api.accounts(self._client.account_sid).fetch()
            
            return {
                'status': 'connected',
                'account_status': account.status,
                'from_number': self._from_number,
                'message': 'Twilio connection successful'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'message': 'Failed to connect to Twilio'
            }


# GLOBAL INSTANCE AND CONVENIENCE FUNCTIONS

_sms_service_instance = None

def get_sms_service() -> SMSService:
    """
    Get the global SMS service instance (singleton)
    
    Returns:
        SMSService instance
    """
    global _sms_service_instance
    if _sms_service_instance is None:
        _sms_service_instance = SMSService()
    return _sms_service_instance


def is_sms_enabled() -> bool:
    """
    Convenience function: Check if SMS service is enabled
    
    Returns:
        True if SMS is enabled and configured, False otherwise
    """
    service = get_sms_service()
    return service.is_enabled()


# Unittests

if __name__ == "__main__":
    """
    Run this file directly to test SMS service configuration
    Usage: python sms_service.py
    """
    print("=" * 70)
    print("SMS SERVICE CONFIGURATION TEST")
    print("=" * 70)
    
    # Initialize service
    sms_service = get_sms_service()
    
    # Test 1: Check if enabled
    print(f"\n1. SMS Service Status:")
    if sms_service.is_enabled():
        print("   ENABLED")
    else:
        print("   DISABLED")
        print("   Check your .env file for:")
        print("   - TWILIO_ACCOUNT_SID")
        print("   - TWILIO_AUTH_TOKEN")
        print("   - TWILIO_PHONE_NUMBER")
        print("   - TWILIO_ENABLED=true")
    
    if sms_service.is_enabled():
        # Test 2: Test connection
        print("\n2. Testing Twilio connection...")
        connection = sms_service.test_connection()
        print(f"   Status: {connection.get('status')}")
        print(f"   Message: {connection.get('message')}")
        
        # Test 3: Test phone formatting
        print("\n3. Testing phone number formatting...")
        test_phones = ['+250788123456', '250788123456', '0788123456', '788123456']
        for phone in test_phones:
            formatted = sms_service.format_rwanda_phone(phone)
            print(f"   {phone:20s} → {formatted}")
        
        # Test 4: Test short message creation
        print("\n4. Testing short message creation...")
        
        test_cases = [
            (2.5, 'low'),
            (5.0, 'medium'),
            (8.5, 'high'),
        ]
        
        for damage, risk in test_cases:
            msg = sms_service.create_short_alert_message(damage, risk)
            print(f"   {risk.upper():8s} ({damage}%): {msg}")
            print(f"            Length: {len(msg)} chars")
        
        # Test 5: Send test SMS (COMMENTED OUT)
        print("\n5. Test SMS sending")
        print("   To send a test SMS, uncomment the code below and add your number")
        
        # UNCOMMENT TO SEND REAL TEST:
        # test_phone = '+250785960876'  # Your verified number
        # result = sms_service.send_daily_alert(
        #     test_phone, 
        #     predicted_damage_pct=3.5,
        #     risk_level='medium'
        # )
        # print(f"   Result: {result}")
    
    print("\n" + "=" * 70)
    print("SMS SERVICE TEST COMPLETE")
    print("=" * 70)