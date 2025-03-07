import json
from datetime import datetime
from pathlib import Path
from practicle_utils import app_path, logger, practicle_cache
from createPracticle import createPracticle

def exportPracticle(feature: str) -> str:
    feature = feature.lower()  # Case-insensitive
    if feature not in practicle_cache:
        logger.info(f"No cached manifest for {feature}, creating it")
        feature_path = f"components/Features/{feature.capitalize()}"  # Guess path
        if "core" in feature.lower():  # Handle Core features
            feature_path = f"components/Core/{feature.capitalize()}"
        practicle_cache[feature] = createPracticle(feature_path)
    
    manifest = practicle_cache[feature]
    if "error" in manifest:
        return f"Cannot export: {manifest['error']}"
    
    practicles_dir = Path(app_path) / "practicles"
    practicles_dir.mkdir(exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    save_path = practicles_dir / f"{feature}_{timestamp}.json"
    try:
        with open(save_path, "w") as f:
            json.dump(manifest, f, indent=2)
        logger.info(f"Exported {save_path}")
        return f"Saved {save_path}"
    except Exception as e:
        logger.error(f"Failed to export {save_path}: {e}")
        return f"Error saving {save_path}: {str(e)}"