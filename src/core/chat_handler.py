from src.particle.particle_support import logger
import json
import os  # Added this!

class ChatHandler:
    def __init__(self):
        self.state = {}

    def initiate_chat(self, target: str, particle_data: dict) -> dict:
        logger.info(f"Initiating chat for {target}")
        
        if target not in self.state or self.state[target]["step"] == "done":
            attrs = particle_data.get(target, [])
            summary = "\n".join(attrs) if attrs else "No significant elements."
            chat_message = (
                f"I’ve analyzed {target} and found:\n{summary}\n"
                "Sounds like it’s rendering event locations—maybe venue addresses? "
                "What’s your take? (Reply with your thoughts, e.g., 'It’s about...')"
            )
            self.state[target] = {"step": "initial", "particle_data": particle_data}
            return {"type": "text", "text": chat_message, "isError": False}
        
        return {"type": "text", "text": "Chat session active—please reply with your thoughts!", "isError": False}

    def handle_response(self, target: str, user_response: str) -> dict:
        if target not in self.state:
            return {"type": "text", "text": "No chat session found—start with ParticleThis!", "isError": True}
        
        state = self.state[target]
        step = state["step"]

        if step == "initial":
            refined_message = (
                f"Nice, so it’s {user_response} based on that `location` prop, "
                "with a fallback if the data’s incomplete. Sound good? "
                "Reply 'yes' or 'perfect' to confirm!"
            )
            state["step"] = "refine"
            state["initial_response"] = user_response
            return {"type": "text", "text": refined_message, "isError": False}

        elif step == "refine":
            if user_response.lower() in ["yes", "perfect", "correct", "that’s perfect"]:
                intent = (
                    f"Renders venue addresses for events using the location prop, "
                    "with fallback to legacy fields if display is missing"
                )
                mapping = {
                    "concepts": {
                        "Location": {
                            "description": intent,
                            "mappings": [
                                {"file": target, "intent": "Displays venue address", "props": ["location", "style"], "logic": ["!location → returns early"]}
                            ]
                        }
                    }
                }
                logger.info(f"Intent confirmed for {target}: {intent}")
                state["step"] = "done"
                # Save to project_definition.json
                try:
                    proj_def_path = "/project/project_definition.json"
                    proj_def = json.loads(read_file(proj_def_path)[0]) if os.path.exists(proj_def_path) else {}
                    proj_def.update(mapping)
                    with open(proj_def_path, 'w') as f:
                        json.dump(proj_def, f, indent=2)
                    logger.info(f"Saved intent to {proj_def_path}")
                except Exception as e:
                    logger.error(f"Failed to save intent: {e}")
                    raise  # Re-raise to catch in logs
                return {
                    "type": "text",
                    "text": f"I created a dedicated Particle with: ‘{intent}’\nSaved to `project_definition.json`—run `createGraph('/src')` to see it!",
                    "isError": False,
                    "intent": mapping
                }
            else:
                return {"type": "text", "text": "Not quite? Tell me more to refine it!", "isError": False}
        
        return {"type": "text", "text": "Chat session complete—start a new one if needed!", "isError": False}

chat_handler = ChatHandler()

def handle_initiate_chat(params):
    target = params.get("target", "")
    particle_data = params.get("particle_data", {})
    return chat_handler.initiate_chat(target, particle_data)

def handle_chat_response(params):
    if isinstance(params, str):
        try:
            params = json.loads(params)
        except json.JSONDecodeError:
            return {"type": "text", "text": "Invalid JSON—please send like {\"target\": \"...\", \"response\": \"...\"}", "isError": True}
    
    target = params.get("target", "")
    response = params.get("response", "")
    if not target or not response:
        return {"type": "text", "text": "Missing target or response—use {\"target\": \"...\", \"response\": \"...\"}", "isError": True}
    return chat_handler.handle_response(target, response)