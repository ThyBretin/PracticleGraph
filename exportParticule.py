import json
from datetime import datetime
from pathlib import Path
from particule_utils import app_path, logger
from loadParticule import loadParticule

def exportParticule(features: str) -> dict:
    """
    Export a Particule manifest (single or aggregate) to a JSON file.
    """
    manifest = loadParticule(features)
    if "error" in manifest:
        return {"error": manifest["error"]}

    feature_str = "_".join(manifest.get("features", [features])).lower()
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    filename = f"{feature_str}_particule_{timestamp}.json" if not manifest.get("aggregate") else f"aggregate_{feature_str}_{timestamp}.json"
    output_path = Path(app_path) / "particules" / filename

    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    
    logger.info(f"Exported {output_path}")
    return {"content": [{"type": "text", "text": f"Saved {output_path}"}], "isError": False}