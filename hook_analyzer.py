import re  # Make sure this is at the top
from particule_utils import logger

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

def extract_hooks(content, rich=True):
    """Extract hooks from content with optional rich descriptions."""
    hooks = []
    hook_pattern = r"use[A-Z]\w*\("
    for line in content.splitlines():
        hook_matches = re.findall(hook_pattern, line)
        for hook in hook_matches:
            hook_name = hook.rstrip("(")
            hooks.append(infer_hook_purpose(hook_name, content) if rich else hook_name)
    return list(dict.fromkeys(hooks))  # Dedupe