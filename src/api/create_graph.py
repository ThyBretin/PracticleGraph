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
        error = PathResolver.write_json_file(graph_path, manifest)
        if error:
            logger.error(f"Error writing graph to {graph_path}: {error}")
            return {"error": f"Failed to write graph: {error}", "status": "ERROR"}
        
        # Serialize, count tokens, and compress for cache
        manifest_json = json.dumps(manifest)
        token_count = len(tokenizer.encode(manifest_json))
        
        # Add token count to the manifest itself
        manifest["token_count"] = token_count
        
        # Re-serialize with token count included
        manifest_json = json.dumps(manifest)
        compressed = zlib.compress(manifest_json.encode())
        
        logger.info(f"Created graph for {feature_name}: {len(processed_files)} files, {manifest['coverage_percentage']}% coverage, {token_count} tokens")
        
        if is_full_codebase:
            cache_manager.set("__codebase__", compressed)
        else:
            cache_manager.set(feature_name, compressed)
    except Exception as e:
        logger.error(f"Cache write failed: {str(e)}")
        return {"error": f"Cache write failed: {str(e)}", "status": "ERROR"}
        
    return {"manifest": manifest, "token_count": token_count}

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