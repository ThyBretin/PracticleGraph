from pathlib import Path
from particle_utils import logger

def infer_purpose(file_path: str, content: str, rich: bool = True) -> str:
    """Infer the purpose of the component based on file name and content."""
    stem = Path(file_path).stem.lower()
    purpose = f"Manages {stem}"
    if "guard" in stem:
        purpose = f"Controls access based on {stem.replace('guard', '')}"
    elif "state" in stem or "store" in stem:
        purpose = f"Manages {stem} state"
    elif "hook" in stem or "use" in stem:
        purpose = f"Provides {stem} logic"
    elif any(x in stem for x in ["form", "button", "bar", "status", "feed"]):
        purpose = f"Renders {stem} UI"
        if rich and "useRole" in content:
            purpose = f"Renders role-based {stem} UI"
    else:
        purpose = f"Handles {stem} functionality"
    return purpose

def build_subparticle(file_path: str, content: str, props: list, hooks: list, calls: list, key_logic: list, depends_on: list, rich: bool = True) -> dict:
    """Assemble the SubParticle context."""
    purpose = infer_purpose(file_path, content, rich)
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

    logger.debug(f"Built SubParticle context: {context}")
    return context