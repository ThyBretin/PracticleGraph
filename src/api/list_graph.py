from src.particle.particle_support import logger
from src.core.path_resolver import PathResolver
from src.helpers.dir_scanner import scan_directory

def listGraph() -> dict:
    """
    List all cached Particle Graphs from the file system with metadata.
    Returns a JSON-RPC response with graph details.
    """
    # Use CACHE_DIR directly from PathResolver
    cache_dir = PathResolver.CACHE_DIR
    logger.info(f"Scanning cached graphs in: {cache_dir}")
    
    # Scan for *.graph.json files (adjust pattern if needed)
    graph_files = scan_directory(str(cache_dir), "*.graph.json")
    if not graph_files:
        logger.info("No cached graphs found")
        return {
            "content": [{"type": "text", "text": "No cached Particle Graphs available"}],
            "status": "OK",
            "isError": False
        }
    
    graphs = []
    for graph_file in graph_files:
        try:
            graph_data, error = PathResolver.read_json_file(str(graph_file))
            if error:
                logger.error(f"Failed to read {graph_file}: {error}")
                continue
            key = graph_file.stem  # e.g., hub_events
            graphs.append({
                "name": key,
                "last_crawled": graph_data.get("last_crawled", "unknown"),
                "file_count": graph_data.get("file_count", 0),
                "token_count": graph_data.get("token_count", 0),
                "features": graph_data.get("features", [key]) if graph_data.get("aggregate") else [key]
            })
        except Exception as e:
            logger.error(f"Error reading graph {graph_file}: {str(e)}")
            continue
    
    if not graphs:
        logger.warning("No valid graphs found")
        return {
            "content": [{"type": "text", "text": "No valid Particle Graphs available"}],
            "status": "OK",
            "isError": False
        }
    
    formatted_list = [f"• {g['name']} (Files: {g['file_count']}, Tokens: {g['token_count']}): {g['last_crawled']}" 
                     for g in sorted(graphs, key=lambda x: x["name"])]
    formatted_text = "Available Particle Graphs:\n\n" + "\n".join(formatted_list)
    
    logger.info(f"Listed {len(graphs)} graphs")
    return {
        "content": [{"type": "text", "text": formatted_text}],
        "status": "OK",
        "isError": False,
        "graphs": graphs
    }