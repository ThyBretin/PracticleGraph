import json
import os
import time
import threading
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List, Set, Union

from src.particle.particle_support import logger
from src.core.path_resolver import PathResolver

class CacheManager:
    """
    Centralized cache management system for Particle Graph.
    
    Handles both in-memory caching and persistent file-based caching with:
    - Cache invalidation strategies
    - Thread-safe operations
    - Automatic persistence
    - Cache statistics and monitoring
    """
    
    def __init__(self):
        """Initialize the cache manager."""
        self._memory_cache: Dict[str, Any] = {}
        self._cache_metadata: Dict[str, Dict[str, Any]] = {}
        self._last_persist_time: float = 0
        self._persist_interval: float = 300  # 5 minutes
        self._lock = threading.RLock()  # Reentrant lock for thread safety
        self.load_from_disk()
    
    def get(self, key: str) -> Tuple[Any, bool]:
        """
        Get a value from the cache.
        
        Args:
            key: The cache key
            
        Returns:
            Tuple of (value, found) where found is a boolean indicating if the key was in the cache
        """
        with self._lock:
            if key in self._memory_cache:
                self._update_access_metadata(key)
                return self._memory_cache[key], True
            
            # Try to load from file if not in memory
            file_path = PathResolver.get_graph_path(key)
            data, error = PathResolver.read_json_file(file_path)
            
            if error:
                return None, False
                
            # Update in-memory cache
            self._memory_cache[key] = data
            self._update_access_metadata(key, is_load=True)
            return data, True
    
    def set(self, key: str, value: Any, persist: bool = True) -> None:
        """
        Set a value in the cache.
        
        Args:
            key: The cache key
            value: The value to cache
            persist: Whether to also persist to disk immediately
        """
        with self._lock:
            self._memory_cache[key] = value
            self._update_access_metadata(key, is_write=True)
            
            if persist:
                self._persist_key(key)
            elif time.time() - self._last_persist_time > self._persist_interval:
                self.persist_all()
    
    def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.
        
        Args:
            key: The cache key to delete
            
        Returns:
            True if the key was found and deleted, False otherwise
        """
        with self._lock:
            if key in self._memory_cache:
                del self._memory_cache[key]
                if key in self._cache_metadata:
                    del self._cache_metadata[key]
                
                # Delete from disk
                file_path = PathResolver.get_graph_path(key)
                try:
                    if file_path.exists():
                        file_path.unlink()
                    return True
                except Exception as e:
                    logger.error(f"Error deleting cache file {file_path}: {e}")
            
            return False
    
    def has_key(self, key: str) -> bool:
        """Check if a key exists in the cache."""
        with self._lock:
            if key in self._memory_cache:
                return True
            
            # Check on disk
            file_path = PathResolver.get_graph_path(key)
            return file_path.exists()
    
    def keys(self) -> List[str]:
        """Get a list of all keys in the cache."""
        with self._lock:
            # Combine memory keys with disk keys
            disk_keys = self._get_disk_keys()
            return list(set(list(self._memory_cache.keys()) + disk_keys))
    
    def _get_disk_keys(self) -> List[str]:
        """Get a list of all keys stored on disk."""
        try:
            cache_dir = PathResolver.CACHE_DIR
            if not cache_dir.exists():
                return []
                
            keys = []
            for file_path in cache_dir.glob("*_graph.json"):
                key = file_path.name.replace("_graph.json", "")
                keys.append(key)
            return keys
        except Exception as e:
            logger.error(f"Error listing cache directory: {e}")
            return []
    
    def _update_access_metadata(self, key: str, is_write: bool = False, is_load: bool = False) -> None:
        """Update metadata for a key access."""
        now = time.time()
        if key not in self._cache_metadata:
            self._cache_metadata[key] = {
                "created_at": now,
                "access_count": 0,
                "last_accessed": now,
                "last_modified": now if is_write else None
            }
        
        metadata = self._cache_metadata[key]
        metadata["access_count"] += 1
        metadata["last_accessed"] = now
        
        if is_write:
            metadata["last_modified"] = now
        
        if is_load:
            metadata["loaded_from_disk"] = True
    
    def _persist_key(self, key: str) -> None:
        """Persist a single key to disk."""
        if key not in self._memory_cache:
            return
            
        value = self._memory_cache[key]
        file_path = PathResolver.get_graph_path(key)
        error = PathResolver.write_json_file(file_path, value)
        
        if error:
            logger.error(f"Error persisting cache key {key}: {error}")
    
    def persist_all(self) -> None:
        """Persist all in-memory cache to disk."""
        with self._lock:
            for key in self._memory_cache:
                self._persist_key(key)
            self._last_persist_time = time.time()
    
    def load_from_disk(self) -> None:
        """Load all cache files from disk into memory."""
        with self._lock:
            disk_keys = self._get_disk_keys()
            for key in disk_keys:
                if key not in self._memory_cache:
                    # Only load if not already in memory
                    self.get(key)
    
    def clear_all(self) -> None:
        """Clear all cached data both in memory and on disk."""
        with self._lock:
            self._memory_cache.clear()
            self._cache_metadata.clear()
            
            # Delete all files in cache directory
            try:
                cache_dir = PathResolver.CACHE_DIR
                if cache_dir.exists():
                    for file_path in cache_dir.glob("*.json"):
                        file_path.unlink()
            except Exception as e:
                logger.error(f"Error clearing cache directory: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the cache."""
        with self._lock:
            memory_size = len(self._memory_cache)
            disk_size = len(self._get_disk_keys())
            
            return {
                "memory_keys": memory_size,
                "disk_keys": disk_size,
                "total_keys": len(self.keys()),
                "metadata": self._cache_metadata
            }
    
    def invalidate_old(self, max_age_seconds: int = 86400) -> int:
        """
        Invalidate cache entries older than the specified age.
        
        Args:
            max_age_seconds: Maximum age in seconds (default: 24 hours)
            
        Returns:
            Number of invalidated entries
        """
        with self._lock:
            now = time.time()
            invalidated = 0
            
            for key, metadata in list(self._cache_metadata.items()):
                if now - metadata["last_accessed"] > max_age_seconds:
                    if self.delete(key):
                        invalidated += 1
            
            return invalidated
    
    def refresh_key(self, key: str) -> bool:
        """
        Refresh a key by reloading it from disk.
        
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            if key in self._memory_cache:
                del self._memory_cache[key]
            
            _, found = self.get(key)
            return found

# Global cache manager instance
cache_manager = CacheManager()
