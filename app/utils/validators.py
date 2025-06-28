import re
from datetime import datetime

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_datetime(dt: datetime) -> bool:
    """Validate that datetime is in the future"""
    return dt > datetime.now()

def validate_duration(duration: int) -> bool:
    """Validate meeting duration (between 15 minutes and 8 hours)"""
    return 15 <= duration <= 480

def sanitize_event_title(title: str) -> str:
    """Sanitize event title"""
    # Remove potentially harmful characters
    sanitized = re.sub(r'[<>"\']', '', title)
    return sanitized.strip()[:100]  