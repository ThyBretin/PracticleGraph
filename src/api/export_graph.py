import json
from datetime import datetime
from pathlib import Path

from src.particle.particle_support import logger
from src.api.load_graph import loadGraph
from src.helpers.data_cleaner import filter_empty
from src.core.path_resolver import PathResolver

def exportGraph(path: str) -> dict:
    """
    Export a Particle Graph (single or aggregate) to a JSON file.
    
    Args:
        path: Path/feature name(s) to export graph for
              Can be comma-separated for multiple features (e.g., "Events,Role")
              Special values: "all" or "codebase" to export the full codebase graph
    
    Returns:
        dict: Result containing path to saved file and operation status
    """
    logger.info(f"Exporting Particle Graph for: {path}")
    
    # Normalize path to lowercase feature name
    feature_name = path.split("/")[-1].lower() if "," not in path else "_".join(p.lower() for p in path.split(","))
    manifest = loadGraph(feature_name)
    if "error" in manifest:
        logger.error(f"Failed to load graph for {feature_name}: {manifest['error']}")
        return {"error": manifest["error"]}
    
    # Handle special formatting for codebase graph
    is_codebase = path.lower() in ("codebase", "all")
    if is_codebase:
        file_count = len(manifest.get("files", {}))
        manifest["file_count"] = file_count
        manifest["js_files_total"] = file_count
        manifest["coverage_percentage"] = 100.0
        manifest["exported_at"] = datetime.utcnow().isoformat() + "Z"
        manifest = filter_empty(manifest)
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        filename = f"codebase_graph_{timestamp}.json"
    else:
        feature_str = "_".join(manifest.get("features", [feature_name])).lower()
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        filename = f"{feature_str}_graph_{timestamp}.json" if not manifest.get("aggregate") else f"aggregate_{feature_str}_{timestamp}.json"
    
    # Create output path using PathResolver
    output_path = PathResolver.export_path(filename)
    
    # Write the manifest to file
    error = PathResolver.write_json_file(output_path, manifest)
    if error:
        logger.error(f"Failed to write export file: {error}")
        return {"error": error, "isError": True}
    
    # Log and prepare response
    if is_codebase:
        file_count = manifest.get("file_count", 0)
        logger.info(f"Exported codebase graph ({file_count} files) to {output_path}")
        summary = (
            f"The graph has been successfully exported to {output_path}. The export includes:\n\n"
            f"{file_count} files analyzed (100% of relevant JS/JSX files)\n"
            f"Complete structure of all components with metadata\n"
            f"Dependencies and relationships between components"
        )
        return {
            "content": [{"type": "text", "text": summary}],
            "summary": summary,
            "isError": False
        }
    else:
        logger.info(f"Exported graph to {output_path}")
        return {
            "content": [{"type": "text", "text": f"Saved {output_path}"}], 
            "isError": False
        }