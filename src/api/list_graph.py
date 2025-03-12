from src.core.particle_utils import logger, particle_cache

def listGraph() -> dict:
    """
    List all cached Particle Graphs with their last crawled timestamp.
    Returns a dictionary of feature names to their last crawled timestamp.
    """
    if not particle_cache:
        logger.info("No Particle Graph cached yet")
        return {"message": "No Particle Graph available"}
    return {k: v["last_crawled"] for k, v in particle_cache.items()}