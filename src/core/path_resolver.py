import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, Union

class PathResolver:
    # Detect if running in Docker or locally
    if os.path.exists("/project"):
        # Docker environment with mount -v /Users/Thy/Today:/project
        PROJECT_ROOT = Path("/project")
        HOST_PROJECT_PATH = "/Users/Thy/Today"  # Matches your mount
    else:
        # Local environment
        PROJECT_ROOT = Path(os.getcwd())
        HOST_PROJECT_PATH = None
    
    # Adjusted to match your logs
    CACHE_DIR = Path(PROJECT_ROOT / "particle-graph/cache")
    EXPORT_DIR = Path(PROJECT_ROOT / "particle-graph")
    PARTICLE_EXTENSION = ".particle.json"

    @classmethod
    def ensure_dir(cls, directory: Path) -> Path:
        """Ensure a directory exists, creating it if necessary."""
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    @classmethod
    def translate_host_path(cls, path: str) -> str:
        """Translate a host path to a container path if needed."""
        if not cls.HOST_PROJECT_PATH:
            return path
        if path.startswith(cls.HOST_PROJECT_PATH):
            return path.replace(cls.HOST_PROJECT_PATH, str(cls.PROJECT_ROOT))
        return path

    @classmethod
    def resolve_path(cls, path: str, base: Path = PROJECT_ROOT) -> Path:
        """Resolve a path relative to a base, returning a normalized Path object."""
        try:
            path = cls.translate_host_path(path)
            if Path(path).is_absolute():
                return Path(path).resolve()
            return (base / path).resolve()
        except Exception as e:
            raise ValueError(f"Invalid path: {path}. Error: {str(e)}")

    @classmethod
    def relative_to_project(cls, path: Union[str, Path]) -> str:
        """Return a path relative to PROJECT_ROOT as a string."""
        try:
            path_obj = Path(path)
            if not path_obj.is_absolute():
                path_obj = cls.resolve_path(str(path))
            return str(path_obj.relative_to(cls.PROJECT_ROOT))
        except Exception as e:
            raise ValueError(f"Cannot make path {path} relative to project root. Error: {str(e)}")

    @classmethod
    def cache_path(cls, filename: str) -> Path:
        """Return a path in the cache directory."""
        cls.ensure_dir(cls.CACHE_DIR)
        return cls.CACHE_DIR / filename

    @classmethod
    def export_path(cls, filename: str) -> Path:
        """Return a path in the export directory."""
        cls.ensure_dir(cls.EXPORT_DIR)
        return cls.EXPORT_DIR / filename
        
    @classmethod
    def get_particle_path(cls, file_path: Union[str, Path]) -> Path:
        """Get the path to the particle file for a given source file."""
        rel_path = cls.relative_to_project(file_path)
        particle_filename = rel_path.replace("/", "_").replace(".", "_") + cls.PARTICLE_EXTENSION
        return cls.cache_path(particle_filename)
        
    @classmethod
    def get_graph_path(cls, feature_name: str) -> Path:
        """Get the path to the graph file for a given feature."""
        return cls.cache_path(f"{feature_name}_graph.json")
        
    @classmethod
    def read_json_file(cls, file_path: Union[str, Path]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Read and parse a JSON file safely."""
        try:
            path_obj = Path(file_path)
            if not path_obj.exists():
                return None, f"File not found: {file_path}"
            with open(path_obj, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data, None
        except json.JSONDecodeError as e:
            return None, f"JSON decode error: {str(e)}"
        except Exception as e:
            return None, f"Error reading file: {str(e)}"
            
    @classmethod
    def write_json_file(cls, file_path: Union[str, Path], data: Dict[str, Any]) -> Optional[str]:
        """Write data to a JSON file safely."""
        try:
            path_obj = Path(file_path)
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            with open(path_obj, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return None
        except Exception as e:
            return f"Error writing file: {str(e)}"