import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from src.api.add_particle import addParticle
from src.graph.aggregate_app_story import aggregate_app_story
from src.graph.tech_stack import get_tech_stack
from src.particle.particle_support import logger, particle_cache
from src.core.utils import filter_empty
from src.particle.file_handler import read_particle
from src.core.path_resolver import PathResolver
from src.core.cache_manager import cache_manager

def createGraph(path: str) -> Dict:
    """
    Create a Particle Graph for a feature or the entire codebase.
    
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
    feature_name = "codebase" if is_full_codebase else path.split("/")[-1].lower()

    # Process files with addParticle - this writes particle data to files
    particle_result = addParticle(path, recursive=True, rich=True)
    if particle_result.get("isError", True):
        logger.error(f"Failed to process particles: {particle_result.get('error')}")
        return {"error": "Particle processing failed", "status": "ERROR"}

    # Gather particle data - we need to read each processed file separately
    particle_data = []
    processed_files = []
    js_files_total = 0
    
    for root, _, files in os.walk(feature_path):
        for file in files:
            if file.endswith((".jsx", ".js")):
                js_files_total += 1
                full_path = os.path.join(root, file)
                try:
                    rel_path = PathResolver.relative_to_project(full_path)
                    
                    # Read the particle data that was written by addParticle
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
                        logger.debug(f"Skipped {rel_path}: {error or 'No particle data'}")
                except ValueError as e:
                    logger.warning(f"Error processing path {full_path}: {str(e)}")
                    continue

    # Split files
    primary_files = [f for f in processed_files if "shared" not in f["path"] and f["type"] != "test"]
    shared_files = [f for f in processed_files if "shared" in f["path"] or f["type"] == "test"]

    # Read package.json directly
    package_json_path = PathResolver.resolve_path("package.json")
    package_json = {}
    if package_json_path.exists():
        try:
            data, error = PathResolver.read_json_file(package_json_path)
            if not error:
                package_json = data
        except Exception as e:
            logger.warning(f"Error reading package.json: {str(e)}")
            
    tech_stack = get_tech_stack(processed_files)

    # Build app story
    app_story = aggregate_app_story(particle_data)

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
    manifest = filter_empty(manifest)

    # Write to cache file using PathResolver
    graph_path = PathResolver.get_graph_path(feature_name)
    error = PathResolver.write_json_file(graph_path, manifest)
    if error:
        logger.error(f"Error writing graph to {graph_path}: {error}")
        return {"error": f"Failed to write graph: {error}", "status": "ERROR"}
        
    # Update the in-memory cache too
    if is_full_codebase:
        cache_manager.set("__codebase__", manifest)
    else:
        cache_manager.set(feature_name, manifest)
        
    logger.info(f"Graph created for {feature_name}: {len(processed_files)} files, {manifest['coverage_percentage']}% coverage")
    return manifest


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        result = createGraph(sys.argv[1])
        print(json.dumps(result, indent=2))
    else:
        print("Please provide a path argument")