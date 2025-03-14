from typing import Dict, List, Any, Union

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
        # Extract routes from the routes field (added in enhanced parser)
        for route_entry in particle.get("routes", []):
            if isinstance(route_entry, dict) and "path" in route_entry:
                routes.add(route_entry["path"])
            elif isinstance(route_entry, str):
                routes.add(route_entry)

        # Extract routes from calls (supporting both old and new formats)
        for call in particle.get("calls", []):
            if isinstance(call, dict):
                # New format: calls as objects with name and args
                if "name" in call and call["name"] in ["router.push", "router.replace", "navigate", "navigateToTab"]:
                    if call.get("args") and isinstance(call["args"], list) and len(call["args"]) > 0:
                        routes.add(call["args"][0])
            elif isinstance(call, str):
                # Old format: calls as strings
                if call.startswith("router.push"):
                    route = call.split("router.push('")[1].rstrip("')") if "router.push('" in call else call
                    routes.add(route)

        # Data (agnostic—any fetch-like or query calls)
        for call in particle.get("calls", []):
            if isinstance(call, dict):
                # New format: calls as objects
                if "name" in call:
                    call_name = call["name"]
                    if any(kw in call_name for kw in ["fetch", "axios", "supabase"]):
                        if call.get("args"):
                            data_entry = f"{call_name}({', '.join(map(str, call['args']))})"
                        else:
                            data_entry = call_name
                        data.add(data_entry)
            elif isinstance(call, str):
                # Old format: calls as strings
                if any(kw in call for kw in ["fetch", "axios", ".from(", ".query("]):
                    data.add(call)

        # Components from JSX usage (supporting both old and new formats)
        for jsx in particle.get("jsx", []):
            if isinstance(jsx, dict):
                # New format: JSX as objects with tag
                if "tag" in jsx:
                    component = jsx["tag"]
                    components[component] = components.get(component, 0) + 1
            elif isinstance(jsx, str):
                # Old format: JSX as strings
                component = jsx.split(" on ")[-1] if " on " in jsx else jsx
                components[component] = components.get(component, 0) + 1

    return {
        "routes": list(routes),
        "data": list(data),
        "components": components
    }
