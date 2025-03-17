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

# Tokenizer setup
tokenizer = tiktoken.get_encoding("cl100k_base")

def exportGraph(*args, paths=None) -> dict:
    """
    Export a Particle Graph (single, multiple, or all) to a JSON file, formatted with Prettier.
    
    Args:
        *args: Positional feature names or paths (e.g., "Events", "Navigation")
        paths: Optional keyword arg for list of paths (e.g., ["Events", "Navigation"])
    
    Returns:
        dict: JSON-RPC response with export details
    """
    # Handle both positional and keyword args
    if paths is not None:
        effective_paths = paths if isinstance(paths, list) else [paths]
    else:
        effective_paths = list(args) if args else []
    
    logger.info(f"Exporting graph for paths: {effective_paths}")
    
    if not effective_paths:
        return {
            "content": [{"type": "text", "text": "No paths provided"}],
            "status": "ERROR",
            "isError": True
        }
    
    # Handle "all" or "codebase" as a single path
    is_full_codebase = len(effective_paths) == 1 and effective_paths[0].lower() in ("all", "codebase")
    feature_names = [p.split("/")[-1].lower() for p in effective_paths]
    export_key = "codebase" if is_full_codebase else "_".join(feature_names)
    
    # Load or generate graphs
    graphs = []
    if is_full_codebase:
        manifest = createGraph("all")
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
            graph, found = cache_manager.get(path.split("/")[-1].lower())
            if not found or not isinstance(graph, dict):
                logger.info(f"Graph for {path} not cached, generating...")
                graph = createGraph(path)
                if "error" in graph:
                    logger.error(f"Failed to create graph for {path}: {graph['error']}")
                    return {
                        "content": [{"type": "text", "text": f"Error: {graph['error']}"}],
                        "status": "ERROR",
                        "isError": True
                    }
            graphs.append(graph)
    
    # Merge graphs if multiple
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
        if not is_full_codebase and "files" in manifest:
            manifest = postProcessGraph(manifest)
    
    # Export to file
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    filename = f"{export_key}_graph_{timestamp}.json"
    output_path = PathResolver.export_path(filename)
    temp_path = output_path.with_suffix('.tmp.json')
    
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