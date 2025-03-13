#!/usr/bin/env python3
"""
Cache diagnostics script for debugging the Particle-Graph caching system.
"""

import os
import sys
import json
from pathlib import Path

# Add the parent directory to the path to make imports work locally
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.particle.particle_support import logger, particle_cache
from src.core.cache_manager import cache_manager
from src.core.path_resolver import PathResolver

def inspect_cache_directories():
    """Check and report on cache directories."""
    print("\n=== Cache Directory Information ===")
    
    # Check PROJECT_ROOT 
    print(f"PROJECT_ROOT path: {PathResolver.PROJECT_ROOT}")
    print(f"PROJECT_ROOT exists: {PathResolver.PROJECT_ROOT.exists()}")
    print(f"PROJECT_ROOT is directory: {PathResolver.PROJECT_ROOT.is_dir() if PathResolver.PROJECT_ROOT.exists() else 'N/A'}")
    
    # Check CACHE_DIR
    print(f"\nCACHE_DIR path: {PathResolver.CACHE_DIR}")
    print(f"CACHE_DIR exists: {PathResolver.CACHE_DIR.exists()}")
    print(f"CACHE_DIR is directory: {PathResolver.CACHE_DIR.is_dir() if PathResolver.CACHE_DIR.exists() else 'N/A'}")
    
    if PathResolver.CACHE_DIR.exists() and PathResolver.CACHE_DIR.is_dir():
        print("\n--- Cache directory contents ---")
        for item in PathResolver.CACHE_DIR.iterdir():
            print(f"  {item.name} - {'dir' if item.is_dir() else 'file'} - {item.stat().st_size} bytes")
            if item.is_file() and item.name.endswith('.json'):
                try:
                    with open(item, 'r') as f:
                        data = json.load(f)
                        if isinstance(data, dict):
                            if "last_crawled" in data:
                                print(f"    Contains 'last_crawled': {data['last_crawled']}")
                            else:
                                print(f"    No 'last_crawled' key")
                except Exception as e:
                    print(f"    Error reading file: {e}")

def inspect_old_cache():
    """Check the old particle_cache from particle_utils."""
    print("\n=== Old Particle Cache (particle_utils.particle_cache) ===")
    print(f"Number of entries: {len(particle_cache)}")
    for k, v in particle_cache.items():
        print(f"  Key: {k}")
        if isinstance(v, dict) and "last_crawled" in v:
            print(f"    last_crawled: {v['last_crawled']}")

def inspect_cache_manager():
    """Test and report on cache_manager functionality."""
    print("\n=== Cache Manager Information ===")
    
    # Check keys
    keys = cache_manager.keys()
    print(f"cache_manager.keys(): {keys}")
    
    # Try to get each key
    for key in keys:
        value, found = cache_manager.get(key)
        print(f"\nKey: {key}")
        print(f"  Found: {found}")
        if found:
            print(f"  Type: {type(value)}")
            if isinstance(value, dict):
                print(f"  Keys: {list(value.keys())[:5]}..." if len(value.keys()) > 5 else f"  Keys: {list(value.keys())}")
                if "last_crawled" in value:
                    print(f"  last_crawled: {value['last_crawled']}")
            else:
                print(f"  Value: {value}")

def main():
    print("=== Particle-Graph Cache Diagnostics ===")
    print(f"Current working directory: {os.getcwd()}")
    
    try:
        inspect_cache_directories()
    except Exception as e:
        print(f"Error inspecting cache directories: {e}")
    
    try:
        inspect_old_cache()
    except Exception as e:
        print(f"Error inspecting old cache: {e}")
    
    try:
        inspect_cache_manager()
    except Exception as e:
        print(f"Error inspecting cache manager: {e}")
    
    # Try list_graph function
    try:
        from src.api.list_graph import listGraph
        print("\n=== Testing listGraph function ===")
        result = listGraph()
        print(f"listGraph result: {result}")
    except Exception as e:
        print(f"Error testing listGraph: {e}")

if __name__ == "__main__":
    main()
