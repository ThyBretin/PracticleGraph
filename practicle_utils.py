import os
from pathlib import Path
import fnmatch
import re
import logging

logger = logging.getLogger("PracticalGraph")
app_path = os.getenv("APP_PATH", "/project")
practicle_cache = {}  # Moved here

def load_gitignore_patterns(base_path: str) -> dict:
    patterns = {}
    base_path = str(Path(base_path).resolve())
    gitignore_path = os.path.join(base_path, ".gitignore")
    if os.path.exists(gitignore_path):
        try:
            with open(gitignore_path, "r") as f:
                ignores = {line.strip().strip("/") for line in f if line.strip() and not line.startswith("#")}
            patterns[base_path] = ignores
            logger.debug(f"Loaded from {gitignore_path}: {ignores}")
        except Exception as e:
            logger.error(f"Error reading {gitignore_path}: {e}")
    if not patterns:
        patterns[base_path] = {"node_modules", ".git", ".expo", "android", "ios", "scripts", "dist", ".DS_Store", "*.log"}
        logger.info("Using fallback patterns")
    logger.info(f"Final .gitignore patterns: {patterns}")
    return patterns

def infer_file_type(file_path: Path) -> str:
    name = file_path.name.lower()
    path_str = str(file_path).lower()
    if ".test." in name:
        return "test"
    if "store" in name:
        return "store"
    if "state" in path_str or "state" in name:
        return "state"
    return "file"

def extract_practicle_logic(file_path: Path) -> str:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            match = re.search(r'export\s+const\s+Practicle\s*=\s*["\'](.+?)["\']', content)
            return match.group(1).strip() if match else None
    except Exception:
        return None

def extract_api_calls(file_path: Path) -> list:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            fetch_calls = re.findall(r'fetch\(["\']([^"\']+)["\']', content)
            axios_calls = re.findall(r'axios\.(?:get|post|put|delete)\(["\']([^"\']+)["\']', content)
            return list(set(fetch_calls + axios_calls)) or None
    except Exception:
        return None

def extract_tech_stack(file_path: Path) -> list:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            imports = re.findall(r'import\s+(?:[\w\s{},*]+from\s+)?["\']([^./][^"\']+)["\']', content)
            tech = [pkg for pkg in imports if pkg in {"react", "axios", "expo", "expo-router", "react-navigation"} or pkg.startswith("expo-")]
            return list(set(tech)) or None
    except Exception:
        return None