from practicle_utils import practicle_cache
from createPracticle import createPracticle

def updatePracticle(feature: str) -> dict:
    feature_path = f"components/Features/{feature}"
    manifest = createPracticle(feature_path)
    practicle_cache[feature] = manifest
    return manifest