from particule_utils import logger, particule_cache

def listGraph() -> dict:
    if not particule_cache:
        logger.info("No Particule Graph cached yet")
        return {"message": "No Particule Graph available"}
    return {k: v["last_crawled"] for k, v in particule_cache.items()}