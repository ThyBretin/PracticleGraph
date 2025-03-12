from particle_utils import particle_cache

def deleteParticle(feature: str) -> str:
    """ 
    Delete a Particle Graph by feature name.
    Returns a message indicating success or failure.
    """
    if feature in particle_cache:
        del particle_cache[feature]
        return f"Deleted {feature}"
    return f"No Particle found for {feature}"