import json
from pathlib import Path
from src.core.particle_utils import app_path, logger

# Configurable tech categories (unchanged)
TECH_CATEGORIES = {
    "expo_sdk": {
        "packages": ["expo"],
        "format": lambda v: f"~{v}"
    },
    "core_libraries": {
        "packages": ["react", "react-dom", "react-native", "expo-router", "expo-.*"],
        "format": lambda v: v
    },
    "state_management": {
        "subcategories": {
            "global": ["zustand", "redux", "@reduxjs/toolkit", "mobx", "jotai"],
            "local": ["react"]  # React state inferred if React is present
        },
        "format": lambda v: f"{v['name']} {v['version']}" if v.get("name") else "React state"
    },
    "ui_libraries": {
        "packages": ["react-native-unistyles", "@mui/.*", "@material-ui/.*", "@shopify/.*"],
        "format": lambda v: v
    },
    "backend": {
        "subcategories": {
            "database": ["supabase", "@supabase/.*"],
            "http": ["axios", "fetch"]
        },
        "format": lambda v: f"{v['name']} {v['version']}" if "database" in v.get("subcategory", "") else v
    },
    "key_dependencies": {
        "packages": [],  # Populated dynamically with all significant deps
        "format": lambda v: v
    }
}

# get_tech_stack(entities: list) -> dict
# [x] What: Extracts a categorized tech stack with versions from package.json and file hints—e.g., Expo SDK, Core Libraries, State Management.
# Inputs: List of file entities (e.g., [{"path": "components/Core/Auth/hooks/useAuth.js", "type": "file"}, ...]).
# Actions: Loads dependencies from package.json, categorizes them using TECH_CATEGORIES config, infers additional tech from file extensions (e.g., .jsx -> React), and builds a structured tech stack dict.
# Output: Categorized tech stack JSON (e.g., {"expo_sdk": "~52.0.36", "core_libraries": {"react": "18.3.1"}, ...}).

def get_tech_stack(entities: list) -> dict:
    """Extract a categorized tech stack with versions from package.json, using configurable categories."""
    pkg_path = Path(app_path) / "package.json"
    tech_stack = {
        cat: {} if "subcategories" in TECH_CATEGORIES[cat] or cat in ["core_libraries", "ui_libraries", "key_dependencies"] else None
        for cat in TECH_CATEGORIES
    }
    key_deps = {}

    # Load package.json
    try:
        with open(pkg_path, "r", encoding="utf-8") as f:
            pkg = json.load(f)
            deps = pkg.get("dependencies", {})
            logger.debug(f"Loaded {len(deps)} dependencies from {pkg_path}")
    except Exception as e:
        logger.error(f"Failed to load {pkg_path}: {e}")
        return tech_stack

    # Categorize dependencies
    for dep, version in deps.items():
        matched = False
        for category, config in TECH_CATEGORIES.items():
            if category == "key_dependencies":
                continue
            if "subcategories" in config:
                for subcat, patterns in config["subcategories"].items():
                    if any(p == dep or (p.endswith(".*") and dep.startswith(p[:-2])) for p in patterns):
                        tech_stack[category][subcat] = config["format"]({"name": dep, "version": version, "subcategory": subcat})
                        matched = True
                        break
                if matched:
                    key_deps[dep] = version
                    break
            elif "packages" in config:
                if any(p == dep or (p.endswith(".*") and dep.startswith(p[:-2])) for p in config["packages"]):
                    if category == "expo_sdk":
                        tech_stack[category] = config["format"](version.lstrip("~^"))  # Strip ~ or ^ to avoid double ~
                    else:
                        tech_stack[category][dep] = config["format"](version)
                    matched = True
                    key_deps[dep] = version
                    break
        if not matched:
            key_deps[dep] = version

    # File extension hints
    react_detected = False
    for entity in entities:
        ext = Path(entity["path"]).suffix.lower()
        if ext in (".jsx", ".tsx"):
            react_detected = True
            if "react" not in deps:
                tech_stack["core_libraries"]["react"] = "unknown"
        if ext == ".tsx" and "typescript" not in deps:
            key_deps["typescript"] = "unknown"

    # Infer React state if React is present
    if react_detected or "react" in deps:
        tech_stack["state_management"]["local"] = TECH_CATEGORIES["state_management"]["format"]({})

    # Populate key_dependencies
    tech_stack["key_dependencies"] = {k: TECH_CATEGORIES["key_dependencies"]["format"](v) for k, v in key_deps.items()}

    # Clean up empty categories
    for category in list(tech_stack.keys()):
        if not tech_stack[category] or (isinstance(tech_stack[category], dict) and not any(tech_stack[category].values())):
            del tech_stack[category]

    logger.info(f"Tech stack for {entities[0]['path'].split('/')[2] if entities else 'unknown'}: {tech_stack}")
    return tech_stack