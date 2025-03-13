import subprocess
import json
import os
from pathlib import Path

from src.core.file_handler import read_file, write_particle
from src.core.particle_utils import logger

PROJECT_ROOT = "/project"

def generate_particle(file_path: str = None, rich: bool = True) -> dict:
    """
    Generate Particle metadata for a single JavaScript/JSX file.
    
    Args:
        file_path: Path to the JS/JSX file to analyze (absolute or relative to PROJECT_ROOT)
        rich: If True, include detailed metadata including key_logic and depends_on
        
    Returns:
        dict: Result containing Particle data and operation status
    """
    logger.info(f"Starting generate particle with file_path: {file_path}")
    if not file_path:
        logger.error("No file_path provided to generate particle")
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
        node_path = str(absolute_path)
        cmd = ['node', '/app/js/babel_parser.js', node_path]
        env = os.environ.copy()
        if rich:
            env['RICH_PARSING'] = '1'
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, env=env)
        if not result.stdout.strip():
            logger.error(f"Empty output from Babel for {relative_path}")
            return {"error": "Babel produced empty output"}
        
        context = json.loads(result.stdout)
        filtered_context = {k: v for k, v in context.items() if v}  # Filter falsy values
        export_str, error = write_particle(relative_path, filtered_context)
        if error:
            return {"error": f"Write failed: {error}"}

        summary = (f"Found {len(filtered_context.get('props', []))} props, "
                  f"{len(filtered_context.get('hooks', []))} hooks, "
                  f"{len(filtered_context.get('calls', []))} calls")
        if rich:
            summary += (f", {len(filtered_context.get('logic', []))} logic, "
                       f"{len(filtered_context.get('depends_on', []))} deps")
        logger.info(f"Generated summary: {summary}")

        return {
            "content": [{"type": "text", "text": export_str}],
            "summary": summary,
            "status": "OK",
            "isError": False,
            "note": "Particle applied to file",
            "post_action": "read",
            "context": filtered_context  # Full rich output
        }
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Babel failed for {relative_path}: {e.stderr}")
        return {"error": f"Babel parse failed: {e.stderr}"}
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON from Babel for {relative_path}: {e}")
        return {"error": f"Invalid JSON: {e}"}
