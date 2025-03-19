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

tokenizer = tiktoken.get_encoding("cl100k_base")

def createGraph(path: str) -> Dict:
    """Create a Particle Graph for a feature or codebase."""
    logger.info(f"Creating graph for path: {path}")
    
    if "," in path:
        features = [feat.strip() for feat in path.split(",")]
        logger.info(f"Creating multi-feature graph for: {features}")
        
        processed_files = []
        feature_names = []
        
        for feature_path in features:
            if feature_path.lower() in ("all", "codebase"):
                logger.warning(f"Skipping '{feature_path}' in multi-feature request")
                continue
                
            feature_name = feature_path.split("/")[-1].lower() if "/" in feature_path else feature_path.lower()
            feature_names.append(feature_name)
            
            try:
                resolved_path = str(PathResolver.resolve_path(feature_path))
                logger.debug(f"Initial resolved path for {feature_path}: {resolved_path}")
                
                if not os.path.exists(resolved_path) and os.path.exists("/project"):
                    potential_paths = [
                        str(PathResolver.resolve_path(f"thy/today/{feature_path}")),
                        str(PathResolver.resolve_path(f"/project/thy/today/{feature_path}"))
                    ]
                    for potential_path in potential_paths:
                        if os.path.exists(potential_path):
                            resolved_path = potential_path
                            logger.info(f"Adjusted to: {resolved_path}")
                            break
                
                if not os.path.exists(resolved_path):
                    logger.error(f"Path does not exist: {resolved_path}")
                    continue
                
                feature_files = processFiles(resolved_path)
                logger.info(f"Found {len(feature_files)} files for {feature_path}")
                processed_files.extend(feature_files)
            except Exception as e:
                logger.error(f"Error processing {feature_path}: {str(e)}")
                continue
        
        if not feature_names or not processed_files:
            logger.error("No valid features or files found")
            return {"error": "No valid features or files found", "status": "ERROR"}
        
        tech_stack = get_tech_stack(processed_files)
        cache_manager.set("tech_stack", tech_stack)
        
        aggregate_manifest = {
            "aggregate": True,
            "features": feature_names,
            "last_crawled": datetime.utcnow().isoformat() + "Z",
            "tech_stack": tech_stack,
            "files": {},
            "file_count": len(processed_files),
        }
        
        for feature_name in feature_names:
            feature_graph, found = cache_manager.get(feature_name)
            if found and isinstance(feature_graph, dict) and feature_graph.get("files"):
                aggregate_manifest["files"][feature_name] = feature_graph["files"]
            else:
                feature_files = [f for f in processed_files if feature_name in f["path"].lower()]
                aggregate_manifest["files"][feature_name] = {
                    "primary": [f for f in feature_files if "shared" not in f["path"] and f["type"] != "test"],
                    "shared": [f for f in feature_files if "shared" in f["path"] or f["type"] == "test"]
                }
        
        aggregate_manifest = filter_empty(aggregate_manifest, preserve_tech_stack=True)
        cache_key = "_".join(feature_names)
        graph_path = PathResolver.get_graph_path(cache_key)
        manifest_json = json.dumps(aggregate_manifest)
        token_count = len(tokenizer.encode(manifest_json))
        aggregate_manifest["token_count"] = token_count
        
        error = PathResolver.write_json_file(graph_path, aggregate_manifest)
        if error:
            logger.error(f"Failed to write graph: {error}")
            return {"error": f"Failed to write graph: {error}", "status": "ERROR"}
        
        cache_manager.set(cache_key, aggregate_manifest)
        logger.info(f"Created aggregate graph for {feature_names}: {len(processed_files)} files")
        return aggregate_manifest
    
    is_full_codebase = path.lower() in ("all", "codebase")
    if is_full_codebase:
        feature_path = str(PathResolver.PROJECT_ROOT)
        feature_name = "codebase"
    else:
        feature_path = str(PathResolver.resolve_path(path))
        feature_name = path.split("/")[-1].lower() if "/" in path else path.lower()
        if not os.path.exists(feature_path) and os.path.exists("/project"):
            for alt_path in [f"thy/today/{path}", f"/project/thy/today/{path}"]:
                alt_resolved = str(PathResolver.resolve_path(alt_path))
                if os.path.exists(alt_resolved):
                    feature_path = alt_resolved
                    logger.info(f"Adjusted to: {feature_path}")
                    break
    
    processed_files = processFiles(feature_path)
    if not processed_files:
        logger.error(f"No Particle data for {feature_name}")
        return {"error": f"No Particle data for '{path}'", "status": "ERROR"}

    primary_files = [f for f in processed_files if "shared" not in f["path"] and f["type"] != "test"]
    shared_files = [f for f in processed_files if "shared" in f["path"] or f["type"] == "test"]

    try:
        tech_stack = get_tech_stack(processed_files)
        cache_manager.set("tech_stack", tech_stack)
        app_story = aggregate_app_story([f.get("context", {}) for f in processed_files if f.get("context")])
    except Exception as e:
        logger.error(f"Failed tech stack/app story: {str(e)}")
        tech_stack = {}
        app_story = {}

    js_files_total = count_js_files(feature_path)
    manifest = {
        "feature": feature_name,
        "scoped_path": feature_path,
        "last_crawled": datetime.utcnow().isoformat() + "Z",
        "tech_stack": tech_stack,
        "files": {"primary": primary_files, "shared": shared_files},
        "file_count": len(processed_files),
        "js_files_total": js_files_total,
        "coverage_percentage": round((len(processed_files) / js_files_total * 100), 2) if js_files_total > 0 else 0,
        "app_story": app_story
    }

    manifest = filter_empty(manifest, preserve_tech_stack=True)
    graph_path = PathResolver.get_graph_path(feature_name)
    
    manifest_json = json.dumps(manifest)
    token_count = len(tokenizer.encode(manifest_json))
    manifest["token_count"] = token_count
    
    error = PathResolver.write_json_file(graph_path, manifest)
    if error:
        logger.error(f"Failed to write graph: {error}")
        return {"error": f"Failed to write graph: {error}", "status": "ERROR"}
    
    cache_manager.set(feature_name if not is_full_codebase else "__codebase__", manifest)
    logger.info(f"Created graph for {feature_name}: {len(processed_files)} files, {manifest['coverage_percentage']}% coverage")
    return manifest

