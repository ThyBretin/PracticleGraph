##load_graph.py 

from datetime import datetime
import json
import zlib
import tiktoken

from src.particle.particle_support import logger
from src.core.path_resolver import PathResolver
from src.core.cache_manager import cache_manager

# Tokenizer setup
tokenizer = tiktoken.get_encoding("cl100k_base")

def loadGraph(path: str) -> dict:
    """
    Load and optionally aggregate Particle Graphs for one or more features.
    
    Args:
        path: Path/feature name(s) to load graph for
              Can be comma-separated for multiple features (e.g., "Events,Role")
              Special values: "all" or "codebase" to load the full codebase graph
    
    Returns:
        dict: The loaded graph manifest or aggregated manifests if multiple features
    """
    logger.info(f"Loading Particle Graph for: {path}")
    
    # Handle special codebase parameter
    if path.lower() in ("codebase", "all"):
        # Load the codebase-wide Particle Graph
        cached, found = cache_manager.get("__codebase__")
        if found:
            logger.info("Loading codebase-wide Particle Graph")
            
            # Decompress the cached data
            try:
                manifest_json = zlib.decompress(cached).decode()
                codebase_graph = json.loads(manifest_json)
                
                # Use existing token count if available, otherwise calculate it
                if "token_count" in codebase_graph:
                    token_count = codebase_graph["token_count"]
                else:
                    token_count = len(tokenizer.encode(manifest_json))
                    # Add token count to the manifest
                    codebase_graph["token_count"] = token_count
                
                logger.info(f"Loaded codebase graph with {codebase_graph.get('file_count', 0)} files ({codebase_graph.get('coverage_percentage', 0)}% coverage), {token_count} tokens")
                
                return codebase_graph
            except Exception as e:
                logger.error(f"Error decompressing codebase graph: {str(e)}")
                return {"error": f"Failed to decompress codebase graph: {str(e)}"}
        else:
            error_msg = "Codebase Particle Graph not found. Run createGraph('all') first."
            logger.error(error_msg)
            return {"error": error_msg}
    
    # Parse comma-separated features
    feature_list = [f.strip().lower() for f in path.split(",")]
    logger.debug(f"Loading Particle Graphs: {feature_list}")

    # Single feature: return directly from cache
    if len(feature_list) == 1:
        feature = feature_list[0]
        cached, found = cache_manager.get(feature)
        if not found:
            error_msg = f"Particle Graph '{feature}' not found in cache"
            logger.error(error_msg)
            return {"error": error_msg}
            
        try:
            manifest_json = zlib.decompress(cached).decode()
            graph = json.loads(manifest_json)
            
            # Use existing token count if available, otherwise calculate it
            if "token_count" in graph:
                token_count = graph["token_count"]
            else:
                token_count = len(tokenizer.encode(manifest_json))
                # Add token count to the manifest
                graph["token_count"] = token_count
                
            logger.info(f"Loaded single Particle Graph: {feature}, {token_count} tokens")
            return graph
        except Exception as e:
            logger.error(f"Error decompressing graph for {feature}: {str(e)}")
            return {"error": f"Failed to decompress graph: {str(e)}"}

    # Check if this exact multi-feature combination already exists in cache
    cache_key = "_".join(feature_list)
    cached, found = cache_manager.get(cache_key)
    if found:
        try:
            manifest_json = zlib.decompress(cached).decode()
            multi_graph = json.loads(manifest_json)
            
            # Use existing token count if available, otherwise calculate it
            if "token_count" in multi_graph:
                token_count = multi_graph["token_count"]
            else:
                token_count = len(tokenizer.encode(manifest_json))
                # Add token count to the manifest
                multi_graph["token_count"] = token_count
                
            logger.info(f"Loaded cached multi-feature graph for: {feature_list}, {token_count} tokens")
            return multi_graph
        except Exception as e:
            logger.error(f"Error decompressing multi-feature graph: {str(e)}")
            return {"error": f"Failed to decompress multi-feature graph: {str(e)}"}

    # Multiple features: check all exist
    missing = [f for f in feature_list if not cache_manager.has_key(f)]
    if missing:
        error_msg = f"Particles Graphs not found in cache: {missing}"
        logger.error(error_msg)
        return {"error": error_msg}

    # Get the global tech stack (if available)
    tech_stack, found = cache_manager.get("tech_stack")
    if not found:
        logger.warning("Global tech stack not found, aggregating from features")
        # Fallback: Aggregate tech_stack from features (though this shouldn't be necessary)
        tech_stack = {}
        for feature in feature_list:
            cached, _ = cache_manager.get(feature)
            try:
                manifest_json = zlib.decompress(cached).decode()
                graph = json.loads(manifest_json)
                feature_tech = graph.get("tech_stack", {})
                for category, value in feature_tech.items():
                    if isinstance(value, dict):
                        if category not in tech_stack:
                            tech_stack[category] = {}
                        tech_stack[category].update(value)
                    else:
                        tech_stack[category] = value
            except Exception as e:
                logger.error(f"Error decompressing graph for tech stack aggregation: {str(e)}")
                continue

    # Group files by feature
    aggregated_files = {}
    file_count = 0
    js_files_total = 0
    
    for feature in feature_list:
        cached, _ = cache_manager.get(feature)
        try:
            manifest_json = zlib.decompress(cached).decode()
            feature_graph = json.loads(manifest_json)
            aggregated_files[feature] = feature_graph.get("files", {})
            
            # Aggregate stats if available
            if "file_count" in feature_graph:
                file_count += feature_graph.get("file_count", 0)
            if "js_files_total" in feature_graph:
                js_files_total += feature_graph.get("js_files_total", 0)
        except Exception as e:
            logger.error(f"Error decompressing graph for file aggregation: {str(e)}")
            continue

    # Calculate coverage percentage
    coverage_percentage = round((file_count / js_files_total * 100) if js_files_total > 0 else 0, 2)
    
    manifest = {
        "aggregate": True,
        "features": feature_list,
        "last_loaded": datetime.utcnow().isoformat() + "Z",
        "tech_stack": tech_stack,
        "files": aggregated_files,
        "file_count": file_count,
        "js_files_total": js_files_total,
        "coverage_percentage": coverage_percentage
    }
    
    # Serialize and compress before caching
    manifest_json = json.dumps(manifest)
    token_count = len(tokenizer.encode(manifest_json))
    
    # Add token count to the manifest itself
    manifest["token_count"] = token_count
    
    # Re-serialize with token count included
    manifest_json = json.dumps(manifest)
    compressed = zlib.compress(manifest_json.encode())
    
    # Cache this combination for future use
    cache_manager.set(cache_key, compressed)
    
    logger.info(f"Aggregated Particles Graph for {feature_list} with {file_count} files ({coverage_percentage}% coverage), {token_count} tokens")
    return manifest

    ## path_resolver.py

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


