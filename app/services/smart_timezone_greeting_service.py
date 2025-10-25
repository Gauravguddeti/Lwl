"""
Smart Timezone Greeting Service - Optimized for worldwide timezone detection
Uses phone number intelligence to determine recipient timezone and scheduled call time for appropriate greetings
"""

import pytz
from datetime import datetime
from typing import Dict, Optional, Union
import phonenumbers
from phonenumbers import geocoder

class SmartTimezoneGreetingService:
    """Optimized service for worldwide timezone-aware greetings based on scheduled call time"""
    
    # Smart timezone mapping - covers 95% of world's phone numbers
    TIMEZONE_MAP = {
        # North America
        'US': {
            'default': 'America/New_York',
            'area_codes': {
                # Eastern (UTC-5/-4)
                '212|646|917|718|347': 'America/New_York',  # NYC
                '215|267|484|610|717|724|570|412|878|445|272|723': 'America/New_York',  # Pennsylvania
                '617|857|781|978|339|351': 'America/New_York',  # Massachusetts
                '305|786|954|561|407|863|904|813|727|941': 'America/New_York',  # Florida
                '404|770|678|912|706|762|470': 'America/New_York',  # Georgia
                
                # Central (UTC-6/-5)
                '312|773|872|708|847|224|630': 'America/Chicago',  # Illinois
                '713|281|832|409|430|903|940|972': 'America/Chicago',  # Texas
                '913|816|417|660': 'America/Chicago',  # Kansas/Missouri
                
                # Mountain (UTC-7/-6)
                '303|720|970|719': 'America/Denver',  # Colorado
                '801|385': 'America/Denver',  # Utah
                '480|602|623|928': 'America/Phoenix',  # Arizona (no DST)
                
                # Pacific (UTC-8/-7)
                '415|628|650|669|408|831|510|925|530': 'America/Los_Angeles',  # California
                '206|253|360|425|564': 'America/Los_Angeles',  # Washington
                '503|541|971': 'America/Los_Angeles',  # Oregon
                
                # Alaska/Hawaii
                '907': 'America/Anchorage',  # Alaska
                '808': 'Pacific/Honolulu',   # Hawaii
            }
        },
        'CA': 'America/Toronto',      # Canada
        
        # Europe
        'GB': 'Europe/London',        # UK
        'DE': 'Europe/Berlin',        # Germany
        'FR': 'Europe/Paris',         # France
        'IT': 'Europe/Rome',          # Italy
        'ES': 'Europe/Madrid',        # Spain
        'NL': 'Europe/Amsterdam',     # Netherlands
        'CH': 'Europe/Zurich',        # Switzerland
        'AT': 'Europe/Vienna',        # Austria
        'BE': 'Europe/Brussels',      # Belgium
        'SE': 'Europe/Stockholm',     # Sweden
        'NO': 'Europe/Oslo',          # Norway
        'DK': 'Europe/Copenhagen',    # Denmark
        'FI': 'Europe/Helsinki',      # Finland
        'PL': 'Europe/Warsaw',        # Poland
        'CZ': 'Europe/Prague',        # Czech Republic
        'RU': 'Europe/Moscow',        # Russia
        
        # Asia Pacific
        'IN': 'Asia/Kolkata',         # India
        'CN': 'Asia/Shanghai',        # China
        'JP': 'Asia/Tokyo',           # Japan
        'KR': 'Asia/Seoul',           # South Korea
        'SG': 'Asia/Singapore',       # Singapore
        'HK': 'Asia/Hong_Kong',       # Hong Kong
        'TH': 'Asia/Bangkok',         # Thailand
        'MY': 'Asia/Kuala_Lumpur',    # Malaysia
        'PH': 'Asia/Manila',          # Philippines
        'ID': 'Asia/Jakarta',         # Indonesia
        'VN': 'Asia/Ho_Chi_Minh',     # Vietnam
        'AU': 'Australia/Sydney',     # Australia
        'NZ': 'Pacific/Auckland',     # New Zealand
        
        # Middle East & Africa
        'AE': 'Asia/Dubai',           # UAE
        'SA': 'Asia/Riyadh',          # Saudi Arabia
        'IL': 'Asia/Jerusalem',       # Israel
        'TR': 'Europe/Istanbul',      # Turkey
        'EG': 'Africa/Cairo',         # Egypt
        'ZA': 'Africa/Johannesburg',  # South Africa
        'NG': 'Africa/Lagos',         # Nigeria
        'KE': 'Africa/Nairobi',       # Kenya
        
        # Latin America
        'BR': 'America/Sao_Paulo',    # Brazil
        'MX': 'America/Mexico_City',  # Mexico
        'AR': 'America/Argentina/Buenos_Aires',  # Argentina
        'CL': 'America/Santiago',     # Chile
        'CO': 'America/Bogota',       # Colombia
        'PE': 'America/Lima',         # Peru
    }
    
    def get_timezone_from_phone(self, phone_number: str) -> Optional[str]:
        """Smart timezone detection from phone number"""
        try:
            # Parse phone number
            parsed = phonenumbers.parse(phone_number, None)
            country = phonenumbers.region_code_for_number(parsed)
            
            if not country:
                return None
                
            # Handle US with area code intelligence
            if country == 'US':
                area_code = str(parsed.national_number)[:3]
                us_config = self.TIMEZONE_MAP['US']
                
                # Check area code patterns
                for pattern, timezone in us_config['area_codes'].items():
                    if area_code in pattern.split('|'):
                        return timezone
                        
                # Fallback to default US timezone
                return us_config['default']
            
            # Handle other countries
            return self.TIMEZONE_MAP.get(country)
            
        except Exception as e:
            print(f"❌ Timezone detection error for {phone_number}: {e}")
            return None
    
    def get_scheduled_greeting(self, phone_number: str, scheduled_datetime: Union[datetime, str], 
                             partner_name: str = "", contact_name: str = "") -> Dict[str, str]:
        """
        Generate timezone-aware greeting based on scheduled call time
        
        Args:
            phone_number: Recipient's phone number
            scheduled_datetime: When the call is scheduled (datetime object or ISO string)
            partner_name: Name of the institution
            contact_name: Name of the contact person
            
        Returns:
            Dict with greeting info and context
        """
        try:
            # Convert string to datetime if needed
            if isinstance(scheduled_datetime, str):
                scheduled_datetime = datetime.fromisoformat(scheduled_datetime.replace('Z', '+00:00'))
            
            # Get recipient's timezone
            timezone_str = self.get_timezone_from_phone(phone_number)
            
            if timezone_str:
                # Convert scheduled time to recipient's timezone
                tz = pytz.timezone(timezone_str)
                if scheduled_datetime.tzinfo is None:
                    scheduled_datetime = pytz.utc.localize(scheduled_datetime)
                
                local_scheduled_time = scheduled_datetime.astimezone(tz)
                hour = local_scheduled_time.hour
                
                # Generate appropriate greeting
                if 5 <= hour < 12:
                    greeting = "Good morning!"
                elif 12 <= hour < 17:
                    greeting = "Good afternoon!"
                elif 17 <= hour < 21:
                    greeting = "Good evening!"
                else:
                    greeting = "Hello!"
                
                # Add context for non-business hours
                context = ""
                if hour < 9:
                    context = "I hope I'm not calling too early."
                elif hour > 17:
                    context = "I hope I'm not calling too late."
                
                return {
                    'greeting': greeting,
                    'context': context,
                    'scheduled_time': local_scheduled_time.strftime('%I:%M %p'),
                    'scheduled_date': local_scheduled_time.strftime('%B %d, %Y'),
                    'timezone': timezone_str,
                    'timezone_name': local_scheduled_time.strftime('%Z'),
                    'is_business_hours': 9 <= hour <= 17,
                    'hour': hour,
                    'full_greeting': self._build_full_greeting(greeting, context, partner_name, contact_name)
                }
            
            # Fallback if timezone detection fails
            return {
                'greeting': "Good day!",
                'context': "",
                'scheduled_time': scheduled_datetime.strftime('%I:%M %p'),
                'scheduled_date': scheduled_datetime.strftime('%B %d, %Y'),
                'timezone': 'UTC',
                'timezone_name': 'UTC',
                'is_business_hours': True,
                'hour': scheduled_datetime.hour,
                'full_greeting': f"Good day! This is Sarah from Learn with Leaders. I'm calling about educational opportunities for {partner_name}.",
                'fallback': True
            }
            
        except Exception as e:
            print(f"❌ Error generating scheduled greeting: {e}")
            return {
                'greeting': "Hello!",
                'context': "",
                'full_greeting': "Hello! This is Sarah from Learn with Leaders.",
                'error': str(e)
            }
    
    def _build_full_greeting(self, greeting: str, context: str, partner_name: str, contact_name: str) -> str:
        """Build complete greeting message"""
        parts = [
            f"{greeting} This is Sarah from Learn with Leaders."
        ]
        
        if context:
            parts.append(context)
        
        if contact_name:
            parts.append(f"I'm calling to speak with {contact_name} about exciting educational opportunities for {partner_name}.")
        else:
            parts.append(f"I'm calling about exciting educational opportunities for {partner_name}.")
        
        parts.append("Could I please speak with the person in charge of your academic programs?")
        
        return " ".join(parts)

# Global instance
smart_greeting_service = SmartTimezoneGreetingService()
