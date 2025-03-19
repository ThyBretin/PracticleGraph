def extract_dependencies(hooks, content, rich=True, particle=None):
    """Extract dependencies from particle attributes and hooks."""
    depends_on = []
    if not rich or not particle:
        return depends_on
    
    # Use particle's depends_on from metadata_extractor.js
    depends_on.extend(particle["attributes"].get("depends_on", []))
    # Add hooks as dependencies (just names, no hardcoded paths)
    for hook in hooks:
        hook_name = hook.split(" - ")[0]
        depends_on.append(hook_name)
    
    return list(dict.fromkeys(depends_on))  # Dedupe