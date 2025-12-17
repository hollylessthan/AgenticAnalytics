"""
Data Cache Manager for AgenticAnalytics

Provides safe caching mechanisms with size limits, TTL, and automatic sampling
for large datasets to prevent memory issues.
"""

import sys
import time
from typing import Any, Optional, Tuple
import pandas as pd
from datetime import datetime, timedelta

from src.config import Config


class CacheEntry:
    """Represents a cached data entry with metadata."""
    
    def __init__(self, data: Any, sql_query: str, config: Config):
        """Initialize cache entry.
        
        Args:
            data: Data to cache (DataFrame, list, etc.)
            sql_query: SQL query that generated this data
            config: Configuration with cache settings
        """
        self.data = data
        self.sql_query = sql_query
        self.timestamp = datetime.now()
        self.config = config
        
        # Calculate metadata
        self.row_count = len(data) if hasattr(data, '__len__') else 0
        self.size_mb = self._calculate_size_mb(data)
        self.is_sampled = False
        self.original_row_count = self.row_count
    
    def _calculate_size_mb(self, data: Any) -> float:
        """Calculate approximate size in MB."""
        try:
            if isinstance(data, pd.DataFrame):
                # More accurate size for DataFrame
                return data.memory_usage(deep=True).sum() / (1024 * 1024)
            else:
                # Rough estimate using sys.getsizeof
                return sys.getsizeof(data) / (1024 * 1024)
        except Exception:
            return 0.0
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired based on TTL."""
        if self.config.cache_ttl_seconds <= 0:
            return False  # No expiration
        
        expiry_time = self.timestamp + timedelta(seconds=self.config.cache_ttl_seconds)
        return datetime.now() > expiry_time
    
    def is_too_large(self) -> bool:
        """Check if cache entry exceeds size limits."""
        if self.row_count > self.config.max_cache_rows:
            return True
        if self.size_mb > self.config.max_cache_size_mb:
            return True
        return False


class DataCacheManager:
    """Manages data caching with safety mechanisms."""
    
    def __init__(self, config: Config = None):
        """Initialize cache manager.
        
        Args:
            config: Configuration object (creates default if None)
        """
        self.config = config or Config()
        self.cache_entry: Optional[CacheEntry] = None
    
    def _calculate_size_mb(self, data: Any) -> float:
        """Calculate approximate size in MB."""
        try:
            if isinstance(data, pd.DataFrame):
                return data.memory_usage(deep=True).sum() / (1024 * 1024)
            else:
                return sys.getsizeof(data) / (1024 * 1024)
        except Exception:
            return 0.0
    
    def should_cache(self, data: Any) -> Tuple[bool, str]:
        """Determine if data should be cached.
        
        Args:
            data: Data to potentially cache
            
        Returns:
            Tuple of (should_cache: bool, reason: str)
        """
        if not self.config.enable_data_cache:
            return False, "Caching disabled in config"
        
        if data is None:
            return False, "Data is None"
        
        # Check size
        try:
            if isinstance(data, pd.DataFrame):
                row_count = len(data)
                size_mb = data.memory_usage(deep=True).sum() / (1024 * 1024)
            else:
                row_count = len(data) if hasattr(data, '__len__') else 0
                size_mb = sys.getsizeof(data) / (1024 * 1024)
            
            # Too many rows?
            if row_count > self.config.max_cache_rows:
                if self.config.auto_sample_large_results:
                    return True, f"Will cache sampled data ({self.config.sample_size} rows)"
                else:
                    return False, f"Too many rows ({row_count} > {self.config.max_cache_rows})"
            
            # Too large in memory?
            if size_mb > self.config.max_cache_size_mb:
                if self.config.auto_sample_large_results:
                    return True, f"Will cache sampled data (size: {size_mb:.1f}MB)"
                else:
                    return False, f"Too large ({size_mb:.1f}MB > {self.config.max_cache_size_mb}MB)"
            
            return True, f"Safe to cache ({row_count} rows, {size_mb:.1f}MB)"
            
        except Exception as e:
            return False, f"Error checking size: {e}"
    
    def cache_data(self, data: Any, sql_query: str) -> Tuple[Any, str]:
        """Cache data with automatic sampling if needed.
        
        Args:
            data: Data to cache
            sql_query: SQL query that generated the data
            
        Returns:
            Tuple of (cached_data, status_message)
        """
        should_cache, reason = self.should_cache(data)
        
        if not should_cache:
            self.cache_entry = None
            return None, f"Not cached: {reason}"
        
        # Check if we need to sample
        cached_data = data
        status_msg = reason
        
        if isinstance(data, pd.DataFrame):
            row_count = len(data)
            size_mb = data.memory_usage(deep=True).sum() / (1024 * 1024)
            
            # Sample if too large
            if (row_count > self.config.max_cache_rows or 
                size_mb > self.config.max_cache_size_mb):
                
                if self.config.auto_sample_large_results:
                    sample_size = min(self.config.sample_size, row_count)
                    cached_data = data.sample(n=sample_size, random_state=42)
                    
                    # Create cache entry with sampling info
                    self.cache_entry = CacheEntry(cached_data, sql_query, self.config)
                    self.cache_entry.is_sampled = True
                    self.cache_entry.original_row_count = row_count
                    
                    status_msg = (f"Cached SAMPLED data: {sample_size}/{row_count} rows "
                                f"({self.cache_entry.size_mb:.1f}MB). "
                                f"Original too large ({size_mb:.1f}MB)")
                else:
                    self.cache_entry = None
                    return None, f"Not cached: Data too large and auto-sampling disabled"
            else:
                # Data is safe to cache as-is
                self.cache_entry = CacheEntry(cached_data, sql_query, self.config)
                status_msg = f"Cached full data: {row_count} rows ({size_mb:.1f}MB)"
        else:
            # Non-DataFrame data
            self.cache_entry = CacheEntry(cached_data, sql_query, self.config)
            status_msg = f"Cached data: {self.cache_entry.size_mb:.1f}MB"
        
        return cached_data, status_msg
    
    def get_cached_data(self) -> Optional[Any]:
        """Retrieve cached data if available and valid.
        
        Returns:
            Cached data or None if not available/expired
        """
        if not self.config.enable_data_cache:
            return None
        
        if self.cache_entry is None:
            return None
        
        # Check expiration
        if self.cache_entry.is_expired():
            self.clear_cache()
            return None
        
        return self.cache_entry.data
    
    def clear_cache(self):
        """Clear cached data."""
        if self.cache_entry is not None:
            # Help garbage collector
            self.cache_entry.data = None
            self.cache_entry = None
    
    def get_cache_info(self) -> dict:
        """Get information about current cache status.
        
        Returns:
            Dictionary with cache statistics
        """
        if self.cache_entry is None:
            return {
                'has_cache': False,
                'enabled': self.config.enable_data_cache
            }
        
        age_seconds = (datetime.now() - self.cache_entry.timestamp).total_seconds()
        ttl_remaining = max(0, self.config.cache_ttl_seconds - age_seconds)
        
        return {
            'has_cache': True,
            'enabled': self.config.enable_data_cache,
            'row_count': self.cache_entry.row_count,
            'size_mb': round(self.cache_entry.size_mb, 3),
            'is_sampled': self.cache_entry.is_sampled,
            'original_row_count': self.cache_entry.original_row_count,
            'age': round(age_seconds, 2),
            'ttl_remaining': round(ttl_remaining, 2),
            'is_expired': self.cache_entry.is_expired(),
            'sql_query': self.cache_entry.sql_query[:100] + '...' if len(self.cache_entry.sql_query) > 100 else self.cache_entry.sql_query
        }
    
    def get_memory_usage_mb(self) -> float:
        """Get approximate memory usage of cache in MB."""
        if self.cache_entry is None:
            return 0.0
        return self.cache_entry.size_mb


# Global cache manager instance
_global_cache_manager = None

def get_cache_manager(config: Config = None) -> DataCacheManager:
    """Get or create global cache manager instance.
    
    Args:
        config: Configuration object
        
    Returns:
        DataCacheManager instance
    """
    global _global_cache_manager
    if _global_cache_manager is None:
        _global_cache_manager = DataCacheManager(config)
    return _global_cache_manager
