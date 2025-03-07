from practicle_utils import app_path, practicle_cache
from createPracticle import createPracticle

def showPracticle(feature: str) -> dict:
    if feature not in practicle_cache:
        feature_path = f"components/Features/{feature}"
        practicle_cache[feature] = createPracticle(feature_path)
    return practicle_cache[feature]