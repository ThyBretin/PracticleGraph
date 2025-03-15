import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from src.graph.aggregate_app_story import aggregate_app_story
from src.graph.tech_stack import get_tech_stack
from src.particle.particle_support import logger
from src.helpers.data_cleaner import filter_empty
from src.particle.file_handler import read_particle
from src.core.path_resolver import PathResolver
from src.core.cache_manager import cache_manager
from src.helpers.gitignore_parser import load_gitignore

def createGraph(path: str) -> Dict:
    """
    Create a Particle Graph from existing Particle data for a feature or the entire codebase.
    
    Args:
        path: Path to create graph for, relative to PROJECT_ROOT
              Special values: "all" or "codebase" for full graph
    
    Returns:
        Dict: The created graph manifest
    """
    logger.info(f"Creating graph for path: {path}")
    
    # Normalize path
    is_full_codebase = path.lower() in ("all", "codebase")
    feature_path = str(PathResolver.PROJECT_ROOT) if is_full_codebase else str(PathResolver.resolve_path(path))
    feature_name = "codebase" if is_full_codebase else (path.split("/")[-1].lower() if "/" in path else path.lower())
    logger.debug(f"Feature name: {feature_name}, Path: {feature_path}")
    
    # Load gitignore
    gitignore = load_gitignore(feature_path)
    logger.debug(f"Gitignore loaded for {feature_path}")

    # Gather particle data (no addParticle call)
    particle_data = []
    processed_files = []
    js_files_total = 0
    
    logger.info(f"Scanning {feature_path} for existing Particle data...")
    for root, dirs, files in os.walk(feature_path):
        dirs[:] = [d for d in dirs if not gitignore.match_file(Path(root) / d)]
        logger.debug(f"Processing dir: {root}, {len(files)} files")
        for file in files:
            if file.endswith((".jsx", ".js")):
                js_files_total += 1
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
                        particle_data.append(particle)
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

    if not processed_files:
        logger.error(f"No Particle data found for {feature_name}. Run addParticle first.")
        return {"error": "No Particle data found. Run addParticle first.", "status": "ERROR"}

    # Split files
    logger.debug(f"Splitting {len(processed_files)} files...")
    primary_files = [f for f in processed_files if "shared" not in f["path"] and f["type"] != "test"]
    shared_files = [f for f in processed_files if "shared" in f["path"] or f["type"] == "test"]

    # Build tech stack and app story
    try:
        logger.debug("Generating tech stack...")
        tech_stack = get_tech_stack(processed_files)
        logger.debug("Aggregating app story...")
        app_story = aggregate_app_story(particle_data)
    except Exception as e:
        logger.error(f"Failed to build tech stack or app story: {str(e)}")
        tech_stack = {}
        app_story = {}

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

    # Filter empty arrays
    logger.debug("Filtering manifest...")
    manifest = filter_empty(manifest)

    # Write to cache
    graph_path = PathResolver.get_graph_path(feature_name)
    try:
        logger.debug(f"Writing graph to {graph_path}")
        error = PathResolver.write_json_file(graph_path, manifest)
        if error:
            logger.error(f"Error writing graph to {graph_path}: {error}")
            return {"error": f"Failed to write graph: {error}", "status": "ERROR"}
        
        if is_full_codebase:
            cache_manager.set("__codebase__", manifest)
        else:
            cache_manager.set(feature_name, manifest)
    except Exception as e:
        logger.error(f"Cache write failed: {str(e)}")
        return {"error": f"Cache write failed: {str(e)}", "status": "ERROR"}
        
    logger.info(f"Graph created for {feature_name}: {len(processed_files)} files, {manifest['coverage_percentage']}% coverage")
    return manifest