## Dockerfile


FROM python:3.10-slim
RUN apt-get update && apt-get install -y nodejs npm
WORKDIR /app

# Create necessary directories
RUN mkdir -p src/api src/core src/graph src/helpers src/particle/js

# Copy server.py from root
COPY server.py ./

# Copy API files
COPY src/api/add_particle.py src/api/create_graph.py src/api/load_graph.py src/api/list_graph.py src/api/update_graph.py src/api/export_graph.py src/api/delete_graph.py src/api/

# Copy core files
COPY src/core/path_resolver.py src/core/cache_manager.py src/core/file_processor.py src/core/

# Copy particle files
COPY src/particle/particle_support.py src/particle/file_handler.py src/particle/dependency_tracker.py src/particle/particle_generator.py src/particle/

# Copy particle JS files
COPY src/particle/js/babel_parser_core.js src/particle/js/metadata_extractor.js src/particle/js/

# Copy graph files
COPY src/graph/tech_stack.py src/graph/aggregate_app_story.py src/graph/graph_support.py src/graph/

# Copy helpers
COPY src/helpers/project_detector.py src/helpers/dir_scanner.py src/helpers/config_loader.py src/helpers/gitignore_parser.py src/helpers/data_cleaner.py src/helpers/

# Add app directory to Python path
ENV PYTHONPATH=/app

