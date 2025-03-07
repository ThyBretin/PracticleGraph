import re
import json
from collections import Counter
from pathlib import Path
from practicle_utils import app_path, logger

def get_tech_stack(entities: list) -> list:
    """Extract top 6 techs from entities, filtered by package.json dependencies."""
    tech = Counter()
    deps = set()
    
    # Load package.json dependencies
    pkg_path = Path(app_path) / "package.json"
    try:
        with open(pkg_path, "r", encoding="utf-8") as f:
            pkg = json.load(f)
            deps.update(pkg.get("dependencies", {}).keys())
            # Skip devDependencies—focus on runtime tech
        logger.debug(f"Loaded {len(deps)} dependencies from {pkg_path}")
    except Exception as e:
        logger.error(f"Failed to load {pkg_path}: {e}")

    # Process each entity
    for entity in entities:
        file_path = Path(app_path) / entity["path"]
        ext = file_path.suffix.lower()
        
        # Base language from extension
        if ext in (".js", ".jsx"):
            tech["javascript"] += 1
            if ext == ".jsx":
                tech["react"] += 1  # JSX implies React
        elif ext in (".ts", ".tsx"):
            tech["typescript"] += 1
            if ext == ".tsx":
                tech["react"] += 1

        # Skip non-code files
        if ext not in (".js", ".jsx", ".ts", ".tsx"):
            continue
        
        # Scan imports
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                imports = re.findall(r"import\s+.*?\s+from\s+['\"]([^'\"]+)['\"]", content)
                for imp in imports:
                    if imp.startswith((".", "..", "/")):  # Skip local imports
                        continue
                    # Normalize sub-imports (e.g., "expo-image" -> "expo")
                    base_imp = imp.split("/")[0]
                    if base_imp in deps:  # Only count if in package.json
                        tech[base_imp] += 1
                    elif base_imp.startswith("expo-"):  # Special case for Expo
                        tech["expo"] += 1
        except Exception as e:
            logger.error(f"Failed to scan {file_path}: {e}")

    # Top 6 by count, then alphabetical
    top_tech = [t for t, _ in tech.most_common(6)]
    logger.info(f"Tech stack for {entities[0]['path'].split('/')[2] if entities else 'unknown'}: {top_tech}")
    return top_tech