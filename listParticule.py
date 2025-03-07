from particule_utils import logger, particule_cache

def listParticule() -> dict:
    if not particule_cache:
        logger.info("No Particule manifests cached yet")
        return {"message": "No manifests available"}
    return {k: v["last_crawled"] for k, v in particule_cache.items()}