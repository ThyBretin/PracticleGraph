import json
import os
import fnmatch
from datetime import datetime
from pathlib import Path
from particule_utils import (
    app_path, logger, particule_cache, load_gitignore_patterns, infer_file_type,
    extract_particule_logic
)
from tech_stack import get_tech_stack

def createParticule(feature_path: str) -> dict: 
    """
    Create a Particule Graph for a feature.
    """
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
            logger.debug(f"Found {len(entries)} entries in {rel_path}: {[e.name for e in entries]}")
            entries.sort(key=lambda e: (not e.is_dir(), e.name.lower()))
            for entry in entries:
                entry_rel_path = os.path.relpath(entry, app_path)
                is_shared = "shared" in entry_rel_path.split(os.sep)
                if entry.is_dir():
                    crawl_tree(entry, depth + 1)
                elif entry.is_file() and not entry.name.startswith("."):
                    context = extract_particule_logic(entry_rel_path)
                    entity = {
                        "path": entry_rel_path,
                        "type": infer_file_type(entry_rel_path),
                    }
                    if context:
                        entity["context"] = context
                    # Filter out empty values
                    entity = {k: v for k, v in entity.items() if v is not None and v != []}
                    if is_shared:
                        shared_entities.append(entity)
                    else:
                        primary_entities.append(entity)
                    logger.debug(f"Added entity: {entity}")
        except Exception as e:
            logger.error(f"Error crawling {path_str}: {e}")
    
    start_path = Path(app_path) / feature_path
    logger.info(f"Starting crawl at: {start_path} (exists: {start_path.exists()})")
    if not start_path.exists():
        logger.error(f"Feature path {feature_path} not found at {start_path}")
        return {"error": f"Feature path {feature_path} not found"}
    
    crawl_tree(start_path)
    all_entities = primary_entities + shared_entities
    manifest = {
        "feature": feature_path.split("/")[-1].lower(),
        "last_crawled": datetime.utcnow().isoformat() + "Z",
        "tech_stack": get_tech_stack(all_entities),
        "files": {"primary": primary_entities, "shared": shared_entities}
    }
    particule_cache[manifest["feature"]] = manifest
    logger.info(f"Created manifest for {manifest['feature']}")
    return manifest