def processFiles(feature_path: str) -> List[Dict]:
    """Process files, excluding unwanted dirs."""
    processed_files = []
    gitignore = load_gitignore(feature_path)
    exclude_dirs = {".git", "particle-graph", "android", "gradle", "__pycache__", ".vscode", "doc", "assets"}
    
    logger.info(f"Scanning {feature_path}...")
    for root, dirs, files in os.walk(feature_path):
        dirs[:] = [d for d in dirs if not gitignore.match_file(Path(root) / d) and d not in exclude_dirs]
        logger.debug(f"Processing dir: {root}, {len(files)} files")
        for file in files:
            if file.endswith((".jsx", ".js")):
                full_path = os.path.join(root, file)
                rel_path = PathResolver.relative_to_project(full_path)
                if gitignore.match_file(rel_path) or "particle_cache" in rel_path:
                    continue
                
                content, read_error = read_file(rel_path)
                if read_error:
                    logger.error(f"Error reading {rel_path}: {read_error}")
                    continue
                
                current_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
                particle, particle_error = read_particle(rel_path)
                is_stale = True
                
                if not particle_error and particle and particle.get("file_hash") == current_hash:
                    is_stale = False
                else:
                    logger.info(f"Regenerating particle for {rel_path}")
                    result = generate_particle(rel_path)
                    if result.get("isError"):
                        logger.error(f"Particle generation failed: {result.get('error')}")
                        continue
                    particle = result.get("particle")
                
                processed_files.append({
                    "path": rel_path,
                    "type": "test" if "__tests__" in rel_path else "file",
                    "context": particle if "test" not in rel_path else None
                })
    return processed_files

def count_js_files(feature_path: str) -> int:
    """Count JS files, excluding unwanted dirs."""
    js_files_total = 0
    gitignore = load_gitignore(feature_path)
    exclude_dirs = {".git", "particle-graph", "android", "gradle", "__pycache__", ".vscode", "doc", "assets"}
    
    for root, dirs, files in os.walk(feature_path):
        dirs[:] = [d for d in dirs if not gitignore.match_file(Path(root) / d) and d not in exclude_dirs]
        for file in files:
            if file.endswith((".jsx", ".js")):
                full_path = os.path.join(root, file)
                rel_path = PathResolver.relative_to_project(full_path)
                if not gitignore.match_file(rel_path) and "particle_cache" not in rel_path:
                    js_files_total += 1
    return js_files_total