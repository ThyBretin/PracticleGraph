import json
from datetime import datetime
from pathlib import Path
from particule_utils import app_path, logger, particule_cache
from createParticule import createParticule

def exportParticule(feature: str) -> str:
    feature = feature.lower()  # Case-insensitive
    if feature not in particule_cache:
        logger.info(f"No cached manifest for {feature}, creating it")
        feature_path = f"components/Features/{feature.capitalize()}"  # Guess path
        if "core" in feature.lower():  # Handle Core features
            feature_path = f"components/Core/{feature.capitalize()}"
        particule_cache[feature] = createParticule(feature_path)
    
    manifest = particule_cache[feature]
    if "error" in manifest:
        return f"Cannot export: {manifest['error']}"
    
    particules_dir = Path(app_path) / "Particules"
    particules_dir.mkdir(exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    save_path = particules_dir / f"{feature}_{timestamp}.json"
    try:
        with open(save_path, "w") as f:
            json.dump(manifest, f, indent=2)
        logger.info(f"Exported {save_path}")
        return f"Saved {save_path}"
    except Exception as e:
        logger.error(f"Failed to export {save_path}: {e}")
        return f"Error saving {save_path}: {str(e)}"