import os
from pathlib import Path
from src.particle.particle_support import app_path, logger, load_gitignore_patterns
import fnmatch

def check_root() -> dict:
    root_path = Path(app_path)
    logger.info(f"Checking root: {root_path} (exists: {root_path.exists()})")
    gitignore_patterns = load_gitignore_patterns(app_path)
    if not root_path.exists():
        return {"error": f"Root {app_path} does not exist"}
    entries = []
    for entry in root_path.iterdir():
        rel_path = os.path.relpath(entry, app_path)
        if entry.name.startswith("."):
            logger.debug(f"Skipping {rel_path} (hidden)")
            continue
        skip = False
        for git_dir, patterns in gitignore_patterns.items():
            git_dir_str = str(git_dir)
            rel_to_git = os.path.relpath(str(entry), git_dir_str) if str(entry).startswith(git_dir_str) else rel_path
            for pattern in patterns:
                if fnmatch.fnmatch(rel_path, pattern) or (rel_to_git != rel_path and fnmatch.fnmatch(rel_to_git, pattern)):
                    skip = True
                    break
            if skip:
                break
        if not skip:
            entries.append({"name": entry.name, "is_dir": entry.is_dir()})
    logger.debug(f"Root entries: {entries}")
    return {"entries": entries}