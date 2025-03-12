from src.core.particle_utils import particle_cache, logger

def deleteGraph(path: str) -> dict:
    """ 
    Delete a Particle Graph by feature name or path.
    
    Args:
        path: Name/path of the graph to delete
              Special values: "all" or "codebase" for the codebase-wide graph
    
    Returns:
        dict: Result containing deletion status message
    """
    logger.info(f"Deleting Particle Graph for: {path}")
    
    # Handle special codebase parameter
    if path.lower() in ("codebase", "all"):
        feature = "__codebase__"
    else:
        feature = path.lower()
    
    if feature in particle_cache:
        del particle_cache[feature]
        success_msg = f"Deleted Particle Graph for: {path}"
        logger.info(success_msg)
        return {
            "content": [{"type": "text", "text": success_msg}],
            "isError": False
        }
    else:
        error_msg = f"No Particle Graph found for: {path}"
        logger.error(error_msg)
        return {
            "content": [{"type": "text", "text": error_msg}],
            "isError": True,
            "error": error_msg
        }
