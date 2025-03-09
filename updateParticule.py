from particule_utils import particule_cache
from createParticule import createParticule

def updateParticule(feature: str) -> dict:
    """
    Update a Particule Graph by feature name.
    Returns the updated manifest.
    """
    feature_path = f"components/Features/{feature}"
    manifest = createParticule(feature_path)
    particule_cache[feature] = manifest
    return manifest