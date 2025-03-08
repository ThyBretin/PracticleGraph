import re
import json
import time
from pathlib import Path
from particule_utils import app_path, logger
from lark import Lark

# Lark grammar for props parsing
grammar = r"""
    ?start: func_def
    func_def: "export"? "const" NAME "=" "(" params ")" "=>" | "export"? "function" NAME "(" params ")" "{"
    params: "{" inner_params "}"
    inner_params: param ("," param)*
    param: NAME ("=" VALUE)?
    NAME: /[a-zA-Z_][a-zA-Z0-9_]*/
    VALUE: /[^,}]+/
    WS: /[ \t\f\r\n]+/
    %ignore WS
"""
parser = Lark(grammar, parser='lalr')  # Initialize Lark parser

def extract_props(content, rich=True):
    try:
        # First attempt to parse props from function signature
        tree = parser.parse(content.split("{", 2)[0] + "{")  # Stop at second { for function body
        logger.debug(f"Lark parse tree: {tree.pretty()}")
        props = []
        for param in tree.find_data("param"):
            name = param.children[0].value
            default = param.children[1].value.strip().replace("'", '"') if len(param.children) > 1 else None
            desc = name + (f" = {default}" if default else "")
            if rich:
                if "current" in desc or "min" in desc or "max" in desc:
                    desc += ": number"
                elif any(x in desc for x in ["type", "route", "icon", "activeIcon", "label"]):
                    desc += ": string"
                elif "color" in desc or "direction" in desc:
                    desc += ": string"
                elif "children" in desc:
                    desc += ": ReactNode"
                elif "requireAuth" in desc:
                    desc += ": boolean"
            props.append(desc)
        
        # If no props found in the signature, or if we want to be more thorough,
        # look for props in the JSX and variable declarations
        if not props or rich:
            # Extract from JSX attributes
            jsx_props = re.findall(r"<[^>]+?\s+([a-zA-Z][a-zA-Z0-9]*)=[{'\"]", content)
            
            # Extract from destructuring assignments
            destructured_props = []
            destructure_matches = re.findall(r"const\s*{\s*([^}]+)\s*}\s*=\s*props", content)
            if destructure_matches:
                for match in destructure_matches:
                    parts = re.split(r',\s*', match)
                    for part in parts:
                        # Handle renaming in destructuring: { oldName: newName }
                        prop_match = re.search(r'^([^:]+)(?::\s*([^=]+))?', part.strip())
                        if prop_match:
                            prop_name = prop_match.group(1).strip()
                            destructured_props.append(prop_name)
            
            # Extract from props access (props.something)
            props_access = re.findall(r'props\.([a-zA-Z][a-zA-Z0-9]*)', content)
            
            # Extract from table definitions (objects that likely contain prop definitions)
            # This is useful for components that define their props in a schema
            tab_items = re.findall(r'{\s*name:\s*[\'"]([^\'"]+)[\'"]', content)
            
            # Combine all found props
            all_props = set(jsx_props + destructured_props + props_access + tab_items)
            seen = set(props)  # Track props we've already added from signature parsing
            
            for prop in all_props:
                if prop and prop not in ["className", "style", "key", "ref"] and prop not in seen:
                    desc = prop
                    if rich:
                        if prop.lower() in ["icon", "activeicon"]:
                            desc += ": string"
                        elif prop.lower() in ["label", "name", "type", "title"]:
                            desc += ": string"
                        elif prop.lower() in ["active", "selected", "disabled", "isactive"]:
                            desc += ": boolean"
                        elif prop.lower() in ["onpress", "onclick", "onchange"]:
                            desc += ": function"
                        elif prop.lower() in ["style", "customstyle"]:
                            desc += ": object"
                    props.append(desc)
                    seen.add(prop)
        
        # Analyze data structures that might define props
        tab_structures = re.findall(r'(\w+):\s*\[\s*{\s*([^}]+)\s*}', content, re.DOTALL)
        for struct_name, struct_content in tab_structures:
            # Extract keys from the structure content
            keys = re.findall(r'(\w+):\s*[\'"][^\'"]+[\'"]', struct_content)
            for key in keys:
                if key and key not in ["className", "style", "key", "ref"] and key not in seen:
                    desc = key
                    if rich:
                        if key.lower() in ["icon", "activeicon", "label", "name"]:
                            desc += ": string"
                    props.append(desc)
                    seen.add(key)
        
        return list(dict.fromkeys(props))  # Dedupe
    except Exception as e:
        logger.debug(f"Lark parse failed: {e}")
        # Fallback to regex-only approach if parsing fails
        props = []
        seen = set()
        
        # Extract from JSX attributes
        jsx_props = re.findall(r"<[^>]+?\s+([a-zA-Z][a-zA-Z0-9]*)=[{'\"]", content)
        
        # Extract properties from object definitions
        obj_props = re.findall(r'{\s*(\w+):\s*[\'"][^\'"]+[\'"]', content)
        
        # Combine all found props
        all_props = set(jsx_props + obj_props)
        
        for prop in all_props:
            if prop and prop not in ["className", "style", "key", "ref"] and prop not in seen:
                desc = prop
                if rich:
                    if any(x in prop.lower() for x in ["icon", "activeicon", "label", "name"]):
                        desc += ": string"
                    elif prop.lower() in ["active", "selected", "disabled"]:
                        desc += ": boolean"
                props.append(desc)
                seen.add(prop)
        
        return list(dict.fromkeys(props))  # Dedupe

