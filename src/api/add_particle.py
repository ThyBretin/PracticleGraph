import subprocess
import json
import os
from pathlib import Path
import pathspec

from src.core.file_handler import read_file, write_particle
from src.core.particle_utils import logger

PROJECT_ROOT = "/project"

def generate_particle(file_path: str = None, rich: bool = True) -> dict:
    """
    Generate Particle metadata for a single JavaScript/JSX file.
    
    Args:
        file_path: Path to the JS/JSX file to analyze (absolute or relative to PROJECT_ROOT)
        rich: If True, include detailed metadata including key_logic and depends_on
        
    Returns:
        dict: Result containing Particle data and operation status
    """
    logger.info(f"Starting generate particle with file_path: {file_path}")
    if not file_path:
        logger.error("No file_path provided to generate particle")
        return {"error": "No file_path provided"}

    # Handle paths that might contain the host machine path
    host_prefix = "/Users/Thy/Today/"
    if file_path.startswith(host_prefix):
        relative_path = file_path[len(host_prefix):]
        logger.warning(f"Converted host path '{file_path}' to relative: '{relative_path}'")
    elif file_path.startswith(PROJECT_ROOT):
        relative_path = file_path[len(PROJECT_ROOT) + 1:]  # Strip '/project/'
    else:
        relative_path = file_path

    absolute_path = Path(PROJECT_ROOT) / relative_path
    logger.debug(f"Computed relative_path: {relative_path}")
    logger.debug(f"Computed absolute_path: {absolute_path}")

    content, error = read_file(relative_path)
    if error:
        logger.error(f"File read failed for {relative_path}: {error}")
        return {"error": f"Read failed: {error}"}

    try:
        node_path = str(absolute_path)
        cmd = ['node', '/app/js/babel_parser.js', node_path]
        env = os.environ.copy()
        if rich:
            env['RICH_PARSING'] = '1'
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, env=env)
        if not result.stdout.strip():
            logger.error(f"Empty output from Babel for {relative_path}")
            return {"error": "Babel produced empty output"}
        
        context = json.loads(result.stdout)
        filtered_context = {k: v for k, v in context.items() if v}  # Filter falsy values
        export_str, error = write_particle(relative_path, filtered_context)
        if error:
            return {"error": f"Write failed: {error}"}

        summary = (f"Found {len(filtered_context.get('props', []))} props, "
                  f"{len(filtered_context.get('hooks', []))} hooks, "
                  f"{len(filtered_context.get('calls', []))} calls")
        if rich:
            summary += (f", {len(filtered_context.get('logic', []))} logic, "
                       f"{len(filtered_context.get('depends_on', []))} deps")
        logger.info(f"Generated summary: {summary}")

        return {
            "content": [{"type": "text", "text": export_str}],
            "summary": summary,
            "status": "OK",
            "isError": False,
            "note": "Particle applied to file",
            "post_action": "read",
            "context": filtered_context  # Full rich output
        }
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Babel failed for {relative_path}: {e.stderr}")
        return {"error": f"Babel parse failed: {e.stderr}"}
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON from Babel for {relative_path}: {e}")
        return {"error": f"Invalid JSON: {e}"}

def load_gitignore(root_dir):
    """
    Load and parse .gitignore file from the specified directory.
    
    Args:
        root_dir: Directory containing .gitignore file
        
    Returns:
        pathspec.PathSpec: Parsed gitignore patterns
    """
    gitignore_path = Path(root_dir) / ".gitignore"
    if gitignore_path.exists():
        with open(gitignore_path, "r") as f:
            return pathspec.PathSpec.from_lines("gitwildmatch", f)
    return pathspec.PathSpec.from_lines("gitwildmatch", [])

def process_directory(root_dir: str, rich: bool = True) -> dict:
    """
    Process all JavaScript/JSX files in a directory recursively.
    
    Args:
        root_dir: Root directory to process
        rich: If True, include detailed metadata
        
    Returns:
        dict: Summary of operation
    """
    logger.info(f"Processing directory: {root_dir}")
    
    gitignore = load_gitignore(root_dir)
    root_path = Path(root_dir)
    modified_count = 0
    errors = []
    js_files_found = 0

    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith((".jsx", ".js")):
                js_files_found += 1
                file_path = Path(root) / file
                rel_path = file_path.relative_to(root_path)
                logger.debug(f"Found JS/JSX file: {rel_path}")
                
                if gitignore.match_file(rel_path):
                    logger.debug(f"Skipped (gitignore): {rel_path}")
                else:
                    try:
                        result = generate_particle(str(file_path), rich)
                        if result.get("isError", True):
                            errors.append(f"{rel_path}: {result.get('error', 'Unknown error')}")
                        else:
                            modified_count += 1
                            logger.info(f"Particled: {rel_path}")
                    except Exception as e:
                        errors.append(f"{rel_path}: {e}")

    if js_files_found == 0:
        logger.warning(f"No JS/JSX files found in {root_dir}")
    
    status = "OK" if not errors else "PARTIAL"
    summary = f"Modified {modified_count} files"
    if errors:
        summary += f", {len(errors)} errors: {', '.join(errors[:3])}" + (len(errors) > 3 and "..." or "")
    logger.info(f"Directory processing summary: {summary}")
    
    return {
        "modified_count": modified_count,
        "errors": errors,
        "js_files_found": js_files_found,
        "status": status,
        "summary": summary
    }

def normalize_path(path: str) -> str:
    """
    Normalize path to handle host paths, absolute paths, and relative paths.
    
    Args:
        path: Path to normalize (host path, absolute container path, or relative path)
        
    Returns:
        str: Normalized path within container
    """
    # Handle "all" or "codebase" special case
    if path and path.lower() in ("all", "codebase"):
        return PROJECT_ROOT
        
    # Handle paths that might contain the host machine path
    host_prefix = "/Users/Thy/Today"  # No trailing slash to match exact path too
    if path == host_prefix or (path and path.startswith(host_prefix + "/")):
        logger.warning(f"Converting host path '{path}' to container path")
        # If it's an exact match or has additional path components
        if path == host_prefix:
            return PROJECT_ROOT
        else:
            # Extract the part after "/Users/Thy/Today/" and append to PROJECT_ROOT
            relative_part = path[len(host_prefix) + 1:]  # +1 for the slash
            return os.path.join(PROJECT_ROOT, relative_part)
    elif path and path != PROJECT_ROOT and not path.startswith(PROJECT_ROOT + "/"):
        # If it's not already the project root and doesn't start with it,
        # treat it as a path relative to project root
        return os.path.join(PROJECT_ROOT, path)
    
    return path

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
        normalized_path = PROJECT_ROOT
        recursive = True
    else:
        normalized_path = normalize_path(path)
        logger.info(f"Normalized path: {normalized_path}")
    
    # Process based on recursive flag
    if recursive:
        # Directory processing (recursive)
        result = process_directory(normalized_path, rich)
        return {
            "content": [{"type": "text", "text": result["summary"]}],
            "status": result["status"],
            "isError": result["status"] != "OK",
            "modified_count": result["modified_count"],
            "errors": result["errors"]
        }
    else:
        # Single file processing
        return generate_particle(normalized_path, rich)
