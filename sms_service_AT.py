from dotenv import load_dotenv
load_dotenv()

"""
SMS Service Module using Africa's Talking API
Handles SMS notifications for Crop Storage Management System
"""

import os
import logging
import africastalking
from typing import Dict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ATSMSService:
    """
    Handles SMS notifications using Africa's Talking
    Singleton pattern for efficient connection reuse
    """
    
    _instance = None
    _sms = None
    _sender_id = None
    _enabled = True
    
    def __new__(cls):
        """Ensure only one instance is created"""
        if cls._instance is None:
            cls._instance = super(ATSMSService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize Africa's Talking client from environment variables"""
        try:
            # Get credentials from environment
            username = os.getenv('AT_USERNAME', 'sandbox')
            api_key = os.getenv('AT_API_KEY')
            self._sender_id = os.getenv('AT_SENDER_ID', 'CropAlert')
            
            # Check if SMS is enabled
            sms_enabled = os.getenv('AT_ENABLED', 'false').lower()
            self._enabled = sms_enabled in ('true', '1', 'yes')
            
            if not self._enabled:
                logger.info(" SMS notifications are DISABLED (AT_ENABLED=false)")
                return
            
            # Validate credentials
            if not api_key:
                logger.warning("Africa's Talking API key missing, SMS disabled")
                logger.warning("   Required: AT_API_KEY")
                self._enabled = False
                return
            
            # Initialize Africa's Talking
            africastalking.initialize(username, api_key)
            self._sms = africastalking.SMS
            
            logger.info(" Africa's Talking SMS service initialized")
            logger.info(f"   Username: {username}")
            logger.info(f"   Sender ID: {self._sender_id}")
            logger.info("   Mode: SANDBOX (limitations apply)")
            
        except Exception as e:
            logger.error(f" Failed to initialize Africa's Talking: {e}")
            self._enabled = False
    
    def is_enabled(self) -> bool:
        """Check if SMS service is enabled and properly configured"""
        return self._enabled and self._sms is not None
    
    def format_rwanda_phone(self, phone: str) -> str:
        """
        Format Rwanda phone number for Africa's Talking
        
        Africa's Talking accepts: +250788123456 or 250788123456
        
        Args:
            phone: Phone number in various formats
            
        Returns:
            Formatted phone number with country code
        """
        # Remove spaces, dashes, parentheses
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
        Create a SHORT alert message
        
        Args:
            predicted_damage_pct: Predicted damage percentage
            risk_level: Risk level (low/medium/high/critical)
            
        Returns:
            Short message string
        """
        # Round to 1 decimal place
        damage = round(predicted_damage_pct, 1)
        
        # Base message
        message = f"Potential {damage}% spoilage detected. Check your account for details."
        
        # Add urgency for high risk
        if risk_level.lower() in ['high', 'critical']:
            message = f"URGENT: {damage}% spoilage risk! Check your account immediately."
        
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
            Dictionary with send status
        """
        if not self.is_enabled():
            logger.info(f" SMS disabled - Would send to {to_phone}")
            return {
                'status': 'disabled',
                'message': 'SMS service is disabled',
                'phone': to_phone
            }
        
        try:
            # Format phone number
            formatted_phone = self.format_rwanda_phone(to_phone)
            
            # Create short message
            message = self.create_short_alert_message(
                predicted_damage_pct=predicted_damage_pct,
                risk_level=risk_level
            )
            
            # Ensure message is under 160 characters
            if len(message) > 160:
                message = message[:157] + "..."
                logger.warning(f" Message truncated to 160 characters")
            
            # Print what we're sending
            print(f"\n   DEBUG - Sending SMS:")
            print(f"   To: {formatted_phone}")
            print(f"   Message: {message}")
            print(f"   Message length: {len(message)} chars")
            
            # Send SMS via Africa's Talking
            try:
                response = self._sms.send(
                    message=message,
                    recipients=[formatted_phone]
                )
            except Exception as e:
                # If that fails, try with senderId using camelCase
                print(f"   Retrying with senderId parameter...")
                response = self._sms.send(
                    message=message,
                    recipients=[formatted_phone],
                    senderId=self._sender_id
                )
            
            # DEBUG: Print full response
            print(f"\n   DEBUG - Full API Response:")
            print(f"   {response}")
            print()
            
            # Parse response
            if response.get('SMSMessageData') and response['SMSMessageData'].get('Recipients'):
                recipients = response['SMSMessageData']['Recipients']
                
                if len(recipients) > 0:
                    recipient = recipients[0]
                    
                    if recipient.get('status') == 'Success':
                        logger.info(f" SMS sent successfully")
                        logger.info(f"   To: {formatted_phone}")
                        logger.info(f"   Message ID: {recipient.get('messageId', 'N/A')}")
                        logger.info(f"   Cost: {recipient.get('cost', 'N/A')}")
                        logger.info(f"   Length: {len(message)} chars")
                        
                        return {
                            'status': 'sent',
                            'message_id': recipient.get('messageId'),
                            'phone': formatted_phone,
                            'cost': recipient.get('cost'),
                            'at_status': recipient['status']
                        }
                    else:
                        # Failed to send
                        logger.error(f" SMS send failed: {recipient.get('status', 'Unknown')}")
                        logger.error(f"   Status code: {recipient.get('statusCode', 'N/A')}")
                        return {
                            'status': 'failed',
                            'error': recipient.get('status', 'Unknown error'),
                            'status_code': recipient.get('statusCode'),
                            'phone': formatted_phone
                        }
                else:
                    logger.error(f" Recipients list is empty")
                    return {
                        'status': 'failed',
                        'error': 'Recipients list is empty',
                        'phone': to_phone
                    }
            else:
                logger.error(f" No recipients in response")
                logger.error(f"   Full response: {response}")
                return {
                    'status': 'failed',
                    'error': 'No recipients in response data',
                    'phone': to_phone,
                    'full_response': str(response)
                }
            
        except Exception as e:
            # General errors
            logger.error(f"✗ SMS send error: {e}")
            import traceback
            traceback.print_exc()
            return {
                'status': 'failed',
                'error': str(e),
                'phone': to_phone
            }
    
    def test_connection(self) -> Dict:
        """
        Test Africa's Talking connection
        
        Returns:
            Dictionary with connection status
        """
        if not self.is_enabled():
            return {
                'status': 'disabled',
                'message': 'SMS service is not enabled. Check .env configuration.'
            }
        
        try:
            return {
                'status': 'connected',
                'sender_id': self._sender_id,
                'message': 'Africa\'s Talking connection successful'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'message': 'Failed to connect to Africa\'s Talking'
            }


# GLOBAL INSTANCE AND CONVENIENCE FUNCTIONS

_at_sms_service_instance = None

def get_sms_service() -> ATSMSService:
    """
    Get the global SMS service instance
    
    Returns:
        ATSMSService instance
    """
    global _at_sms_service_instance
    if _at_sms_service_instance is None:
        _at_sms_service_instance = ATSMSService()
    return _at_sms_service_instance


def is_sms_enabled() -> bool:
    """
    Returns:
        True if SMS is enabled and configured
    """
    service = get_sms_service()
    return service.is_enabled()


# Unit tests

if __name__ == "__main__":
    """
    Test SMS service configuration
    Usage: python sms_service_at.py
    """
    print("=" * 70)
    print("AFRICA'S TALKING SMS SERVICE TEST")
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
        print("   - AT_USERNAME")
        print("   - AT_API_KEY")
        print("   - AT_SENDER_ID")
        print("   - AT_ENABLED=true")
    
    if sms_service.is_enabled():
        # Test 2: Test connection
        print("\n2. Testing Africa's Talking connection...")
        connection = sms_service.test_connection()
        print(f"   Status: {connection.get('status')}")
        print(f"   Message: {connection.get('message')}")
        
        # Test 3: Test phone formatting
        print("\n3. Testing phone number formatting...")
        test_phones = ['+250788123456', '250788123456', '0788123456', '788123456']
        for phone in test_phones:
            formatted = sms_service.format_rwanda_phone(phone)
            print(f"   {phone:20s} → {formatted}")
        
        # Test 4: Test message creation
        print("\n4. Testing message creation...")
        test_cases = [
            (2.5, 'low'),
            (5.0, 'medium'),
            (8.5, 'high'),
        ]
        
        for damage, risk in test_cases:
            msg = sms_service.create_short_alert_message(damage, risk)
            print(f"   {risk.upper():8s} ({damage}%): {msg}")
            print(f"            Length: {len(msg)} chars")
        
        # Test 5: Send test SMS
        print("\n5. Test SMS sending")
        print("   Attempting to send test SMS...")
        
        test_phone = '+250785960876'
        result = sms_service.send_daily_alert(
            test_phone, 
            predicted_damage_pct=3.5,
            risk_level='medium'
        )
        print(f"\n   Final Result: {result}")
    
    print("\n" + "=" * 70)
    print("AFRICA'S TALKING SMS TEST COMPLETE")
    print("=" * 70)