import re
import json
from pathlib import Path
from particule_utils import app_path, logger

def validate_context(context):
    """Check if ContextParticule matches required structure."""
    required = {"purpose": str, "props": list, "hooks": list, "calls": list}
    optional = set(required.keys())
    if not isinstance(context, dict):
        return False, "Context must be a dictionary"
    if "purpose" not in context or not isinstance(context["purpose"], str):
        return False, "Missing or invalid 'purpose' (must be string)"
    for key, value in context.items():
        if key not in optional:
            return False, f"Unexpected field '{key}'"
        if key != "purpose" and not isinstance(value, list):
            return False, f"'{key}' must be a list"
    return True, "OK"

def generate_context(file_path: str, advanced: bool = False) -> dict:
    """Core logic for generating ContextParticule with options."""
    project_root = str(Path("/Users/Thy/Today"))
    if file_path.startswith(project_root):
        file_path = file_path[len(project_root) + 1:]
        logger.info(f"Converted absolute path to relative: {file_path}")
    elif file_path.startswith("/"):
        logger.error(f"Absolute path detected: {file_path} (use relative path from /project)")
        return {"error": f"Absolute path not supported: {file_path} (use relative path from /project, e.g., 'components/...')"}

    full_path = Path(app_path) / file_path
    logger.debug(f"Processing: {full_path} (raw: {file_path}, exists: {full_path.exists()})")
    
    if not full_path.exists():
        logger.error(f"File not found: {full_path} (expected relative path from /project, got: {file_path})")
        return {"error": f"File not found: {file_path} (use relative path from /project, e.g., 'components/...')"}

    try:
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
        logger.debug(f"File content read: {len(content)} chars")

        existing_match = re.search(r"export\s+const\s+ContextParticule\s*=\s*(\{.*?\});", content, re.DOTALL)
        if existing_match:
            logger.info(f"Existing ContextParticule found in {file_path}: {existing_match.group(1)}")
            return {
                "content": [{"type": "text", "text": "ContextParticule already exists; no changes made."}],
                "summary": "Skipped due to existing context",
                "isError": False
            }

        purpose = f"Manages {full_path.stem.lower()} functionality"
        if "guard" in full_path.stem.lower():
            purpose = f"Handles {full_path.stem.lower().replace('guard', '')}-based access control"
        if "auth" in full_path.stem.lower():
            purpose = "Manages authentication state by controlling access to protected routes"
        if "status" in full_path.stem.lower():
            purpose = "Renders event progress with male/female status"  # Sharper!

        props_match = re.search(r"function\s+\w+\s*\(\s*\{([^}]*)\}\s*(?::[^)]*)?\)\s*{|const\s+\w+\s*=\s*\(\s*\{([^}]*)\}\s*(?::[^)]*)?\)\s*=>", content, re.DOTALL)
        props = []
        if props_match:
            prop_str = props_match.group(1) or props_match.group(2)
            logger.debug(f"Props match: {prop_str}")
            for prop in prop_str.split(","):
                prop = prop.strip()
                if prop:
                    default_match = re.search(rf"{prop}\s*=\s*([^,\n]+)", prop_str)
                    desc = prop.split(":")[0].strip()
                    if default_match:
                        default_val = default_match.group(1).strip().replace("'", "\"")
                        desc += f" = {default_val}"
                    if advanced:
                        if "current" in desc or "min" in desc or "max" in desc:
                            desc += ": number"
                        elif "type" in desc:
                            desc += ": string"
                        elif "color" in desc:
                            if "styles.colors.darkBlue" in content:
                                desc += " = \"styles.colors.darkBlue\""
                            desc += ": string"
                        elif "direction" in desc:
                            desc += ": string"
                    props.append(desc)
        logger.debug(f"Extracted props: {props}")

        hooks = []
        hook_pattern = r"use[A-Z]\w*\("
        for line in content.splitlines():
            hook_matches = re.findall(hook_pattern, line)
            for hook in hook_matches:
                hook_name = hook.rstrip("(")
                hooks.append(hook_name if not advanced else f"{hook_name} - Fetches event display data" if "useEventDisplayState" in hook_name else f"{hook_name} - Custom hook")
        hooks = list(dict.fromkeys(hooks))
        logger.debug(f"Extracted hooks: {hooks}")

        calls = []
        for line in content.splitlines():
            if "fetch(" in line.lower():
                url = re.search(r"fetch\(['\"]([^'\"]+)['\"]", line)
                if url:
                    calls.append(url.group(1))
            if "supabase" in line.lower():
                if "signin" in line.lower():
                    calls.append("supabase.auth.signIn")
                elif "signout" in line.lower():
                    calls.append("supabase.auth.signOut")
            if "ismockenabled" in line.lower() and "ismockenabled()" not in hooks:
                calls.append("isMockEnabled()")
        calls = list(dict.fromkeys(calls))
        logger.debug(f"Extracted calls: {calls}")

        context = {"purpose": purpose}
        if props:
            context["props"] = props
        if hooks:
            context["hooks"] = hooks
        if calls:
            context["calls"] = calls

        # Format with indentation
        export_str = "export const ContextParticule = {\n"
        export_str += f"  \"purpose\": \"{context['purpose']}\",\n"
        if "props" in context:
            props_str = json.dumps(context["props"], ensure_ascii=False)
            export_str += f"  \"props\": {props_str},\n"
        if "hooks" in context:
            hooks_str = json.dumps(context["hooks"], ensure_ascii=False)
            export_str += f"  \"hooks\": {hooks_str}\n"
        if "calls" in context:
            calls_str = json.dumps(context["calls"], ensure_ascii=False)
            export_str += f"  \"calls\": {calls_str}\n"
        export_str = export_str.rstrip("\n").rstrip(",") + "\n};"

        summary = f"Found {len(props)} props, {len(hooks)} hooks, {len(calls)} calls"
        
        with open(full_path, "r+", encoding="utf-8") as f:
            content = f.read()
            if "export const ContextParticule" not in content:
                f.seek(0)
                f.write(export_str + "\n" + content)
                f.truncate()
                logger.info(f"Context applied to {file_path}: {export_str}")
            else:
                updated_content = re.sub(
                    r"export\s+const\s+ContextParticule\s*=\s*\{.*?\};",
                    export_str,
                    content,
                    flags=re.DOTALL
                )
                f.seek(0)
                f.write(updated_content)
                f.truncate()
                logger.info(f"Context updated in {file_path}: {export_str}")
            with open(full_path, "r", encoding="utf-8") as f_check:
                updated_content = f_check.read(500)
                logger.debug(f"Updated file content (preview): {updated_content}")

        logger.info(f"Generated and applied ContextParticule for {file_path} - {summary}")
        return {
            "content": [{"type": "text", "text": export_str}],
            "summary": summary,
            "status": "OK",
            "isError": False,
            "note": "Context applied directly to file",
            "post_action": "read"
        }

    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")
        return {"error": f"Error processing {file_path}: {str(e)}"}

def addContext(file_path: str) -> dict:
    """Standard ContextParticule with defaults."""
    return generate_context(file_path, advanced=False)

def addContextAdvanced(file_path: str) -> dict:
    """Advanced ContextParticule with types and enhanced hooks."""
    return generate_context(file_path, advanced=True)