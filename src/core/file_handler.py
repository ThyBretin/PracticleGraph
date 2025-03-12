import re
import json
from pathlib import Path
from src.core.particle_utils import app_path, logger

def read_file(file_path: str) -> tuple[str, dict]:
    """Read file content or return an error."""
    project_root = str(Path("/Users/Thy/Today"))
    if file_path.startswith(project_root):
        old_path = file_path
        file_path = file_path[len(project_root) + 1:]
        logger.warning(f"Converted absolute path '{old_path}' to relative: '{file_path}'")
    elif file_path.startswith("/"):
        logger.error(f"Absolute path detected: {file_path} (use relative path from /project)")
        return None, {"error": f"Absolute path not supported: {file_path} (use relative path from /project)"}

    full_path = Path(app_path) / file_path
    logger.debug(f"Processing: {full_path} (raw: {file_path}, exists: {full_path.exists()})")

    if not full_path.exists():
        logger.error(f"File not found: {full_path}")
        return None, {"error": f"File not found: {full_path}"}
    if full_path.is_dir():
        logger.error(f"Directory detected: {full_path} (expected a file)")
        return None, {"error": f"Got a directory: {file_path}. Use createParticle for directories."}

    with open(full_path, "r", encoding="utf-8") as f:
        content = f.read()
    logger.debug(f"File content read: {len(content)} chars")
    return content, None

def write_particle(file_path: str, context: dict) -> tuple[str, dict]:
    """Write Particle export to file, updating if it exists."""
    project_root = str(Path("/Users/Thy/Today"))
    if file_path.startswith(project_root):
        old_path = file_path
        file_path = file_path[len(project_root) + 1:]
        logger.warning(f"Converted absolute path '{old_path}' to relative: '{file_path}'")
    elif file_path.startswith("/"):
        logger.error(f"Absolute path detected: {file_path} (use relative path from /project)")
        return None, {"error": f"Absolute path not supported: {file_path} (use relative path from /project)"}

    full_path = Path(app_path) / file_path
    
    # Remove empty arrays from context
    filtered_context = {k: v for k, v in context.items() if not (isinstance(v, list) and len(v) == 0)}
    logger.debug(f"Filtered {len(context) - len(filtered_context)} empty arrays from Particle")
    
    # Use json.dumps for valid formatting
    try:
        export_str = f"export const Particle = {json.dumps(filtered_context, indent=2, ensure_ascii=False)};"
        # Validate it
        json.loads(export_str.split("=", 1)[1].rstrip(";"))
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON generated for {file_path}: {e}")
        return None, {"error": f"Invalid JSON: {e}"}

    with open(full_path, "r", encoding="utf-8") as f:
        content = f.read()

    if "export const Particle" in content:
        updated_content = re.sub(
            r"export\s+const\s+Particle\s*=\s*\{.*?\};",
            export_str,
            content,
            flags=re.DOTALL
        )
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(updated_content)
        logger.info(f"Particle updated in {file_path}")
    else:
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(export_str + "\n\n" + content)
        logger.info(f"Particle added to {file_path}")

    return export_str, None