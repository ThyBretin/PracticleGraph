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

    if file_path.startswith(PROJECT_ROOT):
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
        cmd = ['node', 'babel_parser.js', relative_path]  # Use relative_path
        logger.info(f"Executing subprocess: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            cwd="/app"
        )
        logger.debug(f"Babel stdout: {result.stdout}")
        logger.debug(f"Babel stderr: {result.stderr}")
        context = json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        logger.error(f"Babel failed for {relative_path}: {e.stderr}")
        return {"error": f"Babel parse failed: {e.stderr}"}
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON from Babel for {relative_path}: {e}")
        return {"error": f"Invalid JSON: {e}"}

    export_str, error = write_subparticule(relative_path, context)
    if error:
        logger.error(f"Write failed for {relative_path}: {error}")
        return {"error": f"Write failed: {error}"}

    props = context.get("props", [])
    hooks = context.get("hooks", [])
    calls = context.get("calls", [])
    key_logic = context.get("key_logic", [])
    depends_on = context.get("depends_on", [])

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

def addSubParticule(file_path: str = None, rich: bool = True) -> dict:
    return generate_subparticule(file_path, rich=rich)

def addAllSubParticule(root_dir: str = PROJECT_ROOT, rich: bool = True) -> dict:
    from pathlib import Path
    import pathspec

    logger.info(f"Starting addAllSubParticule for root_dir: {root_dir}")
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

    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith((".jsx", ".js")):
                file_path = Path(root) / file
                rel_path = file_path.relative_to(root_path)
                
                if gitignore.match_file(rel_path):
                    logger.debug(f"Skipped (gitignore): {rel_path}")
                else:
                    try:
                        result = generate_subparticule(str(file_path), rich)
                        if result.get("isError", True):
                            errors.append(f"{rel_path}: {result['error']}")
                        else:
                            modified_count += 1
                            logger.info(f"SubParticuled: {rel_path}")
                    except Exception as e:
                        errors.append(f"{rel_path}: {e}")

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