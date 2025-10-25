from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pytz
from app.database.connection import db_queries
import logging

logger = logging.getLogger(__name__)

class CalendarUtils:
    """Utility class for calendar and scheduling operations"""
    
    def __init__(self):
        self.timezone = pytz.timezone('Asia/Kolkata')  # Indian timezone
        self.business_hours_start = 9  # 9 AM
        self.business_hours_end = 17   # 5 PM
        self.business_days = [0, 1, 2, 3, 4]  # Monday to Friday
    
    def get_next_available_slots(self, count: int = 5) -> List[Dict[str, Any]]:
        """
        Get the next available calendar slots
        
        Args:
            count: Number of slots to return
            
        Returns:
            List of available slot dictionaries
        """
        try:
            slots = db_queries.get_available_slots(limit=count)
            return [self._format_slot_for_display(slot) for slot in slots]
        except Exception as e:
            logger.error(f"Failed to get available slots: {e}")
            return []
    
    def is_slot_available(self, slot_datetime: datetime) -> bool:
        """
        Check if a specific time slot is available
        
        Args:
            slot_datetime: The datetime to check
            
        Returns:
            Boolean indicating availability
        """
        try:
            return db_queries.is_slot_open(slot_datetime.isoformat())
        except Exception as e:
            logger.error(f"Failed to check slot availability: {e}")
            return False
    
    def generate_business_hours_slots(self, start_date: datetime, days: int = 7) -> List[datetime]:
        """
        Generate time slots during business hours
        
        Args:
            start_date: Starting date for slot generation
            days: Number of days to generate slots for
            
        Returns:
            List of datetime objects for available slots
        """
        slots = []
        current_date = start_date.replace(hour=self.business_hours_start, minute=0, second=0, microsecond=0)
        
        for day in range(days):
            date = current_date + timedelta(days=day)
            
            # Skip weekends
            if date.weekday() not in self.business_days:
                continue
            
            # Generate hourly slots during business hours
            for hour in range(self.business_hours_start, self.business_hours_end):
                slot_time = date.replace(hour=hour)
                
                # Add both :00 and :30 minute slots
                slots.append(slot_time)
                slots.append(slot_time.replace(minute=30))
        
        return slots
    
    def format_datetime_for_display(self, dt: datetime) -> Dict[str, str]:
        """
        Format datetime for user-friendly display
        
        Args:
            dt: Datetime object to format
            
        Returns:
            Dictionary with formatted date and time strings
        """
        if not dt:
            return {'date': 'TBD', 'time': 'TBD', 'day': 'TBD'}
        
        # Ensure datetime is timezone-aware
        if dt.tzinfo is None:
            dt = self.timezone.localize(dt)
        
        return {
            'date': dt.strftime('%d/%m/%Y'),
            'time': dt.strftime('%I:%M %p'),
            'day': dt.strftime('%A'),
            'full': dt.strftime('%A, %d/%m/%Y at %I:%M %p')
        }
    
    def parse_datetime_string(self, date_str: str) -> Optional[datetime]:
        """
        Parse datetime string in various formats
        
        Args:
            date_str: Date string to parse
            
        Returns:
            Parsed datetime object or None if parsing fails
        """
        formats = [
            '%d/%m/%Y %I:%M %p',
            '%d/%m/%Y %H:%M',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return self.timezone.localize(dt)
            except ValueError:
                continue
        
        logger.warning(f"Failed to parse datetime string: {date_str}")
        return None
    
    def get_next_business_day(self, from_date: datetime = None) -> datetime:
        """
        Get the next business day
        
        Args:
            from_date: Starting date (default: today)
            
        Returns:
            Next business day datetime
        """
        if not from_date:
            from_date = datetime.now(self.timezone)
        
        next_day = from_date + timedelta(days=1)
        
        # Find next business day
        while next_day.weekday() not in self.business_days:
            next_day += timedelta(days=1)
        
        # Set to business hours start
        return next_day.replace(
            hour=self.business_hours_start, 
            minute=0, 
            second=0, 
            microsecond=0
        )
    
    def is_business_hours(self, dt: datetime) -> bool:
        """
        Check if datetime falls within business hours
        
        Args:
            dt: Datetime to check
            
        Returns:
            Boolean indicating if it's business hours
        """
        if dt.weekday() not in self.business_days:
            return False
        
        return self.business_hours_start <= dt.hour < self.business_hours_end
    
    def get_reschedule_options(self, preferred_datetime: datetime = None, count: int = 3) -> List[Dict[str, Any]]:
        """
        Get reschedule options for a call
        
        Args:
            preferred_datetime: Preferred reschedule datetime
            count: Number of options to return
            
        Returns:
            List of reschedule option dictionaries
        """
        options = []
        
        # If preferred datetime is provided and available, include it first
        if preferred_datetime and self.is_slot_available(preferred_datetime):
            options.append({
                'datetime': preferred_datetime,
                'display': self.format_datetime_for_display(preferred_datetime),
                'is_preferred': True
            })
            count -= 1
        
        # Get additional available slots
        available_slots = self.get_next_available_slots(count)
        
        for slot in available_slots:
            if len(options) >= count + (1 if preferred_datetime else 0):
                break
                
            slot_dt = slot.get('slot_datetime')
            if slot_dt and (not preferred_datetime or slot_dt != preferred_datetime):
                options.append({
                    'datetime': slot_dt,
                    'display': self.format_datetime_for_display(slot_dt),
                    'is_preferred': False
                })
        
        return options[:count + (1 if preferred_datetime else 0)]
    
    def _format_slot_for_display(self, slot: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format a database slot record for display
        
        Args:
            slot: Database slot record
            
        Returns:
            Formatted slot dictionary
        """
        slot_datetime = slot.get('slot_datetime')
        formatted_display = self.format_datetime_for_display(slot_datetime)
        
        return {
            'slot_datetime': slot_datetime,
            'duration_minutes': slot.get('slot_duration_minutes', 30),
            'notes': slot.get('notes', ''),
            'display': formatted_display,
            'is_available': True
        }
    
    def calculate_call_duration(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """
        Calculate call duration and provide formatted output
        
        Args:
            start_time: Call start datetime
            end_time: Call end datetime
            
        Returns:
            Dictionary with duration information
        """
        if not start_time or not end_time:
            return {'seconds': 0, 'minutes': 0, 'formatted': '0 minutes'}
        
        duration = end_time - start_time
        total_seconds = int(duration.total_seconds())
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        
        if minutes > 0:
            formatted = f"{minutes} minute{'s' if minutes != 1 else ''}"
            if seconds > 0:
                formatted += f" {seconds} second{'s' if seconds != 1 else ''}"
        else:
            formatted = f"{seconds} second{'s' if seconds != 1 else ''}"
        
        return {
            'seconds': total_seconds,
            'minutes': minutes,
            'formatted': formatted,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat()
        }
