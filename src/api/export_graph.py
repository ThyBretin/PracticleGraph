import json
import subprocess
from datetime import datetime
from pathlib import Path

import tiktoken

from src.particle.particle_support import logger
from src.api.create_graph import createGraph
from src.helpers.data_cleaner import filter_empty
from src.core.path_resolver import PathResolver
from src.core.cache_manager import cache_manager
from src.graph.graph_support import postProcessGraph

tokenizer = tiktoken.get_encoding("cl100k_base")

def exportGraph(*args, paths=None, **kwargs) -> dict:
    """Export a Particle Graph to a JSON file, formatted with Prettier."""
    # For fastmcp compatibility - extract paths from kwargs if provided there
    if not paths and 'params' in kwargs and isinstance(kwargs['params'], dict) and 'paths' in kwargs['params']:
        paths = kwargs['params']['paths']
        logger.info(f"Found paths in kwargs['params']: {paths}")
    
    if paths is not None:
        effective_paths = paths if isinstance(paths, list) else [paths]
    else:
        effective_paths = list(args) if args else []
    
    logger.info(f"Exporting graph for paths: {effective_paths}")
    
    # Return error if no paths provided
    if not effective_paths:
        logger.warning("No paths provided to exportGraph. This is likely a JSON-RPC parameter issue.")
        # Fall back to most recent graph if available
        cached_graphs = cache_manager.keys()
        if cached_graphs:
            # Filter out special keys
            feature_graphs = [g for g in cached_graphs if g not in ["__codebase__", "tech_stack", "all"]]
            if feature_graphs:
                # Use 'events' specifically if we can find it
                events_graph = next((g for g in feature_graphs if 'event' in g.lower()), None)
                if events_graph:
                    most_recent = events_graph
                    logger.info(f"Falling back to Events graph: {most_recent}")
                else:
                    most_recent = feature_graphs[0]  # First graph as fallback
                    logger.info(f"Falling back to first graph: {most_recent}")
                effective_paths = [most_recent]
            else:
                logger.info("No suitable fallback graphs found")
                return {
                    "content": [{"type": "text", "text": "No paths provided. Please include 'paths' parameter in your request."}],
                    "status": "ERROR",
                    "isError": True
                }
        else:
            logger.info("No cached graphs available for fallback")
            return {
                "content": [{"type": "text", "text": "No paths provided. Please include 'paths' parameter in your request."}],
                "status": "ERROR",
                "isError": True
            }
    
    # Check if 'all' or 'codebase' was explicitly requested
    # This ensures we only export the full codebase when specifically asked for it
    is_full_codebase = len(effective_paths) == 1 and effective_paths[0].lower() in ("all", "codebase")
    
    # For each path, extract just the feature name (last part of the path)
    feature_names = []
    for path in effective_paths:
        # Handle the components/Features/Events format
        parts = path.split("/")
        feature_name = parts[-1].lower()
        # For path like "components/Features/Events", we want "events" not "components_features_events"
        feature_names.append(feature_name)
    
    export_key = "codebase" if is_full_codebase else "_".join(feature_names)
    
    graphs = []
    if is_full_codebase:
        manifest = createGraph("all")
        logger.debug(f"Full codebase manifest: {type(manifest)}, keys: {list(manifest.keys())}")
        if "error" in manifest:
            logger.error(f"Failed to create graph for 'all': {manifest['error']}")
            return {
                "content": [{"type": "text", "text": f"Error: {manifest['error']}"}],
                "status": "ERROR",
                "isError": True
            }
        graphs.append(manifest)
    else:
        for path in effective_paths:
            # Extract just the feature name for cache lookup
            feature_name = path.split("/")[-1].lower()
            logger.info(f"Looking up graph for feature: {feature_name}")
            
            graph, found = cache_manager.get(feature_name)
            logger.debug(f"Cache get for {feature_name}: found={found}, type={type(graph)}")
            
            if not found or not isinstance(graph, dict):
                logger.info(f"Graph for {feature_name} not cached, generating using path: {path}")
                graph = createGraph(path)
                if "error" in graph:
                    logger.error(f"Failed to create graph for {path}: {graph['error']}")
                    return {
                        "content": [{"type": "text", "text": f"Error: {graph['error']}"}],
                        "status": "ERROR",
                        "isError": True
                    }
            graphs.append(graph)
    
    if len(graphs) > 1:
        merged = {
            "aggregate": True,
            "features": feature_names,
            "last_crawled": datetime.utcnow().isoformat() + "Z",
            "tech_stack": {},
            "files": {},
            "file_count": 0,
            "token_count": 0
        }
        for graph in graphs:
            merged["tech_stack"].update(graph.get("tech_stack", {}))
            if graph.get("aggregate"):
                merged["files"].update(graph.get("files", {}))
            else:
                merged["files"][graph["feature"]] = graph.get("files", {})
            merged["file_count"] += graph.get("file_count", 0)
            merged["token_count"] += graph.get("token_count", 0)
        manifest = filter_empty(merged, preserve_tech_stack=True)
    else:
        manifest = graphs[0]
        logger.debug(f"Single graph manifest: {type(manifest)}, keys: {list(manifest.keys())}")
        if not is_full_codebase and "files" in manifest:
            manifest = postProcessGraph(manifest, manifest.get("scoped_path"))
            logger.debug(f"Post-processed manifest: {type(manifest)}, keys: {list(manifest.keys())}")
    
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    filename = f"{export_key}_graph_{timestamp}.json"
    output_path = PathResolver.export_path(filename)
    temp_path = output_path.with_suffix('.tmp.json')
    
    logger.debug(f"Writing manifest to {temp_path}, type: {type(manifest)}")
    with open(temp_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f)
    
    try:
        subprocess.run(['prettier', '--write', str(temp_path), '--parser', 'json', '--print-width', '120', '--no-bracket-spacing'], check=True)
        with open(temp_path, 'r', encoding='utf-8') as f:
            formatted_content = f.read()
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(formatted_content)
        temp_path.unlink()
    except subprocess.CalledProcessError as e:
        logger.error(f"Prettier failed: {e}")
        return {
            "content": [{"type": "text", "text": f"Prettier failed: {e}"}],
            "status": "ERROR",
            "isError": True
        }
    
    logger.info(f"Exported graph to {output_path}")
    return {
        "content": [{"type": "text", "text": f"Graph exported to {output_path}"}],
        "status": "OK",
        "isError": False,
        "note": f"Exported {len(graphs)} graphs as {export_key}",
        "file_count": manifest.get("file_count", 0),
        "token_count": manifest.get("token_count", 0)
    }