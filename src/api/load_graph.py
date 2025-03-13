from datetime import datetime
from src.particle.particle_support import logger
from src.core.path_resolver import PathResolver
from src.core.cache_manager import cache_manager

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
        codebase_graph, found = cache_manager.get("__codebase__")
        if found:
            logger.info("Loading codebase-wide Particle Graph")
            
            # Ensure stats are correct
            routes = codebase_graph.get("routes", {})
            data = codebase_graph.get("data", {})
            components = codebase_graph.get("components", {})
            
            # Calculate file count (if not already set correctly)
            file_count = sum(len(collection) for collection in [routes, data, components])
            if file_count > 0:
                codebase_graph["file_count"] = file_count
                
                # For codebase graph, js_files_total is set during creation but ensure it's present
                if "js_files_total" not in codebase_graph or codebase_graph["js_files_total"] == 0:
                    codebase_graph["js_files_total"] = file_count  # Fallback
                    
                # Update coverage percentage
                js_files_total = codebase_graph["js_files_total"]
                codebase_graph["coverage_percentage"] = round((file_count / js_files_total * 100) if js_files_total > 0 else 0, 2)
            
            logger.info(f"Loaded codebase graph with {codebase_graph.get('file_count', 0)} files ({codebase_graph.get('coverage_percentage', 0)}% coverage)")
            
            # Update cached version if we made changes
            cache_manager.set("__codebase__", codebase_graph)
            return codebase_graph
        else:
            error_msg = "Codebase Particle Graph not found. Run createGraph('all') first."
            logger.error(error_msg)
            return {"error": error_msg}
    
    # Parse features (e.g., "Events,Role" → ["events", "role"]
    feature_list = [f.strip().lower() for f in path.split(",")]
    logger.debug(f"Loading Particle Graphs: {feature_list}")

    # Single feature: return directly from cache
    if len(feature_list) == 1:
        feature = feature_list[0]
        graph, found = cache_manager.get(feature)
        if not found:
            error_msg = f"Particle Graph '{feature}' not found in cache"
            logger.error(error_msg)
            return {"error": error_msg}
        logger.info(f"Loaded single Particle Graph: {feature}")
        return graph

    # Multiple features: aggregate
    missing = [f for f in feature_list if not cache_manager.has_key(f)]
    if missing:
        error_msg = f"Particles Graphs not found in cache: {missing}"
        logger.error(error_msg)
        return {"error": error_msg}

    # Aggregate tech_stack (deduplicate)
    aggregated_tech = {}
    for feature in feature_list:
        graph, _ = cache_manager.get(feature)
        tech = graph["tech_stack"]
        for category, value in tech.items():
            if isinstance(value, dict):
                if category not in aggregated_tech:
                    aggregated_tech[category] = {}
                aggregated_tech[category].update(value)
            else:
                aggregated_tech[category] = value

    # Group files by feature
    aggregated_files = {}
    file_count = 0
    js_files_total = 0
    
    for feature in feature_list:
        feature_graph, _ = cache_manager.get(feature)
        aggregated_files[feature] = feature_graph["files"]
        
        # Aggregate stats if available
        if "file_count" in feature_graph:
            file_count += feature_graph["file_count"]
        if "js_files_total" in feature_graph:
            js_files_total += feature_graph["js_files_total"]

    # Calculate coverage percentage
    coverage_percentage = round((file_count / js_files_total * 100) if js_files_total > 0 else 0, 2)
    
    manifest = {
        "aggregate": True,
        "features": feature_list,
        "last_loaded": datetime.utcnow().isoformat() + "Z",
        "tech_stack": aggregated_tech,
        "files": aggregated_files,
        "file_count": file_count,
        "js_files_total": js_files_total,
        "coverage_percentage": coverage_percentage
    }
    
    logger.info(f"Aggregated Particles Graph for {feature_list} with {file_count} files ({coverage_percentage}% coverage)")
    return manifest