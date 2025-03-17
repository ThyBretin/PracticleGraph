import json
import os
import zlib
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import tiktoken

from src.graph.aggregate_app_story import aggregate_app_story
from src.graph.tech_stack import get_tech_stack
from src.particle.particle_support import logger
from src.helpers.data_cleaner import filter_empty
from src.particle.file_handler import read_particle, read_file, write_particle
from src.core.path_resolver import PathResolver
from src.core.cache_manager import cache_manager
from src.helpers.gitignore_parser import load_gitignore
from src.helpers.dir_scanner import scan_directory
from src.particle.particle_generator import generate_particle

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
        
        processed_files = []
        feature_names = []
        
        for feature_path in features:
            if feature_path.lower() in ("all", "codebase"):
                logger.warning(f"Skipping '{feature_path}' in multi-feature request - use it alone instead")
                continue
                
            feature_name = feature_path.split("/")[-1].lower() if "/" in feature_path else feature_path.lower()
            feature_names.append(feature_name)
            
            try:
                # Resolve path
                resolved_path = str(PathResolver.resolve_path(feature_path))
                logger.debug(f"Initial resolved path for {feature_path}: {resolved_path}")
                
                # Fallback paths if initial resolution fails
                if not os.path.exists(resolved_path) and os.path.exists("/project"):
                    potential_paths = [
                        str(PathResolver.resolve_path(f"thy/today/{feature_path}")),
                        str(PathResolver.resolve_path(f"/project/thy/today/{feature_path}"))
                    ]
                    for potential_path in potential_paths:
                        if os.path.exists(potential_path):
                            resolved_path = potential_path
                            logger.info(f"Adjusted to alternate path: {resolved_path}")
                            break
                
                if not os.path.exists(resolved_path):
                    logger.error(f"Resolved path does not exist: {resolved_path} for {feature_path}")
                    continue
                
                # Process files
                feature_files = processFiles(resolved_path)
                logger.info(f"Found {len(feature_files)} files for {feature_path} at {resolved_path}")
                if not feature_files:
                    logger.warning(f"No files processed for {feature_path} - path may be empty or invalid")
                processed_files.extend(feature_files)
            except Exception as e:
                logger.error(f"Error processing {feature_path}: {str(e)}")
                continue
        
        if not feature_names:
            logger.error("No valid features found in multi-feature request")
            return {"error": "No valid features found in multi-feature request", "status": "ERROR"}
        
        if not processed_files:
            logger.error("No files processed for any features")
            return {"error": "No files found for any features", "status": "ERROR"}
        
        # Compute tech stack
        tech_stack = get_tech_stack(processed_files)
        cache_manager.set("tech_stack", tech_stack)
        
        # Build aggregate manifest
        aggregate_manifest = {
            "aggregate": True,
            "features": feature_names,
            "last_crawled": datetime.utcnow().isoformat() + "Z",
            "tech_stack": tech_stack,
            "files": {},
            "file_count": len(processed_files),
        }
        
        # Populate files directly from processed_files instead of relying solely on cache
        for feature_name in feature_names:
            # Try cached graph first
            feature_graph, found = cache_manager.get(feature_name)
            if found and isinstance(feature_graph, dict) and feature_graph.get("files"):
                aggregate_manifest["files"][feature_name] = feature_graph["files"]
                logger.debug(f"Loaded {len(feature_graph['files'])} files from cache for {feature_name}")
            else:
                # Fallback to processed files
                feature_files = [f for f in processed_files if feature_name in f["path"].lower()]
                aggregate_manifest["files"][feature_name] = {
                    "primary": [f for f in feature_files if "shared" not in f["path"] and f["type"] != "test"],
                    "shared": [f for f in feature_files if "shared" in f["path"] or f["type"] == "test"]
                }
                logger.debug(f"Added {len(feature_files)} files directly for {feature_name}")
        
        aggregate_manifest = filter_empty(aggregate_manifest, preserve_tech_stack=True)
        
        # Cache and write to file
        cache_key = "_".join(feature_names)
        graph_path = PathResolver.get_graph_path(cache_key)
        manifest_json = json.dumps(aggregate_manifest)
        token_count = len(tokenizer.encode(manifest_json))
        aggregate_manifest["token_count"] = token_count
        
        error = PathResolver.write_json_file(graph_path, aggregate_manifest)
        if error:
            logger.error(f"Failed to write aggregate graph to {graph_path}: {error}")
            return {"error": f"Failed to write graph: {error}", "status": "ERROR"}
        
        compressed = zlib.compress(manifest_json.encode())
        cache_manager.set(cache_key, compressed)
        
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
    Check for stale/missing particles using file hashes and regenerate if needed.
    
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
                    # Compute current file hash for freshness checks
                    content, read_error = read_file(rel_path)
                    if read_error:
                        logger.error(f"Error reading file content for {rel_path}: {read_error}")
                        continue
                    
                    current_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
                    logger.debug(f"Current hash for {rel_path}: {current_hash}")
                    
                    # Try to read cached particle
                    particle, particle_error = read_particle(rel_path)
                    is_stale = True  # Assume stale by default
                    
                    if not particle_error and particle:
                        # Check if particle has file_hash and compare with current hash
                        if 'file_hash' in particle and particle['file_hash'] == current_hash:
                            is_stale = False
                            logger.debug(f"Particle for {rel_path} is fresh (hash match)")
                        else:
                            logger.info(f"Particle for {rel_path} is stale (hash mismatch or missing hash)")
                    else:
                        logger.info(f"No cached particle for {rel_path} or read error: {particle_error}")
                    
                    # Regenerate particle if stale or missing
                    if is_stale:
                        logger.info(f"Regenerating particle for {rel_path}")
                        result = generate_particle(rel_path)
                        if result.get("isError"):
                            logger.error(f"Failed to generate particle for {rel_path}: {result.get('error')}")
                            continue
                        
                        # Get the freshly generated particle
                        particle = result.get("particle")
                        if not particle:
                            logger.error(f"Generated particle for {rel_path} is empty")
                            continue
                            
                        logger.info(f"Successfully regenerated particle for {rel_path}")
                    
                    # Add particle to processed files
                    file_type = "test" if "__tests__" in rel_path else "file"
                    processed_files.append({
                        "path": rel_path,
                        "type": file_type,
                        "context": particle if file_type != "test" else None
                    })
                    logger.debug(f"Added {rel_path} to graph with {len(particle.get('attributes', {}).get('props', []))} props")
                    
                except Exception as e:
                    logger.error(f"Error processing {full_path}: {str(e)}")
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