import os
from pathlib import Path

from src.particle.file_handler import read_file, write_particle
from src.core.file_processor import process_directory
from src.particle.particle_generator import generate_particle
from src.particle.particle_support import logger
from src.core.path_resolver import PathResolver

def addParticle(path: str = None, recursive: bool = False, rich: bool = True) -> dict:
    """
    Add Particle metadata to JavaScript/JSX files.
    
    This unified function handles both single file and recursive directory processing:
    - If recursive=False, processes one file (like addParticle)
    - If recursive=True, processes a directory recursively (like addParticle)
    - Handles special "all" parameter for codebase-wide operations
    
    Args:
        path: Path to the JS/JSX file or directory to analyze (absolute or relative to PROJECT_ROOT)
              or "all" to process all files in the project
        recursive: If True, process directory recursively; if False, process single file
        rich: If True, include detailed metadata including key_logic and depends_on
        
    Returns:
        dict: Result containing the Particle data and operation status
    """
    logger.info(f"*** ADD PARTICLE FUNCTION CALLED with path: {path}, recursive: {recursive} ***")
    
    # Special case: handle "all" parameter (always recursive)
    if path and path.lower() in ("all", "codebase"):
        logger.info("Processing entire codebase")
        normalized_path = str(PathResolver.PROJECT_ROOT)
        recursive = True
    else:
        try:
            normalized_path = str(PathResolver.resolve_path(path))
            logger.info(f"Normalized path: {normalized_path}")
        except ValueError as e:
            logger.error(f"Path resolution error: {str(e)}")
            return {
                "content": [{"type": "text", "text": f"Error resolving path: {str(e)}"}],
                "status": "ERROR",
                "isError": True,
                "errors": [str(e)]
            }
    
    path_obj = Path(normalized_path)
    
    # If not recursive and path is a file, use generate_particle directly
    if not recursive and path_obj.is_file():
        logger.info(f"Processing single file directly: {path_obj}")
        return generate_particle(normalized_path, rich)
    else:
        # Directory processing (recursive) or path is a directory
        result = process_directory(normalized_path, rich)
        return {
            "content": [{"type": "text", "text": result["summary"]}],
            "status": result["status"],
            "isError": result["status"] != "OK",
            "modified_count": result["modified_count"],
            "errors": result["errors"]
        }
