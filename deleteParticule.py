from particule_utils import particule_cache

def deleteParticule(feature: str) -> str:
    """ 
    Delete a Particule Graph by feature name.
    Returns a message indicating success or failure.
    """
    if feature in particule_cache:
        del particule_cache[feature]
        return f"Deleted {feature}"
    return f"No Particule found for {feature}"