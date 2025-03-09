from particule_utils import logger, particule_cache

def listGraph() -> dict:
    """
    List all cached Particule Graphs with their last crawled timestamp.
    Returns a dictionary of feature names to their last crawled timestamp.
    """
    if not particule_cache:
        logger.info("No Particule Graph cached yet")
        return {"message": "No Particule Graph available"}
    return {k: v["last_crawled"] for k, v in particule_cache.items()}