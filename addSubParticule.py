import re
from prop_parser import extract_props
from hook_analyzer import extract_hooks
from call_detector import extract_calls
from logic_inferer import extract_key_logic
from dependency_tracker import extract_dependencies
from context_builder import build_subparticule
from file_handler import read_file, write_subparticule  # Updated import
from particule_utils import logger

def generate_subparticule(file_path: str = None, rich: bool = True) -> dict:
    """
    Generate SubParticule for a given file.
    """
    if not file_path:
        return {"error": "No file_path provided"}

    content, error = read_file(file_path)
    if error:
        return error

    props = extract_props(content, rich)
    logger.debug(f"Extracted props: {props}")

    hooks = extract_hooks(content, rich)
    logger.debug(f"Extracted hooks: {hooks}")

    calls = extract_calls(content)
    logger.debug(f"Extracted calls: {calls}")

    key_logic = extract_key_logic(content, rich)
    logger.debug(f"Extracted key logic: {key_logic}")

    depends_on = extract_dependencies(hooks, content, rich)
    logger.debug(f"Extracted dependencies: {depends_on}")

    context = build_subparticule(file_path, content, props, hooks, calls, key_logic, depends_on, rich)
    
    export_str, error = write_subparticule(file_path, context)
    if error:
        return error

    summary = f"Found {len(props)} props, {len(hooks)} hooks, {len(calls)} calls"
    if rich:
        summary += f", {len(key_logic)} key logic, {len(depends_on)} dependencies"

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