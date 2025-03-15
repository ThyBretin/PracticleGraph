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
                
                return {"manifest": codebase_graph, "token_count": token_count}
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
            return {"manifest": graph, "token_count": token_count}
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
            return {"manifest": multi_graph, "token_count": token_count}
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
    return {"manifest": manifest, "token_count": token_count}