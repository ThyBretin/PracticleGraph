from particle_utils import particle_cache
from createParticle import createParticle

def updateParticle(feature: str) -> dict:
    """
    Update a Particle Graph by feature name.
    Returns the updated manifest.
    """
    feature_path = f"components/Features/{feature}"
    manifest = createParticle(feature_path)
    particle_cache[feature] = manifest
    return manifest