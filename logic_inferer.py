import re
from pathlib import Path
from particule_utils import logger

def extract_key_logic(content, file_path=None, rich=True):
    stem = Path(file_path).stem.lower() if file_path else ""
    key_logic = []

    # Enums
    enum_match = re.search(r"const\s+\w+\s*=\s*(\[\s*\{|\{[^}]+?\})(\s*\]|\})", content, re.DOTALL)
    if enum_match:
        enums = re.findall(r"['\"](\w+)['\"]\s*:\s*['\"]?\w+['\"]?", enum_match.group(1))
        if enums:
            key_logic.append(f"Defines options: {', '.join(enums[:3])}" + (len(enums) > 3 and "..." or ""))

    # File-specific
    if "NavigationBar" in file_path:
        key_logic.append("Renders tabs by role")
    elif "EventStatus" in file_path:
        key_logic.append("Renders gender-based progress")
    elif "eventDisplayState" in stem:
        key_logic.append("Calculates gender metrics")

    # Role-based logic
    if "useRole" in content or "isAttendee" in content:
        key_logic.append("Switches behavior by user role")

    # Conditional logic
    if "if" in content.lower():
        if any(p in content.lower() for p in ["current", "min", "max"]):
            if "min" in content.lower() or "max" in content.lower():
                key_logic.append("Evaluates capacity limits")
            else:
                key_logic.append("Tracks current position")
        if "scroll" in content.lower() or "useScrollValue" in content:
            key_logic.append("Responds to scroll events")
        if not key_logic:  # Fallback
            key_logic.append("Branches on conditions")

    # Animation logic
    if any(h in content for h in ["useAnimatedStyle", "useDerivedValue", "withSpring", "withTiming"]):
        key_logic.append("Animates UI elements")

    # State management
    if "set" in content.lower() and ("state" in stem or "store" in stem or "useState" in content):
        key_logic.append("Manages state transitions")

    # Fallback
    if not key_logic and "function" in content.lower():
        key_logic.append("Executes core functionality")

    logger.debug(f"Key logic for {file_path}: {key_logic}")
    return key_logic