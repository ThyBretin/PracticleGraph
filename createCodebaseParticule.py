from pathlib import Path
import json
import fnmatch
import os
from datetime import datetime
from particule_utils import app_path, logger, particule_cache, load_gitignore_patterns
from particule_utils import extract_particule_logic
from tech_stack import get_tech_stack

def createCodebaseParticule() -> dict:
    """Create a Particule Graph for the entire codebase, respecting gitignore patterns."""
    logger.info("Creating codebase-wide Particule Graph (non-destructive)")
    
    root_dir = "/project"
    files = {}
    tech_stack = {"dependencies": {}, "devDependencies": {}}
    gitignore_patterns = load_gitignore_patterns(root_dir)
    
    root_path = Path(root_dir)
    file_count = 0
    js_files_total = 0
    
    # Initialize collections to prevent reference errors
    routes = {}
    data = {}
    components = {}
    
    # Collect all entities for tech stack analysis
    entities = []
    root_package_json = None
    
    try:
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
                rel_path_str = str(file_path.relative_to(root_path))
                
                # Special handling for root package.json - we'll use this for tech stack
                if filename == "package.json" and root == root_dir:
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            root_package_json = json.load(f)
                    except Exception as e:
                        logger.warning(f"Error parsing root package.json: {e}")
                    continue
                
                if not (filename.endswith(".js") or filename.endswith(".jsx")):
                    continue
                    
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
                    
                js_files_total += 1
                
                # Add to entities for tech stack analysis 
                entities.append({"path": rel_path_str, "type": "file"})
                
                particule_data = extract_particule_logic(rel_path_str)
                if particule_data:
                    particule_data = {k: v for k, v in particule_data.items() if v is not None and v != []}
                    files[rel_path_str] = particule_data
                    file_count += 1
                    
                    if 'app/(routes)/' in rel_path_str or 'app/(shared)/' in rel_path_str:
                        routes[rel_path_str] = particule_data
                    elif 'supabase' in rel_path_str or '.store' in rel_path_str:
                        data[rel_path_str] = particule_data
                    else:
                        components[rel_path_str] = particule_data
        
        # Process tech stack properly using root package.json and our tech_stack module
        if root_package_json:
            tech_stack = {
                "dependencies": root_package_json.get("dependencies", {}),
                "devDependencies": root_package_json.get("devDependencies", {})
            }
        
        # Use tech_stack.py to get organized tech stack if we have entities
        try:
            organized_tech_stack = get_tech_stack(entities) if entities else {}
        except Exception as e:
            logger.warning(f"Error organizing tech stack: {e}")
            organized_tech_stack = {}
        
        if file_count == 0:
            guidance = (
                "No SubParticule metadata found in codebase. To add metadata:\n"
                "1. Run 'addSubParticule(file_path)' on individual files\n"
                "2. Or run 'addAllSubParticule()' to process all JS/JSX files"
            )
            logger.warning(guidance)
            return {
                "content": [{"type": "text", "text": guidance}],
                "summary": "No SubParticules found in codebase",
                "status": "ERROR",
                "isError": True,
                "error": guidance
            }
        
        # Extract app story data safely with defensive programming
        try:
            route_data = []
            for file in files.values():
                calls = file.get("calls", [])
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
            
            # Safely process hooks and JSX data
            all_hooks = set()
            all_jsx = set()
            
            for file_data in files.values():
                hooks = file_data.get("hooks", [])
                jsx = file_data.get("jsx", [])
                for hook in hooks:
                    all_hooks.add(hook)
                for tag in jsx:
                    all_jsx.add(tag)
                    
            # Create patterns and JSX usage safely
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
        
        try:
            manifest = {
                "is_codebase": True,
                "last_crawled": datetime.utcnow().isoformat() + "Z",
                "tech_stack": organized_tech_stack or tech_stack,  # Use organized if available
                "app_story": app_story,
                "routes": routes if isinstance(routes, dict) else {},
                "data": data if isinstance(data, dict) else {},
                "components": components if isinstance(components, dict) else {},
                "file_count": file_count,
                "js_files_total": js_files_total,
                "coverage_percentage": round((file_count / js_files_total * 100) if js_files_total > 0 else 0, 2),
            }
        except Exception as e:
            logger.error(f"Error creating manifest: {e}")
            return {
                "content": [{"type": "text", "text": f"Error creating manifest: {e}"}],
                "summary": "Error creating manifest",
                "status": "ERROR",
                "isError": True,
                "error": f"Error creating manifest: {e}"
            }
        
        particule_cache["__codebase__"] = manifest
        
        logger.info(f"Created codebase-wide Particule Graph with {file_count}/{js_files_total} files ({manifest['coverage_percentage']}% coverage)")
        summary = f"Created codebase Particule containing metadata for {file_count} files (out of {js_files_total} JS/JSX files)"
        
        return {
            "content": [{"type": "text", "text": summary}],
            "summary": summary,
            "status": "OK",
            "isError": False
        }
    except Exception as e:
        error_msg = f"Error creating codebase Particule: {str(e)}"
        logger.error(error_msg)
        return {
            "content": [{"type": "text", "text": error_msg}],
            "summary": "Error creating codebase Particule",
            "status": "ERROR",
            "isError": True,
            "error": error_msg
        }