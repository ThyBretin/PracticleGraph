from typing import Dict, Any, List, Optional, Union
import logging
from copy import deepcopy

from src.particle.particle_support import logger

def postProcessGraph(graph: Union[Dict[str, Any], List, Any]) -> Union[Dict[str, Any], List, Any]:
    """
    Post-process a particle graph to enhance its data structure and add derived information.
    
    This function takes a raw particle graph and performs various post-processing operations
    to enrich the graph with additional metadata, clean up unnecessary information,
    and ensure consistency across different parts of the graph.
    
    Args:
        graph: The original particle graph data structure
        
    Returns:
        The enhanced particle graph with post-processing applied
    """
    # Handle non-dictionary types gracefully
    if not isinstance(graph, dict):
        logger.debug(f"Non-dict graph encountered in postProcessGraph ({type(graph)}), returning as is")
        return graph
    
    # Skip empty graphs
    if not graph:
        logger.warning("Cannot post-process graph: Empty graph data")
        return graph
    
    # Create a deep copy to avoid modifying the original
    processed_graph = deepcopy(graph)
    
    # Add metadata if not present
    if "metadata" not in processed_graph:
        processed_graph["metadata"] = {}
    
    # Add post-processing flag
    processed_graph["metadata"]["post_processed"] = True
    
    # Calculate additional statistics if files are present
    file_count = 0
    node_count = 0
    
    # Different file structure handling based on codebase data
    if "files" in processed_graph:
        # Handle different possible file structures
        files_data = processed_graph.get("files", {})
        
        # Count structure 1: Dictionary of file paths to file data
        if isinstance(files_data, dict) and all(isinstance(k, str) for k in files_data.keys()):
            file_count = len(files_data)
            # Count nodes in this structure
            for file_path, file_data in files_data.items():
                if isinstance(file_data, dict) and "particles" in file_data:
                    node_count += len(file_data.get("particles", []))
        
        # Count structure 2: Dictionary with 'primary', 'shared', etc. keys
        elif isinstance(files_data, dict) and any(k in ["primary", "shared"] for k in files_data.keys()):
            primary_files = files_data.get("primary", [])
            shared_files = files_data.get("shared", [])
            file_count = len(primary_files) + len(shared_files)
            
            # Count nodes in this structure
            for file_data in primary_files + shared_files:
                if isinstance(file_data, dict) and "particles" in file_data:
                    node_count += len(file_data.get("particles", []))
        
        # Count structure 3: File count from metadata or other fields
        if file_count == 0 and "file_count" in processed_graph:
            file_count = processed_graph["file_count"]
        
        # Update the metadata
        processed_graph["metadata"]["file_count"] = file_count
        processed_graph["metadata"]["node_count"] = node_count
        
        # Apply dependency linking
        processed_graph = linkDependencies(processed_graph)
        
        # Apply reasoning tracing if available
        processed_graph = traceReasoning(processed_graph)
        
        logger.info(f"Post-processed graph: {file_count} files, {node_count} nodes")
    else:
        logger.debug("Skipping detailed post-processing: No 'files' key in graph")
    
    return processed_graph

