import json
import os
from pathlib import Path
import fnmatch
from fastmcp import FastMCP
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("PracticalGraph")

app_path = os.getenv("APP_PATH", "/project")
mcp = FastMCP("practical-graph")

def load_gitignore_patterns(base_path: str) -> dict:
    patterns = {}
    base_path = str(Path(base_path).resolve())
    logger.debug(f"Resolved base_path: {base_path}")
    gitignore_path = os.path.join(base_path, ".gitignore")
    if os.path.exists(gitignore_path):
        try:
            with open(gitignore_path, "r") as f:
                ignores = {line.strip().strip("/") for line in f if line.strip() and not line.startswith("#")}
            patterns[base_path] = ignores
            logger.debug(f"Loaded from {gitignore_path}: {ignores}")
        except Exception as e:
            logger.error(f"Error reading {gitignore_path}: {e}")
    else:
        logger.warning(f"No .gitignore found at {gitignore_path}")
    if not patterns:
        patterns[base_path] = {
            "node_modules", ".git", ".expo", "android", "ios", "scripts",
            "dist", ".DS_Store", "*.log"
        }
        logger.info("Using fallback patterns")
    logger.info(f"Final .gitignore patterns: {patterns}")
    return patterns

@mcp.tool()
def generate_manifest(entry_point: str) -> dict:
    primary_entities = []
    shared_entities = []
    gitignore_patterns = load_gitignore_patterns(app_path)
    
    def crawl_tree(path: Path, depth=0):
        nonlocal primary_entities, shared_entities
        path_str = str(path)
        rel_path = os.path.relpath(path_str, app_path)
        
        if path.name.startswith("."):
            logger.debug(f"Skipping {rel_path} (hidden)")
            return
        
        logger.debug(f"Crawling: {path_str} (rel: {rel_path})")
        for git_dir, patterns in gitignore_patterns.items():
            git_dir_str = str(git_dir)
            rel_to_git = os.path.relpath(path_str, git_dir_str) if path_str.startswith(git_dir_str) else rel_path
            for pattern in patterns:
                if fnmatch.fnmatch(rel_path, pattern) or (rel_to_git != rel_path and fnmatch.fnmatch(rel_to_git, pattern)):
                    logger.debug(f"Skipping {rel_path} (matches {pattern} in {git_dir_str})")
                    return
        
        try:
            entries = list(path.iterdir())
            logger.debug(f"Found {len(entries)} entries in {rel_path}")
            entries.sort(key=lambda e: (not e.is_dir(), e.name.lower()))
            for entry in entries:
                entry_rel_path = os.path.relpath(entry, app_path)
                is_shared = "shared" in entry_rel_path.split(os.sep)
                if entry.is_dir():
                    crawl_tree(entry, depth + 1)
                elif entry.is_file() and not entry.name.startswith("."):
                    entity = {"path": entry_rel_path, "type": "file"}
                    if is_shared:
                        shared_entities.append(entity)
                    else:
                        primary_entities.append(entity)
                    logger.debug(f"Added entity: {entity['path']} (shared: {is_shared})")
        except Exception as e:
            logger.error(f"Error crawling {path_str}: {e}")
    
    corrected_entry = entry_point.replace("Codebase/components", "components")
    start_path = Path(app_path) / corrected_entry
    logger.info(f"Checking start path: {start_path} (exists: {start_path.exists()})")
    if not start_path.exists():
        logger.error(f"Entry point {entry_point} not found at {start_path}")
        return {"error": f"Entry point {entry_point} not found"}
    
    crawl_tree(start_path)
    manifest = {
        "feature": corrected_entry.split("/")[-1],
        "files": {
            "primary": primary_entities,
            "shared": shared_entities
        },
        "business_logic": {"constraints": ["placeholder"], "source": "TBD"}
    }
    logger.info(f"Generated manifest: {json.dumps(manifest, indent=2)}")
    return manifest

@mcp.tool()
def list_dir(path: str) -> dict:
    logger.info(f"Received list_dir request with path: {path}")
    corrected_path = path.replace("Codebase/components", "components")
    dir_path = Path(app_path) / corrected_path
    logger.info(f"Attempting to list: {dir_path} (exists: {dir_path.exists()})")
    logger.debug(f"Raw input path: {path}, Corrected path: {corrected_path}, Full path: {dir_path}")
    if not dir_path.exists():
        parent_path = Path(app_path) / "components"
        logger.info(f"Debug: Checking parent {parent_path} (exists: {parent_path.exists()})")
        if parent_path.exists():
            parent_entries = [{"name": e.name, "is_dir": e.is_dir()} for e in parent_path.iterdir() if not e.name.startswith(".")]
            logger.debug(f"Components dir contents: {parent_entries}")
        logger.error(f"Path {corrected_path} does not exist at {dir_path}")
        return {"error": f"Path {corrected_path} does not exist at {dir_path}"}
    if not dir_path.is_dir():
        logger.error(f"Path {corrected_path} is not a directory at {dir_path}")
        return {"error": f"Path {corrected_path} is not a directory at {dir_path}"}
    entries = []
    for entry in dir_path.iterdir():
        rel_path = os.path.relpath(entry, app_path)
        if entry.name.startswith("."):
            logger.debug(f"Skipping {rel_path} (hidden - {entry.is_dir() and 'dir' or 'file'})")
            continue
        entries.append({"name": entry.name, "is_dir": entry.is_dir()})
        logger.debug(f"Added entry: {entry.name} (is_dir: {entry.is_dir()})")
    logger.debug(f"Entries in {corrected_path}: {entries}")
    return {
        "entries": entries,
        "source": "server"  # Force Cascade to show server data
    }

@mcp.tool()
def check_root() -> dict:
    root_path = Path(app_path)
    logger.info(f"Checking root: {root_path} (exists: {root_path.exists()})")
    gitignore_patterns = load_gitignore_patterns(app_path)
    if not root_path.exists():
        logger.error(f"Root {app_path} does not exist")
        return {"error": f"Root {app_path} does not exist"}
    entries = []
    for entry in root_path.iterdir():
        rel_path = os.path.relpath(entry, app_path)
        if entry.name.startswith("."):
            logger.debug(f"Skipping {rel_path} (hidden - {entry.is_dir() and 'dir' or 'file'})")
            continue
        skip = False
        for git_dir, patterns in gitignore_patterns.items():
            git_dir_str = str(git_dir)
            rel_to_git = os.path.relpath(str(entry), git_dir_str) if str(entry).startswith(git_dir_str) else rel_path
            for pattern in patterns:
                if fnmatch.fnmatch(rel_path, pattern) or (rel_to_git != rel_path and fnmatch.fnmatch(rel_to_git, pattern)):
                    logger.debug(f"Skipping {rel_path} (matches {pattern} in {git_dir_str})")
                    skip = True
                    break
            if skip:
                break
        if not skip:
            entries.append({"name": entry.name, "is_dir": entry.is_dir()})
    logger.debug(f"Root entries: {entries}")
    return {"entries": entries}