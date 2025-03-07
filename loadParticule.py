from particule_utils import app_path, particule_cache
from createParticule import createParticule

def loadParticule(feature: str) -> dict:
    if feature not in particule_cache:
        feature_path = f"components/Features/{feature}"
        particule_cache[feature] = createParticule(feature_path)
    return particule_cache[feature]