def linkDependencies(graph: Union[Dict[str, Any], List, Any]) -> Union[Dict[str, Any], List, Any]:
    """
    Link dependencies between different particles in the graph.
    
    This function identifies and establishes connections between particles 
    based on imports, exports, function calls, and other relationships.
    
    Args:
        graph: The particle graph to process
        
    Returns:
        The graph with linked dependencies
    """
    # Handle non-dictionary types gracefully
    if not isinstance(graph, dict):
        return graph
    
    # Skip empty graphs or graphs without files
    if not graph or "files" not in graph:
        return graph
    
    # Create a deep copy to avoid modifying the original
    linked_graph = deepcopy(graph)
    
    # Track imports and exports across files
    import_map = {}  # Maps imported items to their source files
    export_map = {}  # Maps exported items to their source files
    
    # First pass: collect all exports
    for file_path, file_data in linked_graph.get("files", {}).items():
        if not isinstance(file_data, dict) or "particles" not in file_data:
            continue
            
        for particle in file_data.get("particles", []):
            # Track exports
            for export_item in particle.get("exports", []):
                if isinstance(export_item, dict) and "name" in export_item:
                    export_name = export_item["name"]
                elif isinstance(export_item, str):
                    export_name = export_item
                else:
                    continue
                
                export_map[export_name] = {
                    "file": file_path,
                    "particle_id": particle.get("id", "")
                }
    
    # Second pass: link imports to exports
    for file_path, file_data in linked_graph.get("files", {}).items():
        if not isinstance(file_data, dict) or "particles" not in file_data:
            continue
            
        for particle in file_data.get("particles", []):
            # Track and link imports
            imports_linked = []
            
            for import_item in particle.get("imports", []):
                if isinstance(import_item, dict) and "name" in import_item:
                    import_name = import_item["name"]
                    import_source = import_item.get("source", "")
                elif isinstance(import_item, str):
                    # Simple parsing for string imports like "import { X } from 'Y'"
                    parts = import_item.split(" from ")
                    if len(parts) == 2:
                        import_name = parts[0].replace("import", "").strip()
                        import_source = parts[1].strip().strip("'\"")
                    else:
                        continue
                else:
                    continue
                
                # Check if this import matches a known export
                if import_name in export_map:
                    imports_linked.append({
                        "name": import_name,
                        "source": import_source,
                        "resolved_file": export_map[import_name]["file"],
                        "resolved_particle": export_map[import_name]["particle_id"]
                    })
            
            # Update particle with linked imports
            if imports_linked:
                particle["imports_linked"] = imports_linked
    
    # Track dependency relationships at graph level
    if "dependencies" not in linked_graph:
        linked_graph["dependencies"] = []
    
    # Clear existing dependencies to avoid duplicates
    linked_graph["dependencies"] = []
    
    # Build file-level dependency relationships
    file_dependencies = {}
    
    for file_path, file_data in linked_graph.get("files", {}).items():
        if not isinstance(file_data, dict) or "particles" not in file_data:
            continue
            
        for particle in file_data.get("particles", []):
            if "imports_linked" in particle:
                for linked_import in particle["imports_linked"]:
                    # Get the source file
                    source_file = linked_import.get("resolved_file", "")
                    if source_file and source_file != file_path:
                        # Add to file dependencies tracking
                        if file_path not in file_dependencies:
                            file_dependencies[file_path] = set()
                        file_dependencies[file_path].add(source_file)
    
    # Add file dependencies to graph
    for dependent_file, source_files in file_dependencies.items():
        for source_file in source_files:
            linked_graph["dependencies"].append({
                "source": source_file,
                "target": dependent_file,
                "type": "import"
            })
    
    logger.info(f"Linked dependencies in graph: {len(linked_graph['dependencies'])} connections")
    return linked_graph

def traceReasoning(graph: Union[Dict[str, Any], List, Any]) -> Union[Dict[str, Any], List, Any]:
    """
    Trace reasoning paths through the graph by analyzing function call chains
    and data flow between components.
    
    This function identifies and annotates chains of function calls, data transformations,
    and state changes to provide traceability of logic flows within the application.
    
    Args:
        graph: The particle graph to process
        
    Returns:
        The graph with reasoning paths traced
    """
    # Handle non-dictionary types gracefully
    if not isinstance(graph, dict):
        return graph
    
    # Skip empty graphs or graphs without files
    if not graph or "files" not in graph:
        return graph
    
    # Create a deep copy to avoid modifying the original
    traced_graph = deepcopy(graph)
    
    # Create a map of function definitions
    function_map = {}  # Maps function name to its particle
    
    # First pass: collect all function definitions
    for file_path, file_data in traced_graph.get("files", {}).items():
        if not isinstance(file_data, dict) or "particles" not in file_data:
            continue
            
        for particle in file_data.get("particles", []):
            # Check if this particle defines a function
            if particle.get("type") in ["function", "method", "arrow_function"]:
                function_name = particle.get("name", "")
                if function_name:
                    function_map[function_name] = {
                        "file": file_path,
                        "particle_id": particle.get("id", ""),
                        "particle": particle
                    }
    
    # Second pass: trace function calls
    call_traces = []
    
    for file_path, file_data in traced_graph.get("files", {}).items():
        if not isinstance(file_data, dict) or "particles" not in file_data:
            continue
            
        for particle in file_data.get("particles", []):
            # Check for function calls
            for call in particle.get("calls", []):
                if isinstance(call, dict) and "name" in call:
                    call_name = call["name"]
                elif isinstance(call, str):
                    # Simple parsing for string calls like "someFunction()"
                    call_name = call.split("(")[0].strip() if "(" in call else call
                else:
                    continue
                
                # Check if this call matches a known function
                if call_name in function_map:
                    call_trace = {
                        "caller": {
                            "file": file_path,
                            "particle_id": particle.get("id", ""),
                            "function": particle.get("name", "")
                        },
                        "called": {
                            "file": function_map[call_name]["file"],
                            "particle_id": function_map[call_name]["particle_id"],
                            "function": call_name
                        },
                        "type": "function_call"
                    }
                    call_traces.append(call_trace)
    
    # Add reasoning traces to graph
    traced_graph["reasoning_traces"] = call_traces
    
    logger.info(f"Traced reasoning in graph: {len(call_traces)} function call traces")
    return traced_graph
