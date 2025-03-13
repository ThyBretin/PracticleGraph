import os
from pathlib import Path
import pathspec

PROJECT_ROOT = "/project"

def filter_empty(obj):
    """
    Recursively filter empty arrays, dictionaries, and None values from nested objects.
    Used to reduce size of exported graph files.
    
    Args:
        obj: The object to filter (can be dict, list or primitive value)
        
    Returns:
        Filtered object with empty values removed
    """
    if isinstance(obj, dict):
        return {k: filter_empty(v) for k, v in obj.items() if v not in ([], {}, None)}
    elif isinstance(obj, list):
        return [filter_empty(v) for v in obj if v not in ([], {}, None)]
    return obj

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
