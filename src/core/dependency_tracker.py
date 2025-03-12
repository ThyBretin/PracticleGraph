from src.core.particle_utils import logger

def extract_dependencies(hooks, content, rich=True):
    """Extract dependencies based on hooks and content."""
    depends_on = []
    if not rich:
        return depends_on

    hook_deps = {
        "useRole": "components/Core/Role/hooks/useRole.js",
        "useAuth": "components/Core/Auth/hooks/useAuth.js",
        "useRouter": "expo-router",
        "useSegments": "expo-router",
        "useEventDisplayState": "components/Core/Middleware/state/eventDisplayState.js",
        "useNavigation": "components/Core/Navigation/hooks/useNavigation.js"
    }

    for hook in hooks:
        hook_name = hook.split(" - ")[0]  # Strip description
        if hook_name in hook_deps:
            depends_on.append(hook_deps[hook_name])

    # Add more dependency detection if needed (e.g., imports)
    if "expo-router" in content.lower():
        depends_on.append("expo-router")

    return list(dict.fromkeys(depends_on))  # Dedupe