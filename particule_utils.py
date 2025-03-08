import json
import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Set

app_path = os.getenv("PARTICULE_PATH", "/project")
particule_cache: Dict[str, dict] = {}
logger = logging.getLogger("ParticuleGraph")

def load_gitignore_patterns(root_path: str) -> Dict[str, Set[str]]:
    gitignore_path = Path(root_path) / ".gitignore"
    patterns = {root_path: set()}
    if gitignore_path.exists():
        with open(gitignore_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]
            patterns[root_path].update(lines)
        logger.debug(f"Loaded from {gitignore_path}: {patterns[root_path]}")
    return patterns

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

def extract_particule_logic(file_path: str) -> dict:
    """Extract structured context (purpose, props, calls) from a file's ContextParticule export."""
    full_path = Path(app_path) / file_path
    if not full_path.exists() or full_path.is_dir():
        return None
    
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Parse export const ContextParticule
        context_match = re.search(r"export\s+const\s+ContextParticule\s*=\s*(\{.*?\});", content, re.DOTALL)
        if context_match:
            try:
                context_str = context_match.group(1).replace("'", '"')
                context = eval(context_str, {"__builtins__": {}})
                return {
                    "purpose": context.get("purpose", ""),
                    "props": context.get("props", []),
                    "calls": context.get("calls", [])
                }
            except Exception as e:
                logger.debug(f"Invalid ContextParticule in {file_path}: {e}")

        # Fallback: Infer from code
        context = {"purpose": "", "props": [], "calls": []}
        # Props
        props = re.findall(r"const\s+\w+\s*=\s*\(\{([^}]*)\}\)", content)
        if props:
            context["props"] = [p.strip() for p in props[0].split(",") if p.strip()]
        # Calls (old extract_api_calls logic)
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