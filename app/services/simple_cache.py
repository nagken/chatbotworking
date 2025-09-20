"""
Simple in-memory cache manager for development
Provides caching functionality without external dependencies
"""

import time
import threading
from typing import Dict, Any, Optional
import logging
from ..config import config

logger = logging.getLogger(__name__)

class SimpleCacheManager:
    def __init__(self, custom_config: Optional[Dict[str, Any]] = None):
        """
        Initialize cache manager with configuration
        
        Args:
            custom_config: Optional custom configuration to override defaults
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        
        # Use custom config or fall back to app config
        if custom_config:
            self.default_ttl = custom_config.get('ttl', 1800)
            self.max_size_mb = custom_config.get('max_size_mb', 100)
            self.cleanup_interval = custom_config.get('cleanup_interval', 300)
        else:
            # Use configuration from config.py
            self.default_ttl = config.CACHE_TTL_SECONDS
            self.max_size_mb = config.CACHE_MAX_SIZE_MB
            self.cleanup_interval = config.CACHE_CLEANUP_INTERVAL
        
        # Start cleanup thread if cache is enabled
        if config.CACHE_ENABLED:
            self._start_cleanup_thread()
            logger.info(f"Cache initialized with TTL: {self.default_ttl}s, Max Size: {self.max_size_mb}MB")
        else:
            logger.info("Cache is disabled in configuration")
    
    def _start_cleanup_thread(self):
        """Start background thread for periodic cleanup"""
        def cleanup_worker():
            while True:
                try:
                    time.sleep(self.cleanup_interval)
                    if config.CACHE_ENABLED:
                        cleared = self.clear_expired()
                        if cleared > 0:
                            logger.debug(f"Cache cleanup cleared {cleared} expired entries")
                except Exception as e:
                    logger.error(f"Cache cleanup error: {e}")
        
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
        logger.debug("Cache cleanup thread started")
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set a value in cache with TTL"""
        if not config.CACHE_ENABLED:
            return False
            
        try:
            ttl = ttl or self.default_ttl
            
            # Check if we're approaching size limit
            current_size_mb = self._estimate_memory_usage()
            if current_size_mb > self.max_size_mb * 0.9:  # 90% threshold
                logger.warning(f"Cache approaching size limit: {current_size_mb}MB / {self.max_size_mb}MB")
                # Clear some expired entries to make room
                self.clear_expired()
            
            with self._lock:
                self._cache[key] = {
                    "value": value,
                    "expires_at": time.time() + ttl,
                    "created_at": time.time(),
                    "access_count": 1
                }
            logger.debug(f"Cached key: {key} with TTL: {ttl}s")
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache if not expired"""
        if not config.CACHE_ENABLED:
            return None
            
        try:
            with self._lock:
                if key in self._cache:
                    cache_entry = self._cache[key]
                    
                    # Check if expired
                    if time.time() > cache_entry["expires_at"]:
                        del self._cache[key]
                        return None
                    
                    # Increment access count
                    cache_entry["access_count"] += 1
                    
                    logger.debug(f"Cache hit for key: {key}")
                    return cache_entry["value"]
                
                logger.debug(f"Cache miss for key: {key}")
                return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    def is_enabled(self) -> bool:
        """Check if cache is enabled"""
        return config.CACHE_ENABLED
    
    def get_config(self) -> Dict[str, Any]:
        """Get current cache configuration"""
        return {
            "enabled": config.CACHE_ENABLED,
            "ttl_seconds": self.default_ttl,
            "max_size_mb": self.max_size_mb,
            "cleanup_interval": self.cleanup_interval
        }
    
    def delete(self, key: str) -> bool:
        """Delete a key from cache"""
        try:
            with self._lock:
                if key in self._cache:
                    del self._cache[key]
                    return True
                return False
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    def clear_expired(self) -> int:
        """Clear expired entries and return count cleared"""
        try:
            current_time = time.time()
            expired_keys = []
            
            with self._lock:
                for key, entry in self._cache.items():
                    if current_time > entry["expires_at"]:
                        expired_keys.append(key)
                
                for key in expired_keys:
                    del self._cache[key]
            
            logger.info(f"Cleared {len(expired_keys)} expired cache entries")
            return len(expired_keys)
        except Exception as e:
            logger.error(f"Cache cleanup error: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            with self._lock:
                current_time = time.time()
                total_entries = len(self._cache)
                expired_entries = sum(
                    1 for entry in self._cache.values() 
                    if current_time > entry["expires_at"]
                )
                active_entries = total_entries - expired_entries
                
                return {
                    "total_entries": total_entries,
                    "active_entries": active_entries,
                    "expired_entries": expired_entries,
                    "cache_size_mb": self._estimate_memory_usage()
                }
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {}
    
    def _estimate_memory_usage(self) -> float:
        """Estimate memory usage in MB"""
        try:
            import sys
            total_size = 0
            for key, entry in self._cache.items():
                total_size += sys.getsizeof(key)
                total_size += sys.getsizeof(entry)
            return round(total_size / (1024 * 1024), 2)
        except:
            return 0.0
    
    def clear_all(self) -> int:
        """Clear all cache entries and return count cleared"""
        try:
            with self._lock:
                count = len(self._cache)
                self._cache.clear()
                logger.info(f"Cleared all {count} cache entries")
                return count
        except Exception as e:
            logger.error(f"Cache clear all error: {e}")
            return 0
