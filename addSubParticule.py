import subprocess
from file_handler import read_file, write_subparticule
from particule_utils import logger
import json
import os
from pathlib import Path

PROJECT_ROOT = "/project"

def generate_subparticule(file_path: str = None, rich: bool = True) -> dict:
    logger.info(f"Starting generate_subparticule with file_path: {file_path}")
    if not file_path:
        logger.error("No file_path provided to generate_subparticule")
        return {"error": "No file_path provided"}

    # Handle paths that might contain the host machine path
    host_prefix = "/Users/Thy/Today/"
    if file_path.startswith(host_prefix):
        relative_path = file_path[len(host_prefix):]
        logger.warning(f"Converted host path '{file_path}' to relative: '{relative_path}'")
    elif file_path.startswith(PROJECT_ROOT):
        relative_path = file_path[len(PROJECT_ROOT) + 1:]  # Strip '/project/'
    else:
        relative_path = file_path

    absolute_path = Path(PROJECT_ROOT) / relative_path
    logger.debug(f"Computed relative_path: {relative_path}")
    logger.debug(f"Computed absolute_path: {absolute_path}")

    content, error = read_file(relative_path)
    if error:
        logger.error(f"File read failed for {relative_path}: {error}")
        return {"error": f"Read failed: {error}"}

    try:
        # Absolute path for Node.js to read from PROJECT_ROOT
        node_path = str(absolute_path) 
        cmd = ['node', '/app/babel_parser.js', node_path]
        logger.info(f"Executing subprocess: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        logger.debug(f"Babel stdout: {result.stdout}")
        logger.debug(f"Babel stderr: {result.stderr}")
        if not result.stdout.strip():
            logger.error(f"Empty output from Babel for {relative_path}")
            return {"error": "Babel produced empty output"}
        context = json.loads(result.stdout)
        
        # Filter out empty arrays before passing to write_subparticule
        filtered_context = {k: v for k, v in context.items() if not (isinstance(v, list) and len(v) == 0)}
        logger.debug(f"Filtered context (removed empty arrays): {json.dumps(filtered_context)}")
        
        export_str, error = write_subparticule(relative_path, filtered_context)
        if error:
            logger.error(f"Write failed for {relative_path}: {error}")
            return {"error": f"Write failed: {error}"}

        props = filtered_context.get("props", [])
        hooks = filtered_context.get("hooks", [])
        calls = filtered_context.get("calls", [])
        key_logic = filtered_context.get("key_logic", [])
        depends_on = filtered_context.get("depends_on", [])

        summary = f"Found {len(props)} props, {len(hooks)} hooks, {len(calls)} calls"
        if rich:
            summary += f", {len(key_logic)} key logic, {len(depends_on)} dependencies"
        logger.info(f"Generated summary: {summary}")

        return {
            "content": [{"type": "text", "text": export_str}],
            "summary": summary,
            "status": "OK",
            "isError": False,
            "note": "SubParticule applied directly to file",
            "post_action": "read"
        }

    except subprocess.CalledProcessError as e:
        logger.error(f"Babel failed for {relative_path}: {e.stderr}")
        return {"error": f"Babel parse failed: {e.stderr}"}
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON from Babel for {relative_path}: {e}")
        return {"error": f"Invalid JSON: {e}"}

def addSubParticule(file_path: str = None, rich: bool = True) -> dict:
    """
    Analyze a single file and add a SubParticule metadata export to it.
    
    This function parses a JavaScript/JSX file to extract component props, hooks,
    API calls, key logic, and dependencies, then writes this metadata back to the
    file as an 'export const SubParticule = {...}' statement.
    
    Unlike createParticule which creates a graph for an entire feature,
    addSubParticule focuses on a single file only.
    
    Args:
        file_path: Path to the JS/JSX file to analyze (absolute or relative to PROJECT_ROOT)
        rich: If True, include detailed metadata including key_logic and depends_on
        
    Returns:
        dict: Result containing the SubParticule data and operation status
    """
    logger.info(f"*** ADDSUB PARTICULE FUNCTION EXPLICITLY CALLED with {file_path} ***")
    return generate_subparticule(file_path, rich=rich)

def addAllSubParticule(root_dir: str = PROJECT_ROOT, rich: bool = True) -> dict:
    """
    Analyze all JavaScript/JSX files in a directory and add SubParticule metadata to each.
    
    This function recursively walks through the specified directory, finds all JS/JSX
    files, and adds SubParticule metadata to each file by calling generate_subparticule.
    It respects .gitignore files to skip files that should be ignored.
    
    Args:
        root_dir: Directory to process (absolute or relative to PROJECT_ROOT)
        rich: If True, include detailed metadata including key_logic and depends_on
        
    Returns:
        dict: Summary of operation with count of modified files and any errors
    """
    from pathlib import Path
    import pathspec

    logger.info(f"*** ADDALL SUBPARTICULE FUNCTION EXPLICITLY CALLED with root_dir: {root_dir} ***")
    
    # Handle paths that might contain the host machine path
    host_prefix = "/Users/Thy/Today"  # No trailing slash to match exact path too
    if root_dir == host_prefix or root_dir.startswith(host_prefix + "/"):
        logger.warning(f"Converting host path '{root_dir}' to container path '{PROJECT_ROOT}'")
        # If it's an exact match or has additional path components
        if root_dir == host_prefix:
            root_dir = PROJECT_ROOT
        else:
            # Extract the part after "/Users/Thy/Today/" and append to PROJECT_ROOT
            relative_part = root_dir[len(host_prefix) + 1:]  # +1 for the slash
            root_dir = os.path.join(PROJECT_ROOT, relative_part)
    elif root_dir != PROJECT_ROOT and not root_dir.startswith(PROJECT_ROOT):
        # If it's not already the project root and doesn't start with it,
        # treat it as a path relative to project root
        root_dir = os.path.join(PROJECT_ROOT, root_dir)
    
    logger.info(f"Using container path for processing: {root_dir}")

    def load_gitignore(root_dir):
        gitignore_path = Path(root_dir) / ".gitignore"
        if gitignore_path.exists():
            with open(gitignore_path, "r") as f:
                return pathspec.PathSpec.from_lines("gitwildmatch", f)
        return pathspec.PathSpec.from_lines("gitwildmatch", [])

    gitignore = load_gitignore(root_dir)
    root_path = Path(root_dir)
    modified_count = 0
    errors = []
    js_files_found = 0

    logger.info(f"Searching for JS/JSX files in {root_dir}")
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith((".jsx", ".js")):
                js_files_found += 1
                file_path = Path(root) / file
                rel_path = file_path.relative_to(root_path)
                logger.debug(f"Found JS/JSX file: {rel_path}")
                
                if gitignore.match_file(rel_path):
                    logger.debug(f"Skipped (gitignore): {rel_path}")
                else:
                    try:
                        result = generate_subparticule(str(file_path), rich)
                        if result.get("isError", True):
                            errors.append(f"{rel_path}: {result.get('error', 'Unknown error')}")
                        else:
                            modified_count += 1
                            logger.info(f"SubParticuled: {rel_path}")
                    except Exception as e:
                        errors.append(f"{rel_path}: {e}")

    if js_files_found == 0:
        logger.warning(f"No JS/JSX files found in {root_dir}")
    status = "OK" if not errors else "PARTIAL"
    summary = f"Modified {modified_count} files"
    if errors:
        summary += f", {len(errors)} errors: {', '.join(errors[:3])}" + (len(errors) > 3 and "..." or "")
    logger.info(f"addAllSubParticule summary: {summary}")

    return {
        "content": [{"type": "text", "text": summary}],
        "summary": summary,
        "status": status,
        "isError": len(errors) > 0,
        "note": f"SubParticules applied to {modified_count} files in {root_dir}"
    }

if __name__ == "__main__":
    addSubParticule("components/Features/Hub/components/shared/HubContent.jsx")