import json
from datetime import datetime
from particule_utils import particule_cache, logger

def loadParticule(features: str) -> dict:
    """
    Load and optionally aggregate Particule manifests for one or more features.
    If multiple features are provided (comma-separated), aggregates tech_stack and groups files.
    """
    # Parse features (e.g., "Events,Role" → ["events", "role"])
    feature_list = [f.strip().lower() for f in features.split(",")]
    logger.debug(f"Loading features: {feature_list}")

    # Single feature: return directly from cache
    if len(feature_list) == 1:
        feature = feature_list[0]
        if feature not in particule_cache:
            logger.error(f"Feature '{feature}' not found in cache")
            return {"error": f"Feature '{feature}' not found"}
        logger.info(f"Loaded single feature: {feature}")
        return particule_cache[feature]

    # Multiple features: aggregate
    missing = [f for f in feature_list if f not in particule_cache]
    if missing:
        logger.error(f"Features not found in cache: {missing}")
        return {"error": f"Features not found: {missing}"}

    # Aggregate tech_stack (deduplicate)
    aggregated_tech = {}
    for feature in feature_list:
        tech = particule_cache[feature]["tech_stack"]
        for category, value in tech.items():
            if isinstance(value, dict):
                if category not in aggregated_tech:
                    aggregated_tech[category] = {}
                aggregated_tech[category].update(value)
            else:
                aggregated_tech[category] = value

    # Group files by feature
    aggregated_files = {}
    for feature in feature_list:
        aggregated_files[feature] = particule_cache[feature]["files"]

    manifest = {
        "aggregate": True,
        "features": feature_list,
        "last_crawled": datetime.utcnow().isoformat() + "Z",
        "tech_stack": aggregated_tech,
        "files": aggregated_files
    }
    logger.info(f"Aggregated manifest for features: {feature_list}")
    return manifest