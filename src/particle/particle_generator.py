import subprocess
import json
import os
import hashlib
from pathlib import Path

from src.particle.file_handler import read_file, write_particle
from src.particle.particle_support import logger

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
        return {"error": "No file_path provided", "isError": True}

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
        return {"error": f"Read failed: {error}", "isError": True}

    # Generate file hash for freshness checking
    file_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
    logger.debug(f"Generated MD5 hash for {relative_path}: {file_hash}")

    try:
        node_path = str(absolute_path)
        # Step 1: Generate AST with babel_parser_core.js
        cmd = ['node', '/app/src/particle/js/babel_parser_core.js', node_path]
        env = os.environ.copy()
        env['RICH_PARSING'] = '1'
        ast_result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        if not ast_result.stdout.strip():
            logger.error(f"Empty AST output from Babel for {relative_path}")
            return {"error": "Babel AST generation produced empty output", "isError": True}
        ast_data = json.loads(ast_result.stdout)
        
        # Step 2: Extract metadata with metadata_extractor.js
        cmd = ['node', '/app/src/particle/js/metadata_extractor.js', node_path]
        result = subprocess.run(
            cmd,
            input=json.dumps(ast_data['ast']),
            capture_output=True,
            text=True,
            check=True,
            env=env
        )
        if not result.stdout.strip():
            logger.error(f"Empty metadata output from Babel for {relative_path}")
            return {"error": "Babel metadata extraction produced empty output", "isError": True}
        
        context = json.loads(result.stdout)
        filtered_context = {k: v for k, v in context.items() if v}  # Filter falsy values
        
        # Add file hash to the particle metadata for freshness checking
        filtered_context['file_hash'] = file_hash
        
        # Write particle to cache as JSON
        cache_path, error = write_particle(relative_path, filtered_context)
        if error:
            return {"error": f"Write failed: {error}", "isError": True}

        # Generate summary
        summary_fields = []
        attrs = filtered_context.get('attributes', {})
        for field_name, display_name in [
            ('props', 'props'),
            ('hooks', 'hooks'),
            ('calls', 'calls'),
            ('logic', 'logic conditions'),
            ('depends_on', 'dependencies'),
            ('jsx', 'JSX elements'),
            ('routes', 'routes'),
            ('comments', 'comments')
        ]:
            if field_name in attrs:
                count = len(attrs[field_name])
                if count > 0:
                    summary_fields.append(f"{count} {display_name}")
        
        if 'state_machine' in attrs:
            states_count = len(attrs['state_machine'].get('states', []))
            if states_count > 0:
                summary_fields.append(f"state machine with {states_count} states")
        
        summary = ", ".join(summary_fields) or "No significant elements found"
        logger.info(f"Generated summary: {summary}")

        return {
            "content": [{"type": "text", "text": f"Particle generated for {relative_path}: {summary}"}],
            "status": "OK",
            "isError": False,
            "note": "Particle cached at " + cache_path,
            "post_action": "read",
            "particle": filtered_context
        }
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Babel failed for {relative_path}: {e.stderr}")
        return {"error": f"Babel parse failed: {e.stderr}", "isError": True}
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON from Babel for {relative_path}: {e}")
        return {"error": f"Invalid JSON: {e}", "isError": True}