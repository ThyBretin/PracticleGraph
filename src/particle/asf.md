hold on, I need to collect other files :

so dependency tracker is hardcoded 
Metadata_extractor.js is hard coded - line 202 to 215 
Particle Generator seems fine.
and particle_support.py looks fine also but will help you to understand the logic . 

The Particle it self with all it's field is sound....But because we previously hard coded some of it, I find a way to counter act the hard coding, that must be get rid off, by creating ParticleThis() Which should provide accuracy and more explicit definition to hooks, functions.... 

Sorry, I'm not a dev, I have a goal, but you surely have a better understand of this than myself...Maybe we can start by reference what is doing what : ie :

                    "purpose": context.get("purpose", ""),
                    "props": context.get("props", []),
                    "hooks": context.get("hooks", []),
                    "calls": context.get("calls", []),
                    "key_logic": context.get("key_logic", []),
                    "depends_on": context.get("depends_on", [])
props, 
comments.... 
 

This is particle_support.py: 

import json
import logging
import os
import re
import fnmatch
from pathlib import Path
from typing import Dict, List, Set, Optional

app_path = os.getenv("PARTICLE_PATH", "/project")
particle_cache: Dict[str, dict] = {}
logger = logging.getLogger("ParticleGraph")

def infer_file_type(file_path: str) -> str:
    ext = Path(file_path).suffix.lower()
    if "test" in file_path.lower():
        return "test"
    if ext in (".jsx", ".tsx"):
        return "file"
    if "store" in file_path.lower():
        return "store"
    if "context" in file_path.lower():
        return "state"
    return "file"

def extract_particle_logic(file_path: str) -> dict:
    """Extract structured context (purpose, props, calls) from a file's Particle export."""
    full_path = Path(app_path) / file_path
    if not full_path.exists() or full_path.is_dir():
        return None
    
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Parse export const Particle
        context_match = re.search(r"export\s+const\s+Particle\s*=\s*(\{.*?\});", content, re.DOTALL)
        if context_match:
            try:
                context_str = context_match.group(1).replace("'", '"')
                context = eval(context_str, {"__builtins__": {}})
                return {
                    "purpose": context.get("purpose", ""),
                    "props": context.get("props", []),
                    "hooks": context.get("hooks", []),
                    "calls": context.get("calls", []),
                    "key_logic": context.get("key_logic", []),
                    "depends_on": context.get("depends_on", [])
                }
            except Exception as e:
                logger.debug(f"Invalid Particle in {file_path}: {e}")

        # Fallback: Infer from code
        context = {"purpose": "", "props": [], "hooks": [], "calls": []}
        # Props
        props = re.findall(r"const\s+\w+\s*=\s*\(\{([^}]*)\}\)", content)
        if props:
            context["props"] = [p.strip() for p in props[0].split(",") if p.strip()]
        for line in content.splitlines():
            if "fetch(" in line:
                url = re.search(r"fetch\(['\"]([^'\"]+)['\"]", line)
                if url:
                    context["calls"].append(url.group(1))
            if "supabase" in line:
                if "signIn" in line:
                    context["calls"].append("supabase.auth.signIn")
                elif "signOut" in line:
                    context["calls"].append("supabase.auth.signOut")
        return context if any(context.values()) else None

    except Exception as e:
        logger.debug(f"Error reading {file_path}: {e}")
        return None

# Drop extract_api_calls since it's merged

This is particle_generator.py : 
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


 