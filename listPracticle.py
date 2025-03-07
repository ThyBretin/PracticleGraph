from practicle_utils import logger, practicle_cache

def listPracticle() -> dict:
    if not practicle_cache:
        logger.info("No Practicle manifests cached yet")
        return {"message": "No manifests available"}
    return {k: v["last_crawled"] for k, v in practicle_cache.items()}