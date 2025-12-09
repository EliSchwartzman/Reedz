from datetime import datetime, timezone  # UTC timezone and datetime operations
from zoneinfo import ZoneInfo           # IANA timezone database (Python 3.9+)
# test


# Eastern Timezone (handles EDT/EST automatically)
ET_ZONE = ZoneInfo("America/New_York")


def utc_to_eastern(utc_dt: datetime | None) -> datetime | None:
    """
    Converts UTC datetime to Eastern Time (EDT/EST).
    
    Args:
        utc_dt (datetime | None): UTC timestamp or None
    
    Returns:
        datetime | None: Eastern timezone equivalent or None
    """
    if utc_dt is None:
        return None
    
    # Ensure input has UTC timezone info
    if utc_dt.tzinfo is None:
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
    
    # Convert to Eastern timezone (handles DST automatically)
    return utc_dt.astimezone(ET_ZONE)


def format_et(dt_val):
    """
    Formats any datetime/string/None to human-readable Eastern Time string.
    
    Supported formats:
    * datetime objects (naive → UTC → ET)
    * ISO strings ("2025-01-01T12:00:00")
    * None → empty string
    
    Args:
        dt_val: datetime, ISO string, or None
    
    Returns:
        str: "2025-01-01 12:00 PM ET" or original value if unparseable
    """
    if dt_val is None:
        return ""  # Empty string for null dates
    
    # Handle ISO string input from database
    if isinstance(dt_val, str):
        try:
            dt = datetime.fromisoformat(dt_val)
        except ValueError:
            return str(dt_val)  # Return original if unparseable
    else:
        dt = dt_val  # Already a datetime object
    
    # Ensure UTC timezone for conversion
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    # Convert to Eastern and format
    edt = dt.astimezone(ET_ZONE)
    return edt.strftime("%Y-%m-%d %I:%M %p ET")  # "2025-01-01 07:00 PM ET"