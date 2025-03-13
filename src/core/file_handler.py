import re
import json
import os
from pathlib import Path
from typing import Tuple, Dict, Any, Optional, Union

from src.core.particle_utils import logger
from src.core.path_resolver import PathResolver

def read_file(file_path: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """Read file content or return an error."""
    try:
        # Resolve path using PathResolver
        full_path = PathResolver.resolve_path(file_path)
        logger.debug(f"Processing: {full_path} (raw: {file_path}, exists: {full_path.exists()})")

        if not full_path.exists():
            logger.error(f"File not found: {full_path}")
            return None, {"error": f"File not found: {full_path}"}
        if full_path.is_dir():
            logger.error(f"Directory detected: {full_path} (expected a file)")
            return None, {"error": f"Got a directory: {file_path}. Use createParticle for directories."}

        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
        logger.debug(f"File content read: {len(content)} chars")
        return content, None
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {str(e)}")
        return None, {"error": f"Error reading file: {str(e)}"}

def read_particle(file_path: str) -> Tuple[Dict[str, Any], Optional[str]]:
    """Read particle data for a file from the cache."""
    try:
        # Get the particle path using PathResolver
        particle_path = PathResolver.get_particle_path(file_path)
        data, error = PathResolver.read_json_file(particle_path)
        if error:
            return {}, f"Failed to read particle data: {error}"
        return data, None
    except Exception as e:
        return {}, f"Error reading particle data: {str(e)}"

def write_particle(file_path: str, context: dict) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """Write Particle export to file, updating if it exists."""
    try:
        # Resolve file path using PathResolver
        full_path = PathResolver.resolve_path(file_path)
        
        # Store the particle in the particle cache as well
        particle_path = PathResolver.get_particle_path(file_path)
        error = PathResolver.write_json_file(particle_path, context)
        if error:
            logger.warning(f"Failed to cache particle data: {error}")
        
        # Remove empty arrays from context
        filtered_context = {k: v for k, v in context.items() if not (isinstance(v, list) and len(v) == 0)}
        logger.debug(f"Filtered {len(context) - len(filtered_context)} empty arrays from Particle")
        
        # Use json.dumps for valid formatting
        try:
            export_str = f"export const Particle = {json.dumps(filtered_context, indent=2, ensure_ascii=False)};"
            # Validate it
            json.loads(export_str.split("=", 1)[1].rstrip(";"))
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON generated for {file_path}: {e}")
            return None, {"error": f"Invalid JSON: {e}"}

        # Read existing content if file exists
        if full_path.exists():
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()

            if "export const Particle" in content:
                updated_content = re.sub(
                    r"export\s+const\s+Particle\s*=\s*\{.*?\};",
                    export_str,
                    content,
                    flags=re.DOTALL
                )
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(updated_content)
                logger.info(f"Particle updated in {file_path}")
            else:
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(export_str + "\n\n" + content)
                logger.info(f"Particle added to {file_path}")
        else:
            # Create directory if it doesn't exist
            full_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(export_str)
            logger.info(f"Created new file with Particle: {file_path}")

        return export_str, None
    except Exception as e:
        logger.error(f"Error writing particle to {file_path}: {str(e)}")
        return None, {"error": f"Error writing particle: {str(e)}"}