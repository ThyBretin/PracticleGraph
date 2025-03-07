import os
from pathlib import Path
import fnmatch
import re
import logging

logger = logging.getLogger("PracticalGraph")
app_path = os.getenv("APP_PATH", "/project")
particule_cache = {}  # Moved here

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

def extract_particule_logic(file_path: Path) -> str:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            match = re.search(r'export\s+const\s+ContextParticule\s*=\s*["\'](.+?)["\']', content)
            return match.group(1).strip() if match else None
    except Exception:
        return None

def extract_api_calls(file_path: Path) -> list | None:
    """
    Scan a file for API calls (fetch, axios, custom clients, Supabase auth) and extract endpoints or methods.
    Returns a list of detected API interactions (e.g., ["/api/roles", "supabase.auth.signIn"]) or None if none found.
    """
    calls = []
    if file_path.suffix.lower() not in (".js", ".jsx", ".ts", ".tsx"):
        logger.debug(f"Skipping API call extraction for non-code file: {file_path}")
        return None

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Fetch calls: fetch("/api/endpoint")
        fetch_matches = re.findall(r'fetch\s*\(\s*["\']([^"\']+)["\']', content)
        calls.extend(fetch_matches)

        # Axios calls: axios("/api/endpoint"), axios.get("/api/endpoint"), etc.
        axios_matches = re.findall(r'axios(?:\.\w+)?\s*\(\s*["\']([^"\']+)["\']', content)
        calls.extend(axios_matches)

        # Custom HTTP clients: http.get("/api/data"), apiClient("/api/users"), etc.
        custom_matches = re.findall(r'(?:http|apiClient)\.\w+\s*\(\s*["\']([^"\']+)["\']', content)
        calls.extend(custom_matches)

        # Supabase auth calls: supabase.auth.signInWithPassword, supabase.auth.signOut, etc.
        supabase_auth_matches = re.findall(r'supabase\.auth\.(signInWith\w+|signOut|signUp|resetPasswordForEmail|updateUser)\b', content)
        calls.extend([f"supabase.auth.{match}" for match in supabase_auth_matches])

        # Filter to likely endpoints/methods and deduplicate
        calls = [call.strip() for call in calls if call.strip()]  # Keep all non-empty matches
        calls = list(dict.fromkeys(calls))  # Preserve order, remove duplicates

        if calls:
            logger.debug(f"Found API calls in {file_path}: {calls}")
            return calls
        else:
            logger.debug(f"No API calls found in {file_path}")
            return None

    except Exception as e:
        logger.error(f"Failed to scan {file_path} for API calls: {e}")
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