RUN pip install fastmcp pathspec tiktoken
RUN npm install @babel/parser
RUN npm install -g prettier
CMD ["python", "server.py"]

create_graph.py

import json
import os
import zlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import tiktoken

from src.graph.aggregate_app_story import aggregate_app_story
from src.graph.tech_stack import get_tech_stack
from src.particle.particle_support import logger
from src.helpers.data_cleaner import filter_empty
from src.particle.file_handler import read_particle
from src.core.path_resolver import PathResolver
from src.core.cache_manager import cache_manager
from src.helpers.gitignore_parser import load_gitignore

# Tokenizer setup
tokenizer = tiktoken.get_encoding("cl100k_base")

def createGraph(path: str) -> Dict:
    """
    Create a Particle Graph from existing Particle data for a feature or the entire codebase.
    
    Args:
        path: Path to create graph for, relative to PROJECT_ROOT
              Special values: "all" or "codebase" for full graph
              Can be comma-separated for multiple features (e.g., "Events,Navigation")
    
    Returns:
        Dict: The created graph manifest
    """
    logger.info(f"Creating graph for path: {path}")
    
    # Check if it's a multi-feature request
    if "," in path:
        features = [feat.strip() for feat in path.split(",")]
        logger.info(f"Creating multi-feature graph for: {features}")
        
        # Process each feature path to build a list of processed files
        processed_files = []
        feature_names = []
        
        for feature_path in features:
            # Skip "all" and "codebase" in multi-feature as they are handled separately
            if feature_path.lower() in ("all", "codebase"):
                logger.warning(f"Skipping '{feature_path}' in multi-feature request - use it alone instead")
                continue
                
            feature_name = feature_path.split("/")[-1].lower() if "/" in feature_path else feature_path.lower()
            feature_names.append(feature_name)
            
            # Improve path resolution for specific features
            try:
                # First try a direct path within PROJECT_ROOT
                resolved_path = str(PathResolver.resolve_path(feature_path))
                
                # If path appears incorrect (doesn't exist), try in thy/today/ directory
                if not os.path.exists(resolved_path) and os.path.exists("/project"):
                    potential_paths = [
                        str(PathResolver.resolve_path(f"thy/today/{feature_path}")), 
                        str(PathResolver.resolve_path(f"/project/thy/today/{feature_path}"))
                    ]
                    
                    for potential_path in potential_paths:
                        if os.path.exists(potential_path):
                            logger.info(f"Found feature at alternate path: {potential_path}")
                            resolved_path = potential_path
                            break
                
                logger.debug(f"Resolved path for {feature_path}: {resolved_path}")
                feature_files = processFiles(resolved_path)
                processed_files.extend(feature_files)
            except Exception as e:
                logger.error(f"Error resolving path for {feature_path}: {str(e)}")
                continue
            
        if not feature_names:
            logger.error("No valid features found in multi-feature request")
            return {"error": "No valid features found in multi-feature request", "status": "ERROR"}
            
        # Compute full tech stack and cache it globally
        tech_stack = get_tech_stack(processed_files)
        cache_manager.set("tech_stack", tech_stack)
        
        # Prepare the aggregate manifest
        aggregate_manifest = {
            "aggregate": True,
            "features": feature_names,
            "last_crawled": datetime.utcnow().isoformat() + "Z",
            "tech_stack": tech_stack,
            "files": {},
            "file_count": len(processed_files),
        }
        
        # Add files from each feature to the aggregate manifest
        for feature_name in feature_names:
            feature_graph, found = cache_manager.get(feature_name)
            if found:
                aggregate_manifest["files"][feature_name] = feature_graph.get("files", {})
        
        # Filter empty values but preserve tech_stack
        aggregate_manifest = filter_empty(aggregate_manifest, preserve_tech_stack=True)
        
        # Cache the aggregate manifest
        cache_key = "_".join(feature_names)
        cache_manager.set(cache_key, aggregate_manifest)
        
        logger.info(f"Created aggregate graph for {feature_names}: {len(processed_files)} files")
        return aggregate_manifest
    
    # Normalize path for single feature or "all"
    is_full_codebase = path.lower() in ("all", "codebase")
    
    if is_full_codebase:
        feature_path = str(PathResolver.PROJECT_ROOT)
        feature_name = "codebase"
    else:
        # Improved path resolution for specific features
        # First, try resolving the path directly
        feature_path = str(PathResolver.resolve_path(path))
        feature_name = path.split("/")[-1].lower() if "/" in path else path.lower()
        
        # If path doesn't exist, try common alternatives
        if not os.path.exists(feature_path) and os.path.exists("/project"):
            logger.debug(f"Path {feature_path} doesn't exist, trying alternatives...")
            alternate_paths = [
                str(PathResolver.resolve_path(f"thy/today/{path}")),
                str(PathResolver.resolve_path(f"/project/thy/today/{path}"))
            ]
            
            for alt_path in alternate_paths:
                if os.path.exists(alt_path):
                    logger.info(f"Found feature at alternate path: {alt_path}")
                    feature_path = alt_path
                    break
    
    logger.debug(f"Feature name: {feature_name}, Path: {feature_path}")
    
    # Process files to build the graph
    processed_files = processFiles(feature_path)
    
    if not processed_files:
        logger.error(f"No Particle data found for {feature_name}. Run addParticle first.")
        return {"error": f"No Particle data found for path '{path}'. Run addParticle first.", "status": "ERROR"}

    # Split files
    logger.debug(f"Splitting {len(processed_files)} files...")
    primary_files = [f for f in processed_files if "shared" not in f["path"] and f["type"] != "test"]
    shared_files = [f for f in processed_files if "shared" in f["path"] or f["type"] == "test"]

    # Compute full tech stack and cache it globally
    try:
        logger.debug("Generating tech stack...")
        tech_stack = get_tech_stack(processed_files)
        cache_manager.set("tech_stack", tech_stack)
        
        logger.debug("Aggregating app story...")
        app_story = aggregate_app_story([f.get("context", {}) for f in processed_files if f.get("context")])
    except Exception as e:
        logger.error(f"Failed to build tech stack or app story: {str(e)}")
        tech_stack = {}
        app_story = {}

    # Count total JS files for coverage calculation
    js_files_total = count_js_files(feature_path)

    # Construct manifest
    manifest = {
        "feature": feature_name,
        "last_crawled": datetime.utcnow().isoformat() + "Z",
        "tech_stack": tech_stack,
        "files": {
            "primary": primary_files,
            "shared": shared_files
        },
        "file_count": len(processed_files),
        "js_files_total": js_files_total,
        "coverage_percentage": round((len(processed_files) / js_files_total * 100), 2) if js_files_total > 0 else 0,
        "app_story": app_story
    }

    # Filter empty values but preserve tech_stack
    logger.debug("Filtering manifest...")
    manifest = filter_empty(manifest, preserve_tech_stack=True)

    # Write to cache
    graph_path = PathResolver.get_graph_path(feature_name)
    try:
        logger.debug(f"Writing graph to {graph_path}")
        
        # Serialize and count tokens before writing to file
        manifest_json = json.dumps(manifest)
        token_count = len(tokenizer.encode(manifest_json))
        
        # Add token count to the manifest itself BEFORE writing to file
        manifest["token_count"] = token_count
        
        # Write the manifest with token count to the file
        error = PathResolver.write_json_file(graph_path, manifest)
        if error:
            logger.error(f"Error writing graph to {graph_path}: {error}")
            return {"error": f"Failed to write graph: {error}", "status": "ERROR"}
        
        # Compress for cache
        manifest_json = json.dumps(manifest)  # Re-serialize with token count
        compressed = zlib.compress(manifest_json.encode())
        
        logger.info(f"Created graph for {feature_name}: {len(processed_files)} files, {manifest['coverage_percentage']}% coverage, {token_count} tokens")
        
        if is_full_codebase:
            cache_manager.set("__codebase__", compressed)
        else:
            cache_manager.set(feature_name, compressed)
    except Exception as e:
        logger.error(f"Cache write failed: {str(e)}")
        return {"error": f"Cache write failed: {str(e)}", "status": "ERROR"}
        
    return manifest  # Return the manifest directly with token_count included

