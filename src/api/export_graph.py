import json
import subprocess
from datetime import datetime
from pathlib import Path

from src.particle.particle_support import logger
from src.api.load_graph import loadGraph
from src.helpers.data_cleaner import filter_empty
from src.core.path_resolver import PathResolver
from src.graph.graph_support import postProcessGraph, linkDependencies, traceReasoning
from src.graph.tech_stack import get_tech_stack

def exportGraph(path: str) -> dict:
    """
    Export a Particle Graph (single or aggregate) to a JSON file, formatted with Prettier.
    
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
    if isinstance(manifest, dict) and "error" in manifest:
        logger.error(f"Failed to load graph for {feature_name}: {manifest['error']}")
        return {"error": manifest["error"]}
    
    # Extract entities and ensure tech stack
    is_codebase = path.lower() in ("codebase", "all")
    entities = []
    if isinstance(manifest, dict):
        if is_codebase or not manifest.get("aggregate"):
            entities = [{"path": f["path"], "type": f.get("type", "file")} for f in manifest.get("files", {}).get("primary", []) + manifest.get("files", {}).get("shared", [])]
        else:
            for feature_files in manifest.get("files", {}).values():
                entities.extend([{"path": k, "type": v.get("type", "file")} for k, v in feature_files.items()])
    
    # Ensure tech_stack is present
    if entities and "tech_stack" not in manifest:
        try:
            manifest["tech_stack"] = get_tech_stack(entities)
        except Exception as e:
            logger.warning(f"Tech stack generation failed: {str(e)}")
    
    # Apply post-processing if applicable
    if isinstance(manifest, dict) and "files" in manifest and not manifest.get("aggregate"):
        try:
            manifest = postProcessGraph(manifest)
        except Exception as e:
            logger.warning(f"Graph post-processing skipped: {str(e)}")
    
    # Handle special formatting for codebase graph
    if is_codebase:
        file_count = manifest.get("file_count", len(entities))
        manifest["file_count"] = file_count
        manifest["js_files_total"] = manifest.get("js_files_total", file_count)
        manifest["coverage_percentage"] = manifest.get("coverage_percentage", 100.0)
        manifest["exported_at"] = datetime.utcnow().isoformat() + "Z"
        manifest = filter_empty(manifest)
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        filename = f"codebase_graph_{timestamp}.json"
    else:
        if isinstance(manifest, dict):
            feature_str = "_".join(manifest.get("features", [feature_name])).lower()
            timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            filename = f"{feature_str}_graph_{timestamp}.json" if not manifest.get("aggregate") else f"aggregate_{feature_str}_{timestamp}.json"
        else:
            timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            filename = f"{feature_name}_graph_{timestamp}.json"
    
    # Create output path using PathResolver
    output_path = PathResolver.export_path(filename)
    temp_path = output_path.with_suffix('.tmp.json')
    
    # Write raw JSON to temp file
    with open(temp_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f)
    logger.debug(f"Wrote raw graph to {temp_path}")
    
    # Format with Prettier
    try:
        prettier_cmd = [
            'prettier',
            '--write',
            str(temp_path),
            '--parser', 'json',
            '--print-width', '120',
            '--no-bracket-spacing'
        ]
        subprocess.run(prettier_cmd, check=True)
        logger.debug(f"Ran Prettier on {temp_path}")
        
        # Move formatted content to final path
        with open(temp_path, 'r', encoding='utf-8') as f:
            formatted_content = f.read()
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(formatted_content)
        logger.info(f"Wrote Prettier-formatted graph to {output_path}")
        
        # Clean up
        temp_path.unlink()
    except subprocess.CalledProcessError as e:
        logger.error(f"Prettier failed: {e}")
        return {"error": f"Prettier failed: {e}", "isError": True}
    
    # Log and prepare response
    if is_codebase:
        file_count = manifest.get("file_count", 0)
        node_count = manifest.get("metadata", {}).get("node_count", 0) if isinstance(manifest, dict) else 0
        dependency_count = len(manifest.get("dependencies", [])) if isinstance(manifest, dict) else 0
        
        logger.info(f"Exported codebase graph ({file_count} files) to {output_path}")
        summary = (
            f"The graph has been successfully exported to {output_path}. The export includes:\n\n"
            f"{file_count} files analyzed ({manifest.get('coverage_percentage', 0)}% of JS files)\n"
        )
        if node_count > 0:
            summary += f"{node_count} particles identified across all files\n"
        if dependency_count > 0:
            summary += f"{dependency_count} dependencies traced between components\n"
        if "tech_stack" in manifest and manifest["tech_stack"]:
            tech_list = [f"{k}: {', '.join(v.keys())}" for k, v in manifest["tech_stack"].items()]
            summary += f"Tech stack: {', '.join(tech_list)}\n"
        summary += (
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