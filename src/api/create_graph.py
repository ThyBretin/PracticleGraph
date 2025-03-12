import json
import os
import fnmatch
from datetime import datetime
from pathlib import Path

from src.core.particle_utils import (
    app_path, logger, particle_cache, load_gitignore_patterns, infer_file_type,
    extract_particle_logic
)
from src.analysis.tech_stack import get_tech_stack

def createGraph(path: str) -> dict:
    """
    Create a Particle Graph for a feature or the entire codebase.
    
    Args:
        path: Path to create graph for, relative to app_path
              Special values: "all" or "codebase" to create a graph for the entire codebase
    
    Returns:
        dict: The created graph manifest
    """
    logger.info(f"Creating Particle Graph for: {path}")
    
    # Check if we should crawl the entire codebase or a specific path
    is_codebase = path.lower() in ("all", "codebase")
    root_dir = "/project" if is_codebase else os.path.join(app_path, path)
    
    # Initialize collections
    files = {}
    entities = []
    root_package_json = None
    routes = {}
    data = {}
    components = {}
    primary_entities = []
    shared_entities = []
    
    # Load gitignore patterns
    gitignore_patterns = load_gitignore_patterns(app_path if not is_codebase else root_dir)
    
    # Initialize counters
    file_count = 0
    js_files_total = 0
    
    # Check if path exists
    root_path = Path(root_dir)
    if not root_path.exists():
        error_msg = f"Path {path} not found at {root_path}"
        logger.error(error_msg)
        return {"error": error_msg}
    
    try:
        # For feature-specific processing, use depth-first directory crawling
        if not is_codebase:
            def crawl_tree(path: Path, depth=0):
                nonlocal primary_entities, shared_entities, file_count, js_files_total
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
                            # Count JS files for stats
                            if entry.name.endswith((".js", ".jsx")):
                                js_files_total += 1
                                
                            # Extract particle logic
                            context = extract_particle_logic(entry_rel_path)
                            if context:
                                file_count += 1
                                
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
                                
                            # Add to entities for tech stack analysis
                            entities.append(entity)
                            
                            logger.debug(f"Added entity: {entity}")
                except Exception as e:
                    logger.error(f"Error crawling {path_str}: {e}")
            
            # Start crawling from the provided path
            crawl_tree(root_path)
            
        # For codebase-wide processing, use os.walk
        else:
            for root, _, filenames in os.walk(root_dir):
                root_path_str = str(Path(root))
                should_ignore_dir = False
                for git_dir, patterns in gitignore_patterns.items():
                    git_dir_str = str(git_dir)
                    if not root_path_str.startswith(git_dir_str):
                        continue
                    rel_to_git = os.path.relpath(root_path_str, git_dir_str)
                    for pattern in patterns:
                        if fnmatch.fnmatch(rel_to_git, pattern) or pattern == rel_to_git:
                            should_ignore_dir = True
                            break
                    if should_ignore_dir:
                        break
                if should_ignore_dir:
                    continue
                    
                for filename in filenames:
                    file_path = Path(root) / filename
                    
                    # Handle codebase-specific path relativity
                    rel_path_str = str(file_path.relative_to(root_path))
                    
                    # Special handling for root package.json
                    if filename == "package.json" and root == root_dir:
                        try:
                            with open(file_path, "r", encoding="utf-8") as f:
                                root_package_json = json.load(f)
                        except Exception as e:
                            logger.warning(f"Error parsing root package.json: {e}")
                        continue
                    
                    # Skip non-JS/JSX files for codebase-wide analysis
                    if not (filename.endswith(".js") or filename.endswith(".jsx")):
                        continue
                        
                    # Check gitignore patterns
                    should_ignore_file = False
                    for git_dir, patterns in gitignore_patterns.items():
                        git_dir_str = str(git_dir)
                        if not str(file_path).startswith(git_dir_str):
                            continue
                        rel_to_git = os.path.relpath(str(file_path), git_dir_str)
                        for pattern in patterns:
                            if fnmatch.fnmatch(rel_path_str, pattern) or fnmatch.fnmatch(rel_to_git, pattern) or 'node_modules' in rel_path_str:
                                should_ignore_file = True
                                break
                        if should_ignore_file:
                            break
                            
                    if should_ignore_file:
                        continue
                        
                    # Count JS files
                    js_files_total += 1
                    
                    # Add to entities for tech stack analysis 
                    entity = {"path": rel_path_str, "type": "file"}
                    entities.append(entity)
                    
                    # Extract particle data
                    particle_data = extract_particle_logic(rel_path_str)
                    if particle_data:
                        particle_data = {k: v for k, v in particle_data.items() if v is not None and v != []}
                        files[rel_path_str] = particle_data
                        file_count += 1
                        
                        # Categorize files for codebase-wide graph
                        if 'app/(routes)/' in rel_path_str or 'app/(shared)/' in rel_path_str:
                            routes[rel_path_str] = particle_data
                        elif 'supabase' in rel_path_str or '.store' in rel_path_str:
                            data[rel_path_str] = particle_data
                        else:
                            components[rel_path_str] = particle_data
                            
                        # Also track by primary/shared
                        is_shared = "shared" in rel_path_str.split(os.sep)
                        entity_with_context = {
                            "path": rel_path_str,
                            "type": infer_file_type(rel_path_str),
                            "context": particle_data
                        }
                        if is_shared:
                            shared_entities.append(entity_with_context)
                        else:
                            primary_entities.append(entity_with_context)
        
        # No files found case
        if file_count == 0:
            guidance = (
                "No Particle metadata found. To add metadata:\n"
                "1. Run 'addParticle(file_path)' on individual files\n"
                "2. Or run 'addParticle(path, recursive=True)' to process all JS/JSX files"
            )
            logger.warning(guidance)
            return {
                "content": [{"type": "text", "text": guidance}],
                "summary": "No Particles found",
                "status": "ERROR",
                "isError": True,
                "error": guidance
            }
        
        # Process tech stack
        tech_stack = {}
        if is_codebase and root_package_json:
            tech_stack = {
                "dependencies": root_package_json.get("dependencies", {}),
                "devDependencies": root_package_json.get("devDependencies", {})
            }
        
        try:
            organized_tech_stack = get_tech_stack(entities)
        except Exception as e:
            logger.warning(f"Error organizing tech stack: {e}")
            organized_tech_stack = {}
        
        # For codebase-wide graph, extract app story
        app_story = None
        if is_codebase:
            try:
                route_data = []
                for file_data in files.values():
                    calls = file_data.get("calls", [])
                    for call in calls:
                        if "router.push" in call or "navigateToTab" in call:
                            try:
                                # Default to just storing the call itself
                                route_to_add = "router.push"
                                
                                # Try to extract route path
                                if "'" in call:
                                    parts = call.split("'")
                                    if len(parts) > 1:
                                        route_to_add = parts[1]
                                elif '"' in call:
                                    parts = call.split('"')
                                    if len(parts) > 1:
                                        route_to_add = parts[1]
                                
                                # Add to route data
                                route_data.append(route_to_add)
                            except Exception as e:
                                logger.warning(f"Error processing route call {call}: {e}")
                                # Fallback to a safe default
                                route_data.append("router.push")
                
                # Process hooks and JSX data
                all_hooks = set()
                all_jsx = set()
                
                for file_data in files.values():
                    hooks = file_data.get("hooks", [])
                    jsx = file_data.get("jsx", [])
                    for hook in hooks:
                        all_hooks.add(hook)
                    for tag in jsx:
                        all_jsx.add(tag)
                        
                # Create patterns and JSX usage
                patterns = {}
                jsx_usage = {}
                
                for hook in all_hooks:
                    hook_count = 0
                    for file_data in files.values():
                        if hook in file_data.get("hooks", []):
                            hook_count += 1
                    patterns[hook] = hook_count
                    
                for tag in all_jsx:
                    tag_count = 0
                    for file_data in files.values():
                        if tag in file_data.get("jsx", []):
                            tag_count += 1
                    jsx_usage[tag] = tag_count
                    
                app_story = {
                    "routes": route_data,
                    "patterns": patterns,
                    "jsx_usage": jsx_usage
                }
            except Exception as e:
                logger.warning(f"Error building app_story: {e}")
                app_story = {
                    "routes": [],
                    "patterns": {},
                    "jsx_usage": {}
                }
        
        # Calculate coverage percentage
        coverage_percentage = round((file_count / js_files_total * 100) if js_files_total > 0 else 0, 2)
        
        # Create the appropriate manifest based on what we're processing
        if is_codebase:
            manifest = {
                "is_codebase": True,
                "last_crawled": datetime.utcnow().isoformat() + "Z",
                "tech_stack": organized_tech_stack or tech_stack,
                "app_story": app_story,
                "routes": routes if isinstance(routes, dict) else {},
                "data": data if isinstance(data, dict) else {},
                "components": components if isinstance(components, dict) else {},
                "file_count": file_count,
                "js_files_total": js_files_total,
                "coverage_percentage": coverage_percentage,
            }
            # Store in cache
            particle_cache["__codebase__"] = manifest
        else:
            manifest = {
                "feature": path.split("/")[-1].lower(),
                "last_crawled": datetime.utcnow().isoformat() + "Z",
                "tech_stack": organized_tech_stack or tech_stack,
                "files": {"primary": primary_entities, "shared": shared_entities},
                "file_count": file_count,
                "js_files_total": js_files_total,
                "coverage_percentage": coverage_percentage
            }
            # Store in cache
            particle_cache[manifest["feature"]] = manifest
        
        # Create success message
        if is_codebase:
            summary = f"Created codebase Particle containing metadata for {file_count} files (out of {js_files_total} JS/JSX files)"
        else:
            summary = f"Created Particle for {path} with {file_count} files (out of {js_files_total} JS/JSX files)"
        
        logger.info(f"{summary} ({coverage_percentage}% coverage)")
        
        return {
            "content": [{"type": "text", "text": summary}],
            "summary": summary,
            "status": "OK",
            "isError": False,
            "manifest": manifest
        }
        
    except Exception as e:
        error_msg = f"Error creating Particle Graph: {str(e)}"
        logger.error(error_msg)
        return {
            "content": [{"type": "text", "text": error_msg}],
            "summary": "Error creating Particle Graph",
            "status": "ERROR",
            "isError": True,
            "error": error_msg
        }