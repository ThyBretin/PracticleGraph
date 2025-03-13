import os
from pathlib import Path
from typing import Dict, List

import pathspec

from src.particle.particle_support import logger


def load_gitignore(root_dir: str, recursive: bool = False) -> pathspec.PathSpec:
    """
    Load and parse .gitignore file(s) from the specified directory.
    
    Args:
        root_dir: Directory containing .gitignore file
        recursive: If True, recursively scan for .gitignore files in subdirectories
        
    Returns:
        pathspec.PathSpec: Parsed gitignore patterns when recursive=False
        Dict[Path, List[str]]: Directory paths mapped to gitignore patterns when recursive=True
    """
    if recursive:
        return _load_gitignore_recursive(root_dir)
    else:
        return _load_gitignore_single(root_dir)


def _load_gitignore_single(root_dir: str) -> pathspec.PathSpec:
    """
    Load and parse a single .gitignore file from the specified directory.
    
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


def _load_gitignore_recursive(root_path: str) -> Dict[Path, List[str]]:
    """
    Load gitignore patterns recursively from all .gitignore files in the directory tree.
    
    Args:
        root_path: The root directory to start searching from
        
    Returns:
        A dictionary mapping directory paths to lists of gitignore patterns
    """
    patterns = {}
    root = Path(root_path)
    
    # Function to process a .gitignore file
    def process_gitignore(path: Path, gitignore_path: Path):
        if not gitignore_path.exists():
            return
        
        try:
            with open(gitignore_path, "r", encoding="utf-8") as f:
                lines = []
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue
                    # Normalize patterns
                    if line.startswith('/'):
                        line = line[1:]  # Remove leading slash for relative patterns
                    # Add the pattern
                    lines.append(line)
                
                if lines:
                    patterns[path] = lines
                    logger.debug(f"Loaded {len(lines)} patterns from {gitignore_path}")
        except Exception as e:
            logger.warning(f"Error reading {gitignore_path}: {e}")
    
    # First check the root .gitignore
    process_gitignore(root, root / ".gitignore")
    
    # Then walk the directory tree to find all .gitignore files
    for dirpath, dirnames, filenames in os.walk(root_path):
        # Skip .git directories
        if '.git' in dirnames:
            dirnames.remove('.git')
        
        dir_path = Path(dirpath)
        if '.gitignore' in filenames:
            process_gitignore(dir_path, dir_path / '.gitignore')
    
    return patterns
