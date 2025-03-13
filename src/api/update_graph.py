from src.core.particle_utils import logger
from src.core.cache_manager import cache_manager
from src.api.create_graph import createGraph

def updateGraph(path: str) -> dict:
    """
    Update a Particle Graph by feature name or path.
    
    Args:
        path: Name/path of the graph to update
              Feature name will be converted to "components/Features/{path}"
              Special values: "all" or "codebase" to update the codebase-wide graph
    
    Returns:
        dict: The updated graph manifest
    """
    logger.info(f"Updating Particle Graph for: {path}")
    
    # Handle special codebase parameter
    if path.lower() in ("codebase", "all"):
        feature_path = "all"
        cache_key = "__codebase__"
    else:
        # Maintain the original path construction logic
        feature_path = f"components/Features/{path}"
        cache_key = path.lower()
    
    # Create updated graph
    manifest = createGraph(feature_path)
    
    # Update cache if successful
    if "error" not in manifest:
        cache_manager.set(cache_key, manifest, persist=True)
        logger.info(f"Updated Particle Graph for: {path}")
    else:
        logger.error(f"Failed to update Particle Graph for: {path}")
    
    return manifest
