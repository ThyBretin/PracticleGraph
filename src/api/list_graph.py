from src.particle.particle_support import logger
from src.core.cache_manager import cache_manager
from src.core.path_resolver import PathResolver

def listGraph() -> dict:
    """
    List all cached Particle Graphs with their last crawled timestamp.
    Returns a dictionary of feature names to their last crawled timestamp.
    """
    # Log cache directory location for debugging
    logger.info(f"Looking for cached graphs in: {PathResolver.CACHE_DIR}")
    
    # Get all cache keys
    keys = cache_manager.keys()
    logger.info(f"Found {len(keys)} potential graph keys: {keys}")
    
    if not keys:
        logger.info("No Particle Graph cached yet")
        return {
            "content": [{"type": "text", "text": "No Particle Graph available"}],
            "isError": False
        }
        
    result = {}
    for key in keys:
        try:
            # Skip internal keys and tech_stack
            if key.startswith("__") and key != "__codebase__":
                continue
            if key == "tech_stack":
                continue
                
            graph, found = cache_manager.get(key)
            
            if found and isinstance(graph, dict):
                # If graph is a dictionary and has last_crawled field
                if "last_crawled" in graph:
                    result[key] = graph["last_crawled"]
                else:
                    # Use creation timestamp if available, otherwise "unknown"
                    result[key] = graph.get("created_at", "unknown")
            elif found:
                # Graph was found but is not a dictionary
                logger.warning(f"Graph for key '{key}' is not a dictionary: {type(graph)}")
                result[key] = "invalid format"
            else:
                # Graph was not found
                logger.warning(f"Failed to retrieve graph for key: {key}")
        except Exception as e:
            # Catch any exceptions to prevent function failure
            logger.error(f"Error processing graph key '{key}': {str(e)}")
            result[key] = f"error: {str(e)}"
    
    if not result:
        logger.warning("No valid graphs found in cache")
        return {
            "content": [{"type": "text", "text": "No valid Particle Graphs available"}],
            "isError": False
        }
        
    # Format the result for MCP client
    formatted_list = []
    for graph_name, timestamp in sorted(result.items()):
        formatted_list.append(f"• {graph_name}: {timestamp}")
    
    formatted_text = "Available Particle Graphs:\n\n" + "\n".join(formatted_list)
    
    logger.info(f"Successfully listed {len(result)} graphs")
    return {
        "content": [{"type": "text", "text": formatted_text}],
        "isError": False
    }