from practicle_utils import practicle_cache

def deletePracticle(feature: str) -> str:
    if feature in practicle_cache:
        del practicle_cache[feature]
        return f"Deleted {feature}"
    return f"No Practicle found for {feature}"