def validate_context(context):
    """Check if SubParticule matches required structure."""
    required = {"purpose": str, "props": list, "hooks": list, "calls": list}
    optional = {"purpose", "props", "hooks", "calls", "key_logic", "depends_on"}
    if not isinstance(context, dict):
        return False, "SubParticule must be a dictionary"
    if "purpose" not in context or not isinstance(context["purpose"], str):
        return False, "Missing or invalid 'purpose' (must be string)"
    for key, value in context.items():
        if key not in optional:
            return False, f"Unexpected field '{key}'"
        if key != "purpose" and key != "key_logic" and not isinstance(value, list):
            return False, f"'{key}' must be a list"
    return True, "OK"

def infer_hook_purpose(hook_name: str, content: str) -> str:
    """Hybrid: Predefined for common hooks, contextual for customs."""
    predefined = {
        "useState": f"{hook_name} - Manages component state",
        "useEffect": f"{hook_name} - Handles side effects on mount/update",
        "useContext": f"{hook_name} - Accesses app-wide context",
        "useReducer": f"{hook_name} - Manages complex state logic",
        "useCallback": f"{hook_name} - Memoizes functions",
        "useMemo": f"{hook_name} - Memoizes values",
        "useRef": f"{hook_name} - Persists mutable references",
        "useRouter": f"{hook_name} - Expo Router hook for navigation",
        "useSegments": f"{hook_name} - Expo Router hook for route segments",
        "useAuth": f"{hook_name} - Manages authentication state",
        "useEventDisplayState": f"{hook_name} - Fetches event display data",
        "useRole": f"{hook_name} - Manages authentication state",
        "useNavigation": f"{hook_name} - Controls navigation",
        "useScrollValue": f"{hook_name} - Manages scroll state",
        "useDerivedValue": f"{hook_name} - Computes derived values",
        "useAnimatedStyle": f"{hook_name} - Manages animated styles"
    }
    if hook_name in predefined:
        return predefined[hook_name]

    hook_lower = hook_name.lower()
    if "state" in hook_lower:
        return f"{hook_name} - Manages local state"
    if "effect" in hook_lower:
        return f"{hook_name} - Handles side effects"
    if "fetch" in hook_lower or "data" in hook_lower:
        return f"{hook_name} - Fetches data"
    if "auth" in hook_lower or "login" in hook_lower:
        return f"{hook_name} - Handles authentication logic"
    if "route" in hook_lower or "nav" in hook_lower:
        return f"{hook_name} - Controls navigation"

    lines = content.splitlines()
    for i, line in enumerate(lines):
        if hook_name in line:
            context_lines = lines[max(0, i-2):i+3]
            context_text = " ".join(context_lines).lower()
            if "set" in context_text or "state" in context_text:
                return f"{hook_name} - Manages local state"
            if "fetch" in context_text or "api" in context_text:
                return f"{hook_name} - Fetches data"
            if "navigate" in context_text or "push" in context_text:
                return f"{hook_name} - Controls navigation"
            if "auth" in context_text or "session" in context_text:
                return f"{hook_name} - Handles authentication logic"

    return f"{hook_name} - Manages local state or effects"