def processFiles(feature_path: str) -> List[Dict]:
    """
    Process files in a directory to build a list of files with particle data.
    
    Args:
        feature_path: Path to process, must be an absolute path
    
    Returns:
        List[Dict]: List of processed files with particle data
    """
    processed_files = []
    
    # Load gitignore
    gitignore = load_gitignore(feature_path)
    logger.debug(f"Gitignore loaded for {feature_path}")
    
    logger.info(f"Scanning {feature_path} for existing Particle data...")
    for root, dirs, files in os.walk(feature_path):
        dirs[:] = [d for d in dirs if not gitignore.match_file(Path(root) / d)]
        logger.debug(f"Processing dir: {root}, {len(files)} files")
        for file in files:
            if file.endswith((".jsx", ".js")):
                full_path = os.path.join(root, file)
                rel_path = PathResolver.relative_to_project(full_path)
                if gitignore.match_file(rel_path) or "particle_cache" in rel_path:
                    logger.debug(f"Skipping {rel_path} (gitignore or particle_cache)")
                    continue
                try:
                    logger.debug(f"Reading particle for {rel_path}")
                    particle, error = read_particle(rel_path)
                    if not error and particle:
                        file_type = "test" if "__tests__" in rel_path else "file"
                        processed_files.append({
                            "path": rel_path,
                            "type": file_type,
                            "context": particle if file_type != "test" else None
                        })
                        logger.debug(f"Added {rel_path} to graph with {len(particle.get('props', []))} props")
                    else:
                        logger.warning(f"Skipped {rel_path}: {error or 'No particle data'}")
                except Exception as e:
                    logger.error(f"Error reading {full_path}: {str(e)}")
                    continue
    
    return processed_files

