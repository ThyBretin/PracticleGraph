import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from src.api.add_particle import addParticle
from src.core.particle_utils import logger

PROJECT_ROOT = "/project"
CACHE_DIR = Path("particle_cache")

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

def analyze_tech_stack(package_json: Dict) -> Dict:
    """
    Analyze tech stack from package.json (moved from tech_stack.py).
    """
    deps = {**package_json.get("dependencies", {}), **package_json.get("devDependencies", {})}
    tech_stack = {
        "core_libraries": {},
        "state_management": {"global": None, "local": "React state"},
        "ui_libraries": {},
        "backend": {},
        "key_dependencies": deps
    }
    
    if "expo" in deps:
        tech_stack["expo_sdk"] = deps["expo"]
        for dep in deps:
            if dep.startswith("expo-"):
                tech_stack["core_libraries"][dep] = deps[dep]
            elif dep in ["zustand", "redux"]:
                tech_stack["state_management"]["global"] = f"{dep} {deps[dep]}"
            elif "react-native" in dep or "native-base" in dep or "flash-list" in dep or "unistyles" in dep:
                tech_stack["ui_libraries"][dep] = deps[dep]
            elif "supabase" in dep or "firebase" in dep or "axios" in dep:
                tech_stack["backend"][dep] = deps[dep]
    
    return {k: v for k, v in tech_stack.items() if v}

def createGraph(path: str) -> Dict:
    """
    Create a Particle Graph for a feature or the entire codebase.
    
    Args:
        path: Path to create graph for, relative to PROJECT_ROOT
              Special values: "all" or "codebase" for full graph
    
    Returns:
        Dict: The created graph manifest
    """
    logger.info(f"Creating graph for path: {path}")
    
    # Normalize path
    is_full_codebase = path.lower() in ("all", "codebase")
    feature_path = PROJECT_ROOT if is_full_codebase else os.path.join(PROJECT_ROOT, path)
    feature_name = "codebase" if is_full_codebase else path.split("/")[-1].lower()

    # Ensure cache directory exists
    CACHE_DIR.mkdir(exist_ok=True)

    # Process files with addParticle
    particle_result = addParticle(path, recursive=True, rich=True)
    if particle_result.get("isError", True):
        logger.error(f"Failed to process particles: {particle_result.get('error')}")
        return {"error": "Particle processing failed", "status": "ERROR"}

    # Gather particle data
    particle_data = []
    processed_files = []
    js_files_total = 0
    
    for root, _, files in os.walk(feature_path):
        for file in files:
            if file.endswith((".jsx", ".js")):
                js_files_total += 1
                rel_path = os.path.relpath(os.path.join(root, file), PROJECT_ROOT)
                # Assume addParticle writes context to result['context'] or cache
                if "context" in particle_result:
                    particle = particle_result["context"]
                    particle_data.append(particle)
                    file_type = "test" if "__tests__" in rel_path else "file"
                    processed_files.append({
                        "path": rel_path,
                        "type": file_type,
                        "context": particle if file_type != "test" else None
                    })

    # Split files
    primary_files = [f for f in processed_files if "shared" not in f["path"] and f["type"] != "test"]
    shared_files = [f for f in processed_files if "shared" in f["path"] or f["type"] == "test"]

    # Read package.json directly
    package_json_path = os.path.join(PROJECT_ROOT, "package.json")
    package_json = {}
    if os.path.exists(package_json_path):
        with open(package_json_path, "r") as f:
            package_json = json.load(f)
    tech_stack = analyze_tech_stack(package_json)

    # Build app story
    app_story = aggregate_app_story(particle_data)

    # Construct manifest
    manifest = {
        "feature": feature_name,
        "last_crawled": datetime.utcnow().isoformat() + "Z",
        "tech_stack": tech_stack,
        "files": {
            "primary": primary_files,
            "shared": shared_files
        },
        "file_count": len(processed_files),
        "js_files_total": js_files_total,
        "coverage_percentage": round((len(processed_files) / js_files_total * 100), 2) if js_files_total > 0 else 0,
        "app_story": app_story
    }

    # Filter empty arrays
    def filter_empty(obj):
        if isinstance(obj, dict):
            return {k: filter_empty(v) for k, v in obj.items() if v not in ([], {}, None)}
        elif isinstance(obj, list):
            return [filter_empty(v) for v in obj if v not in ([], {}, None)]
        return obj
    manifest = filter_empty(manifest)

    # Write to cache
    cache_file = CACHE_DIR / f"{feature_name}_graph.json"
    with open(cache_file, "w") as f:
        json.dump(manifest, f, indent=2)

    logger.info(f"Graph created for {feature_name}: {len(processed_files)} files, {manifest['coverage_percentage']}% coverage")
    return manifest

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        result = createGraph(sys.argv[1])
        print(json.dumps(result, indent=2))
    else:
        logger.error("No path provided for createGraph")