def generate_subparticule(file_path: str = None, rich: bool = True) -> dict:
    """Generate SubParticule for active file or given path, with optional rich mode."""
    time.sleep(0.1)  # Avoid I/O pileup

    if not file_path:
        return {"error": "No file_path provided—active file detection not yet implemented"}

    project_root = str(Path("/Users/Thy/Today"))
    if file_path.startswith(project_root):
        old_path = file_path
        file_path = file_path[len(project_root) + 1:]
        logger.warning(f"Converted absolute path '{old_path}' to relative: '{file_path}'")
    elif file_path.startswith("/"):
        logger.error(f"Absolute path detected: {file_path} (use relative path from /project)")
        return {"error": f"Absolute path not supported: {file_path} (use relative path from /project)"}

    full_path = Path(app_path) / file_path
    logger.debug(f"Processing: {full_path} (raw: {file_path}, exists: {full_path.exists()})")
    
    if not full_path.exists():
        logger.error(f"Path not found: {full_path}")
        return {"error": f"Path not found: {file_path}"}
    if full_path.is_dir():
        logger.error(f"Directory detected: {full_path} (expected a file)")
        return {"error": f"Got a directory: {file_path}. Use createParticule for directories."}

    try:
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
        logger.debug(f"File content read: {len(content)} chars")

        existing_match = re.search(r"export\s+const\s+SubParticule\s*=\s*(\{.*?\});", content, re.DOTALL)
        if existing_match:
            logger.info(f"Existing SubParticule found in {file_path}: {existing_match.group(1)}")
            return {
                "content": [{"type": "text", "text": "SubParticule already exists; no changes made."}],
                "summary": "Skipped due to existing context",
                "isError": False
            }

        # Smarter purpose
        stem = full_path.stem.lower()
        purpose = f"Manages {stem}"
        if "guard" in stem:
            purpose = f"Controls access based on {stem.replace('guard', '')}"
        elif "state" in stem or "store" in stem:
            purpose = f"Manages {stem} state"
        elif "hook" in stem or "use" in stem:
            purpose = f"Provides {stem} logic"
        elif any(x in stem for x in ["form", "button", "bar", "status"]):
            purpose = f"Renders {stem} UI"
            if rich and "useRole" in content:
                purpose = f"Renders role-based {stem} UI"
        else:
            purpose = f"Handles {stem} functionality"

        # Props with Lark
        props = extract_props(content, rich)
        if not props:
            jsx_props = re.findall(r"<[^>]+?\s+([a-zA-Z]+)=[{['\"]", content)
            seen = set()
            for prop in jsx_props:
                if prop and prop not in ["className", "style", "key", "ref"] and prop not in seen:
                    desc = prop
                    if rich and any(x in prop.lower() for x in ["icon", "activeicon", "label", "type"]):
                        desc += ": string"
                    props.append(desc)
                    seen.add(prop)
        logger.debug(f"Extracted props: {props}")

        # Hooks
        hooks = []
        hook_pattern = r"use[A-Z]\w*\("
        for line in content.splitlines():
            hook_matches = re.findall(hook_pattern, line)
            for hook in hook_matches:
                hook_name = hook.rstrip("(")
                hooks.append(infer_hook_purpose(hook_name, content) if rich else hook_name)
        hooks = list(dict.fromkeys(hooks))
        logger.debug(f"Extracted hooks: {hooks}")

        # Calls
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

        # Key Logic
        key_logic = []
        if rich:
            enum_match = re.search(r"const\s+\w+\s*=\s*\{([^}]+)\}", content)
            if "useRole" in content:
                key_logic.append("Defines values: Role-based rendering options")
            elif enum_match:
                enums = [e.strip().split(":")[0].strip() for e in enum_match.group(1).split(",") if e.strip()]
                if enums:
                    key_logic.append(f"Defines values: {', '.join(enums[:3])}" + ("" if len(enums) <= 3 else "..."))
            if any(p in content.lower() for p in ["current", "min", "max"]) and "if" in content.lower():
                key_logic.append("Constrained by conditions")
            if "set" in content.lower() and ("state" in stem or "store" in stem):
                key_logic.append("State transitions")

        # Dependencies
        depends_on = []
        if rich:
            hook_deps = {
                "useRole": "components/Core/Role/hooks/useRole.js",
                "useAuth": "components/Core/Auth/hooks/useAuth.js",
                "useRouter": "expo-router",
                "useEventDisplayState": "components/Core/Middleware/state/eventDisplayState.js",
                "useNavigation": "components/Core/Navigation/hooks/useNavigation.js"
            }
            for hook in hooks:
                hook_name = hook.split(" - ")[0]
                if hook_name in hook_deps:
                    depends_on.append(hook_deps[hook_name])

        # Build context
        context = {"purpose": purpose}
        if props:
            context["props"] = props
        if hooks:
            context["hooks"] = hooks
        if calls:
            context["calls"] = calls
        if key_logic:
            context["key_logic"] = key_logic
        if depends_on:
            context["depends_on"] = depends_on

        # Generate export string
        export_str = "export const SubParticule = {\n"
        for key, value in context.items():
            if key == "purpose" or isinstance(value, str):
                export_str += f'  "{key}": "{value}",\n'
            else:
                value_str = json.dumps(value, ensure_ascii=False)
                export_str += f'  "{key}": {value_str},\n'
        export_str = export_str.rstrip("\n").rstrip(",") + "\n};"

        summary = f"Found {len(props)} props, {len(hooks)} hooks, {len(calls)} calls"
        if rich:
            summary += f", {len(key_logic)} key logic, {len(depends_on)} dependencies"

        # Write to file
        with open(full_path, "r+", encoding="utf-8") as f:
            content = f.read()
            if "export const SubParticule" not in content:
                f.seek(0)
                f.write(export_str + "\n" + content)
                f.truncate()
                logger.info(f"SubParticule applied to {file_path}: {export_str}")
            else:
                updated_content = re.sub(
                    r"export\s+const\s+SubParticule\s*=\s*\{.*?\};",
                    export_str,
                    content,
                    flags=re.DOTALL
                )
                f.seek(0)
                f.write(updated_content)
                f.truncate()
                logger.info(f"SubParticule updated in {file_path}: {export_str}")
            with open(full_path, "r", encoding="utf-8") as f_check:
                updated_content = f_check.read(500)
                logger.debug(f"Updated file content (preview): {updated_content}")

        logger.info(f"Generated and applied SubParticule for {file_path} - {summary}")
        return {
            "content": [{"type": "text", "text": export_str}],
            "summary": summary,
            "status": "OK",
            "isError": False,
            "note": "SubParticule applied directly to file",
            "post_action": "read"
        }

    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")
        return {"error": f"Error processing {file_path}: {str(e)}"}

def addSubParticule(file_path: str = None, rich: bool = True) -> dict:
    """Generate SubParticule with optional rich mode (default: True)."""
    return generate_subparticule(file_path, rich=rich)