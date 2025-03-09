import re
from particule_utils import logger

def extract_key_logic(content, rich=True):
    """Infer key logic from content."""
    key_logic = []
    if not rich:
        return key_logic

    enum_match = re.search(r"const\s+\w+\s*=\s*\{([^}]+)\}", content)
    stem = "eventfeed"  # Hardcoded for now; we'll pass file_path later
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

    return key_logic