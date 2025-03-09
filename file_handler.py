import re
from pathlib import Path
from particule_utils import app_path, logger

def read_file(file_path: str) -> tuple[str, dict]:
    """Read file content or return an error."""
    project_root = str(Path("/Users/Thy/Today"))  # Adjust if your root differs
    if file_path.startswith(project_root):
        old_path = file_path
        file_path = file_path[len(project_root) + 1:]  # Strip root and separator
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
        return None, {"error": f"Got a directory: {file_path}. Use createParticule for directories."}

    with open(full_path, "r", encoding="utf-8") as f:
        content = f.read()
    logger.debug(f"File content read: {len(content)} chars")
    return content, None

def write_subparticule(file_path: str, context: dict) -> tuple[str, dict]:
    """Write SubParticule export to file, updating if it exists."""
    project_root = str(Path("/Users/Thy/Today"))
    if file_path.startswith(project_root):
        old_path = file_path
        file_path = file_path[len(project_root) + 1:]
        logger.warning(f"Converted absolute path '{old_path}' to relative: '{file_path}'")
    elif file_path.startswith("/"):
        logger.error(f"Absolute path detected: {file_path} (use relative path from /project)")
        return None, {"error": f"Absolute path not supported: {file_path} (use relative path from /project)"}

    full_path = Path(app_path) / file_path
    export_str = "export const SubParticule = {\n"
    for key, value in context.items():
        if key == "purpose" or isinstance(value, str):
            export_str += f'  "{key}": "{value}",\n'
        else:
            value_str = str(value).replace("'", '"')  # Simple JSON-like format
            export_str += f'  "{key}": {value_str},\n'
    export_str = export_str.rstrip("\n").rstrip(",") + "\n};"

    with open(full_path, "r", encoding="utf-8") as f:
        content = f.read()

    if "export const SubParticule" in content:
        updated_content = re.sub(
            r"export\s+const\s+SubParticule\s*=\s*\{.*?\};",
            export_str,
            content,
            flags=re.DOTALL
        )
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(updated_content)
        logger.info(f"SubParticule updated in {file_path}")
    else:
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(export_str + "\n\n" + content)
        logger.info(f"SubParticule added to {file_path}")

    return export_str, None