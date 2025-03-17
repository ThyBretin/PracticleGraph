from src.particle.particle_generator import generate_particle
from src.core.path_resolver import PathResolver
from src.particle.particle_support import logger

def particleThis(target: str):
    """Process a target and return particle data for chat refinement."""
    logger.info(f"ParticleThis called with target: {target}")
    
    resolved_path = PathResolver.resolve_path(target)
    result = {}

    if resolved_path.exists():  # File mode
        particle_data = generate_particle(target, rich=True)
        if particle_data.get("isError"):
            return {"content": [{"type": "text", "text": particle_data["error"]}], "isError": True}
        
        particle = particle_data["particle"]
        attrs = particle.get("attributes", {})
        summary = []
        
        for key, label in [
            ("props", "Props"),
            ("hooks", "Hooks"),
            ("calls", "Calls"),
            ("logic", "Logic"),
            ("comments", "Comments"),
            ("variables", "Variables"),
            ("functions", "Functions"),
            ("depends_on", "Dependencies")
        ]:
            if key in attrs and attrs[key]:
                if key == "logic":
                    values = [f"{item['condition']} → {item['action']}" for item in attrs[key]]
                elif key == "comments":
                    values = [item["text"] for item in attrs[key]]
                elif isinstance(attrs[key], list) and all(isinstance(item, dict) for item in attrs[key]):
                    values = [item["name"] for item in attrs[key]]
                else:
                    values = attrs[key]
                summary.append(f"{label}: {', '.join(str(v) for v in values[:5])}")
        
        result[target] = summary or ["No significant elements"]
        chat_output = f"I’ve analyzed {target} and found:\n" + "\n".join(summary) if summary else f"{target} has no key elements."
    else:  # Function mode placeholder
        chat_output = f"Assuming '{target}' is a function—scanning all files not implemented yet."
        result[target] = ["Function mode TBD"]

    return {
        "content": [{"type": "text", "text": chat_output}],
        "isError": False,
        "particle_data": result
    }

# MCP JSON-RPC handler
def handle_particle_this(params):
    target = params.get("target", "")
    if not target:
        return {"content": [{"type": "text", "text": "No target provided"}], "isError": True}
    return particleThis(target)