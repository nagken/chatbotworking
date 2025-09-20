"""
DateTime utilities for consistent timezone handling across the application
Prevents timezone mixing bugs by providing standardized datetime functions
"""

from datetime import datetime, timedelta, timezone
from typing import Optional


def utc_now() -> datetime:
    """
    Get current UTC datetime with timezone info
    
    Returns:
        timezone-aware datetime object in UTC
        
    Note:
        Use this instead of datetime.now() or datetime.utcnow() to prevent
        timezone mixing bugs when working with database timestamps
    """
    return datetime.now(timezone.utc)


def utc_from_timestamp(timestamp: float) -> datetime:
    """
    Convert Unix timestamp to timezone-aware UTC datetime
    
    Args:
        timestamp: Unix timestamp (seconds since epoch)
        
    Returns:
        timezone-aware datetime object in UTC
    """
    return datetime.fromtimestamp(timestamp, tz=timezone.utc)


def utc_plus_timedelta(delta: timedelta) -> datetime:
    """
    Get UTC datetime with added timedelta
    
    Args:
        delta: Time delta to add to current UTC time
        
    Returns:
        timezone-aware datetime object in UTC
        
    Example:
        # Get time 30 days from now
        future_time = utc_plus_timedelta(timedelta(days=30))
    """
    return utc_now() + delta


def utc_minus_timedelta(delta: timedelta) -> datetime:
    """
    Get UTC datetime with subtracted timedelta
    
    Args:
        delta: Time delta to subtract from current UTC time
        
    Returns:
        timezone-aware datetime object in UTC
        
    Example:
        # Get time 1 hour ago
        past_time = utc_minus_timedelta(timedelta(hours=1))
    """
    return utc_now() - delta


def is_expired(expires_at: datetime, now: Optional[datetime] = None) -> bool:
    """
    Check if a datetime has expired
    
    Args:
        expires_at: The expiration datetime to check
        now: Current time (defaults to utc_now())
        
    Returns:
        True if expired, False otherwise
        
    Example:
        if is_expired(session.expires_at):
            print("Session has expired")
    """
    if now is None:
        now = utc_now()
    
    # Handle timezone-naive expires_at by assuming UTC
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    
    return now >= expires_at


def seconds_until_expiry(expires_at: datetime, now: Optional[datetime] = None) -> int:
    """
    Get seconds until expiration (can be negative if already expired)
    
    Args:
        expires_at: The expiration datetime
        now: Current time (defaults to utc_now())
        
    Returns:
        Number of seconds until expiry (negative if expired)
    """
    if now is None:
        now = utc_now()
    
    # Handle timezone-naive expires_at by assuming UTC
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    
    return int((expires_at - now).total_seconds())


def format_iso_utc(dt: datetime) -> str:
    """
    Format datetime as ISO string in UTC
    
    Args:
        dt: datetime to format
        
    Returns:
        ISO formatted string in UTC
        
    Example:
        iso_string = format_iso_utc(utc_now())
        # Returns: "2024-01-15T14:30:45.123456+00:00"
    """
    if dt.tzinfo is None:
        # Assume UTC if timezone-naive
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        # Convert to UTC if not already
        dt = dt.astimezone(timezone.utc)
    
    return dt.isoformat()
