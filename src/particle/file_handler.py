from typing import Tuple, Optional, Dict, Any
from pathlib import Path
from src.core.path_resolver import PathResolver
from src.particle.particle_support import logger
import json

def read_file(file_path: str) -> Tuple[Optional[str], Optional[str]]:
    """Read file content, return (content, error)."""
    try:
        full_path = PathResolver.resolve_path(file_path)
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        logger.debug(f"Read content from {full_path}, length: {len(content)}")
        return content, None
    except Exception as e:
        logger.error(f"Error reading {file_path}: {str(e)}")
        return None, f"Read error: {str(e)}"

def write_particle(file_path: str, context: dict) -> Tuple[Optional[str], Optional[str]]:
    """Write Particle data to cache as JSON, return (cache_path, error)."""
    try:
        # Resolve particle cache path
        particle_path = PathResolver.get_particle_path(file_path)
        logger.debug(f"Writing particle to {particle_path}")
        
        # Remove empty arrays from context
        filtered_context = {k: v for k, v in context.items() if not (isinstance(v, list) and len(v) == 0)}
        logger.debug(f"Filtered {len(context) - len(filtered_context)} empty arrays from Particle")
        
        # Write JSON to cache
        error = PathResolver.write_json_file(particle_path, filtered_context)
        if error:
            logger.error(f"Failed to cache particle data: {error}")
            return None, f"Cache write failed: {error}"
        
        logger.info(f"Wrote Particle JSON to {particle_path}")
        return str(particle_path), None
    
    except Exception as e:
        logger.error(f"Write error for {file_path}: {str(e)}")
        return None, f"Write error: {str(e)}"

def read_particle(file_path: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Read Particle data from the particle cache."""
    try:
        particle_path = PathResolver.get_particle_path(file_path)
        logger.debug(f"Reading particle from {particle_path}")
        
        data, error = PathResolver.read_json_file(particle_path)
        if error:
            logger.error(f"Failed to read particle data: {error}")
            return None, f"Read error: {error}"
        
        logger.debug(f"Read particle data from {particle_path}, keys: {list(data.keys() if data else [])}")
        return data, None
    except Exception as e:
        logger.error(f"Error reading particle for {file_path}: {str(e)}")
        return None, f"Read error: {str(e)}"