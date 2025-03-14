from typing import Tuple, Optional, Dict, Any
from pathlib import Path
from src.core.path_resolver import PathResolver
from src.particle.particle_support import logger
import json
import re

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

def write_particle(file_path: str, context: dict) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """Write Particle export to file, updating if it exists."""
    try:
        # Resolve file path using PathResolver
        full_path = PathResolver.resolve_path(file_path)
        logger.debug(f"Resolved full_path: {full_path}")
        
        # Store the particle in the particle cache as well
        particle_path = PathResolver.get_particle_path(file_path)
        error = PathResolver.write_json_file(particle_path, context)
        if error:
            logger.warning(f"Failed to cache particle data: {error}")
        
        # Remove empty arrays from context
        filtered_context = {k: v for k, v in context.items() if not (isinstance(v, list) and len(v) == 0)}
        logger.debug(f"Filtered {len(context) - len(filtered_context)} empty arrays from Particle")
        
        # Custom single-line array formatting
        export_lines = ["export const Particle = {"]
        for key, value in filtered_context.items():
            if isinstance(value, list):
                formatted_value = json.dumps(value, separators=(',', ':'), ensure_ascii=False)
                export_lines.append(f'"{key}":{formatted_value},')
            else:
                formatted_value = json.dumps(value, ensure_ascii=False)
                export_lines.append(f'"{key}":{formatted_value},')
        export_lines[-1] = export_lines[-1].rstrip(',')  # Remove trailing comma
        export_lines.append("};")
        export_str = "\n".join(export_lines)
        logger.debug(f"Generated export_str: {export_str}")
        
        # Validate it parses as JS
        try:
            json.loads(export_str.split("=", 1)[1].rstrip(";"))
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON generated for {file_path}: {e}")
            return None, {"error": f"Invalid JSON: {e}"}
        
        # Write to file
        content, error = read_file(file_path)
        if error:
            logger.error(f"Read failed for {file_path}: {error}")
            return None, {"error": f"Read failed: {error}"}
        logger.debug(f"Original content length: {len(content)}")
        
        # Remove any existing Particle data from the content
        particle_pattern = re.compile(r'export\s+const\s+Particle\s*=\s*\{[\s\S]*?\};', re.MULTILINE)
        cleaned_content = re.sub(particle_pattern, '', content).strip()
        
        # Prepend the Particle data at the top of the file
        new_content = f"{export_str}\n\n{cleaned_content}"
        with open(full_path, 'w', encoding='utf-8') as f:
            logger.debug(f"Attempting write to {full_path}")
            f.write(new_content)
        logger.info(f"Wrote custom-formatted Particle to {full_path}")
        return export_str, None
    
    except Exception as e:
        logger.error(f"Write error for {file_path}: {str(e)}")
        return None, {"error": f"Write error: {str(e)}"}

def read_particle(file_path: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Read Particle data from the particle cache.
    
    Args:
        file_path: Path to the original file that the particle was generated for
        
    Returns:
        tuple: (particle_data, error) where particle_data is a dict and error is a string if there was an error
    """
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