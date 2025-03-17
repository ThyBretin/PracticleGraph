from src.particle.particle_generator import generate_particle
from src.core.path_resolver import PathResolver
from src.core.chat_handler import chat_handler
from src.particle.particle_support import logger

def particleThis(target: str, active_file: str = None):
    logger.info(f"ParticleThis called with target: {target}, active_file: {active_file}")
    
    if active_file and not target.startswith('/project') and target in active_file:
        target = active_file
    if target.startswith('/Users/Thy/Today/'):
        target = target[len('/Users/Thy/Today/'):]
    
    resolved_path = PathResolver.resolve_path(target)
    result = {}

    if resolved_path.exists():
        particle_data = generate_particle(target, rich=True)
        if particle_data.get("isError"):
            return {"type": "text", "text": particle_data["error"], "isError": True}
        
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
        return chat_handler.initiate_chat(target, result)
    else:
        chat_output = f"Couldn’t find '{target}' as a file—assuming it’s a function? Scanning all files not implemented yet."
        result[target] = ["Function mode TBD"]
        return {"type": "text", "text": chat_output, "isError": False, "particle_data": result}

def handle_particle_this(params):
    target = params.get("target", "")
    active_file = params.get("active_file", None)
    if not target:
        return {"type": "text", "text": "No target provided", "isError": True}
    return particleThis(target, active_file)