def count_js_files(feature_path: str) -> int:
    """
    Count the total number of JavaScript files in a directory.
    
    Args:
        feature_path: Path to count files in, must be an absolute path
    
    Returns:
        int: Total number of JavaScript files
    """
    js_files_total = 0
    
    # Load gitignore
    gitignore = load_gitignore(feature_path)
    
    for root, dirs, files in os.walk(feature_path):
        dirs[:] = [d for d in dirs if not gitignore.match_file(Path(root) / d)]
        for file in files:
            if file.endswith((".jsx", ".js")):
                full_path = os.path.join(root, file)
                rel_path = PathResolver.relative_to_project(full_path)
                if not gitignore.match_file(rel_path) and "particle_cache" not in rel_path:
                    js_files_total += 1
    
    return js_files_total


 ## .env
 GETREAL_PATH=/Users/Thy/Today 
note : I'm not sure if it gets used or not 


 ## server.py

 import fastmcp
import logging
from src.particle.particle_support import logger
from src.api.add_particle import addParticle
from src.api.create_graph import createGraph
from src.api.load_graph import loadGraph
from src.api.list_graph import listGraph
from src.api.update_graph import updateGraph
from src.api.delete_graph import deleteGraph
from src.api.export_graph import exportGraph

logger.setLevel(logging.DEBUG)

def main():
    mcp = fastmcp.FastMCP("particle-graph")
    mcp.tool()(addParticle)
    mcp.tool()(createGraph)
    mcp.tool()(listGraph)
    mcp.tool()(loadGraph)
    mcp.tool()(exportGraph)
    mcp.tool()(updateGraph)
    mcp.tool()(deleteGraph)

    logger.info("Server initialized, entering main loop")
    mcp.run()  # Stdin/stdout

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Server crashed: {e}")
        raise

## cache_manager.py

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


## Server stdin 

The server is configure via the client side by mcp config :
{
  "mcpServers": {
    "particle-graph": {
      "command": "docker",
      "args": ["run", "-v", "/Users/Thy/Today:/project", "-i", "particle-graph"],
      "stdio": true
    },

and loaded via the interactive commandline :

docker build -t particle-graph .
docker run -m 2g -v /Users/Thy/Today:/project -i particle-graph