from typing import Dict, List

def aggregate_app_story(particle_data: List[Dict]) -> Dict:
    """
    Aggregate routes, data, and components from particle data into an app_story.
    
    Args:
        particle_data: List of particle contexts from processed files
        
    Returns:
        Dict with routes, data, and components
    """
    routes = set()
    data = set()
    components = {}

    for particle in particle_data:
        # Routes from router.push calls
        for call in particle.get("calls", []):
            if call.startswith("router.push"):
                route = call.split("router.push('")[1].rstrip("')") if "router.push('" in call else call
                routes.add(route)

        # Data (agnostic—any fetch-like or query calls)
        for call in particle.get("calls", []):
            if any(kw in call for kw in ["fetch", "axios", ".from(", ".query("]):
                data.add(call)

        # Components from JSX usage
        for jsx in particle.get("jsx", []):
            component = jsx.split(" on ")[-1] if " on " in jsx else jsx
            components[component] = components.get(component, 0) + 1

    return {
        "routes": list(routes),
        "data": list(data),
        "components": components
    }
