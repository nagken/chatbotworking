"""
Global cache manager for the application
Provides a centralized cache instance and utility functions
"""

from .simple_cache import SimpleCacheManager
from ..config import config
import logging
import time

logger = logging.getLogger(__name__)

# Global cache instance
_cache_instance: SimpleCacheManager = None

def get_cache() -> SimpleCacheManager:
    """
    Get the global cache instance
    
    Returns:
        SimpleCacheManager instance
    """
    global _cache_instance
    
    if _cache_instance is None:
        _cache_instance = SimpleCacheManager()
        logger.info("Global cache instance initialized")
    
    return _cache_instance

def clear_cache() -> int:
    """
    Clear all cache entries
    
    Returns:
        Number of entries cleared
    """
    cache = get_cache()
    return cache.clear_all()

def get_cache_stats() -> dict:
    """
    Get cache statistics
    
    Returns:
        Dictionary with cache statistics
    """
    cache = get_cache()
    stats = cache.get_stats()
    config_info = cache.get_config()
    
    return {
        **stats,
        "config": config_info
    }

def cache_key(prefix: str, *args) -> str:
    """
    Generate a consistent cache key
    
    Args:
        prefix: Key prefix
        *args: Additional key components
        
    Returns:
        Formatted cache key string
    """
    key_parts = [prefix]
    key_parts.extend(str(arg) for arg in args)
    return ":".join(key_parts)

# Example usage functions
def cache_message_result(message_id: str, result_data: dict, ttl: int = None) -> bool:
    """
    Cache a message execution result
    
    Args:
        message_id: Message UUID
        result_data: Result data to cache
        ttl: Optional custom TTL
        
    Returns:
        True if cached successfully
    """
    cache = get_cache()
    key = cache_key("message_result", message_id)
    return cache.set(key, result_data, ttl)

def get_cached_message_result(message_id: str) -> dict:
    """
    Get cached message execution result
    
    Args:
        message_id: Message UUID
        
    Returns:
        Cached result data or None
    """
    cache = get_cache()
    key = cache_key("message_result", message_id)
    return cache.get(key)

def cache_chart_data(chart_id: str, chart_data: dict, ttl: int = None) -> bool:
    """
    Cache chart data for re-rendering
    
    Args:
        chart_id: Chart identifier
        chart_data: Chart data to cache
        ttl: Optional custom TTL
        
    Returns:
        True if cached successfully
    """
    cache = get_cache()
    key = cache_key("chart_data", chart_id)
    return cache.set(key, chart_data, ttl)

def get_cached_chart_data(chart_id: str) -> dict:
    """
    Get cached chart data
    
    Args:
        chart_id: Chart identifier
        
    Returns:
        Cached chart data or None
    """
    cache = get_cache()
    key = cache_key("chart_data", chart_id)
    return cache.get(key)


def cache_chart_reexecution_result(
    message_id: str, 
    chart_config: dict, 
    execution_result: dict, 
    ttl: int = None
) -> bool:
    """
    Cache chart re-execution result for a specific message
    
    Args:
        message_id: Message UUID
        chart_config: Chart configuration used for re-execution
        execution_result: Result of the re-execution (data, chart, etc.)
        ttl: Optional custom TTL
        
    Returns:
        True if cached successfully
    """
    cache = get_cache()
    key = cache_key("chart_reexecution", message_id)
    
    cache_data = {
        "chart_config": chart_config,
        "execution_result": execution_result,
        "cached_at": time.time(),
        "message_id": message_id
    }
    
    return cache.set(key, cache_data, ttl)


def get_cached_chart_reexecution_result(message_id: str) -> dict:
    """
    Get cached chart re-execution result for a specific message
    
    Args:
        message_id: Message UUID
        
    Returns:
        Cached re-execution result or None
    """
    cache = get_cache()
    key = cache_key("chart_reexecution", message_id)
    return cache.get(key)
