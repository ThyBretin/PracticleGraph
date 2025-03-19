from typing import Dict, Any, List, Optional, Union
from copy import deepcopy

from src.particle.particle_support import logger

def postProcessGraph(graph: Union[Dict[str, Any], List, Any], feature_path: Optional[str] = None) -> Union[Dict[str, Any], List, Any]:
    if not isinstance(graph, dict):
        logger.debug(f"Non-dict graph encountered in postProcessGraph ({type(graph)}), returning as is")
        return graph
    
    if not graph:
        logger.warning("Cannot post-process graph: Empty graph data")
        return graph
    
    processed_graph = deepcopy(graph)
    
    if "metadata" not in processed_graph:
        processed_graph["metadata"] = {}
    
    processed_graph["metadata"]["post_processed"] = True
    
    file_count = 0
    node_count = 0
    
    if "files" in processed_graph:
        files_data = processed_graph.get("files", {})
        
        if isinstance(files_data, dict) and all(isinstance(k, str) for k in files_data.keys()):
            file_count = len(files_data)
            for file_path, file_data in files_data.items():
                if isinstance(file_data, dict) and "particles" in file_data:
                    node_count += len(file_data.get("particles", []))
        elif isinstance(files_data, dict) and any(k in ["primary", "shared"] for k in files_data.keys()):
            primary_files = files_data.get("primary", [])
            shared_files = files_data.get("shared", [])
            file_count = len(primary_files) + len(shared_files)
            for file_data in primary_files + shared_files:
                if isinstance(file_data, dict) and "context" in file_data:
                    node_count += 1
        
        if file_count == 0 and "file_count" in processed_graph:
            file_count = processed_graph["file_count"]
        
        processed_graph["metadata"]["file_count"] = file_count
        processed_graph["metadata"]["node_count"] = node_count
        
        processed_graph = linkDependencies(processed_graph, feature_path)
        processed_graph = traceReasoning(processed_graph)
        
        logger.info(f"Post-processed graph: {file_count} files, {node_count} nodes")
    else:
        logger.debug("Skipping detailed post-processing: No 'files' key in graph")
    
    return processed_graph

def linkDependencies(graph: Union[Dict[str, Any], List, Any], feature_path: Optional[str] = None) -> Union[Dict[str, Any], List, Any]:
    if not isinstance(graph, dict) or "files" not in graph:
        return graph
    
    linked_graph = deepcopy(graph)
    import_map = {}
    export_map = {}
    
    files_data = linked_graph.get("files", {})
    if "primary" in files_data or "shared" in files_data:
        for particle in files_data.get("primary", []) + files_data.get("shared", []):
            if isinstance(particle, dict) and "context" in particle:
                for export_item in particle["context"].get("attributes", {}).get("exports", []):
                    export_name = export_item.get("name", export_item) if isinstance(export_item, dict) else export_item
                    if export_name:
                        export_map[export_name] = {
                            "file": particle["path"],
                            "particle_id": particle.get("id", particle["path"])
                        }
    else:
        for file_key, file_data in files_data.items():
            if isinstance(file_data, dict) and "particles" in file_data:
                for particle in file_data.get("particles", []):
                    for export_item in particle.get("exports", []):
                        export_name = export_item.get("name", export_item) if isinstance(export_item, dict) else export_item
                        if export_name:
                            export_map[export_name] = {
                                "file": file_key,
                                "particle_id": particle.get("id", "")
                            }
    
    if "primary" in files_data or "shared" in files_data:
        for particle in files_data.get("primary", []) + files_data.get("shared", []):
            if isinstance(particle, dict) and "context" in particle:
                imports_linked = []
                depends_on = particle["context"].get("attributes", {}).get("depends_on", [])
                for import_item in depends_on:
                    import_source = import_item.split(" (")[0]
                    import_name = import_source.split("/")[-1]
                    if import_name in export_map:
                        imports_linked.append({
                            "name": import_name,
                            "source": import_source,
                            "resolved_file": export_map[import_name]["file"],
                            "resolved_particle": export_map[import_name]["particle_id"]
                        })
                if imports_linked:
                    particle["context"]["imports_linked"] = imports_linked
    else:
        for file_key, file_data in files_data.items():
            if isinstance(file_data, dict) and "particles" in file_data:
                for particle in file_data.get("particles", []):
                    imports_linked = []
                    for import_item in particle.get("imports", []):
                        if isinstance(import_item, dict) and "name" in import_item:
                            import_name = import_item["name"]
                            import_source = import_item.get("source", "")
                        elif isinstance(import_item, str):
                            parts = import_item.split(" from ")
                            if len(parts) == 2:
                                import_name = parts[0].replace("import", "").strip()
                                import_source = parts[1].strip().strip("'\"")
                            else:
                                continue
                        else:
                            continue
                        if import_name in export_map:
                            imports_linked.append({
                                "name": import_name,
                                "source": import_source,
                                "resolved_file": export_map[import_name]["file"],
                                "resolved_particle": export_map[import_name]["particle_id"]
                            })
                    if imports_linked:
                        particle["imports_linked"] = imports_linked
    
    linked_graph["dependencies"] = []
    file_dependencies = {}
    
    if "primary" in files_data or "shared" in files_data:
        for particle in files_data.get("primary", []) + files_data.get("shared", []):
            if isinstance(particle, dict) and "context" in particle and "imports_linked" in particle["context"]:
                file_path = particle["path"]
                for linked_import in particle["context"]["imports_linked"]:
                    source_file = linked_import.get("resolved_file", "")
                    if source_file and source_file != file_path:
                        if not feature_path or (source_file.startswith(feature_path) and file_path.startswith(feature_path)):
                            file_dependencies.setdefault(file_path, set()).add(source_file)
    else:
        for file_key, file_data in files_data.items():
            if isinstance(file_data, dict) and "particles" in file_data:
                for particle in file_data.get("particles", []):
                    if "imports_linked" in particle:
                        file_path = file_key
                        for linked_import in particle["imports_linked"]:
                            source_file = linked_import.get("resolved_file", "")
                            if source_file and source_file != file_path:
                                if not feature_path or (source_file.startswith(feature_path) and file_path.startswith(feature_path)):
                                    file_dependencies.setdefault(file_path, set()).add(source_file)
    
    for dependent_file, source_files in file_dependencies.items():
        for source_file in source_files:
            linked_graph["dependencies"].append({
                "source": source_file,
                "target": dependent_file,
                "type": "import"
            })
    
    logger.info(f"Linked dependencies in graph: {len(linked_graph['dependencies'])} connections, scoped to {feature_path or 'unscoped'}")
    return linked_graph

def traceReasoning(graph: Union[Dict[str, Any], List, Any]) -> Union[Dict[str, Any], List, Any]:
    if not isinstance(graph, dict) or "files" not in graph:
        return graph
    
    traced_graph = deepcopy(graph)
    function_map = {}
    
    files_data = traced_graph.get("files", {})
    if "primary" in files_data or "shared" in files_data:
        for particle in files_data.get("primary", []) + files_data.get("shared", []):
            if isinstance(particle, dict) and "context" in particle:
                functions = particle["context"].get("attributes", {}).get("functions", {})
                if isinstance(functions, dict):
                    for func_name, lines in functions.items():
                        function_map[func_name] = {
                            "file": particle["path"],
                            "particle_id": particle.get("id", particle["path"]),
                            "particle": particle["context"]
                        }
                elif isinstance(functions, list):
                    for func in functions:
                        if isinstance(func, str):
                            func_name = func.split("(")[0].strip()
                            function_map[func_name] = {
                                "file": particle["path"],
                                "particle_id": particle.get("id", particle["path"]),
                                "particle": particle["context"]
                            }
                        elif isinstance(func, dict) and "name" in func:
                            function_map[func["name"]] = {
                                "file": particle["path"],
                                "particle_id": particle.get("id", particle["path"]),
                                "particle": particle["context"]
                            }
    
    call_traces = []
    if "primary" in files_data or "shared" in files_data:
        for particle in files_data.get("primary", []) + files_data.get("shared", []):
            if isinstance(particle, dict) and "context" in particle:
                calls = particle["context"].get("attributes", {}).get("calls", [])
                for call in calls:
                    call_name = call["name"] if isinstance(call, dict) else call.split("(")[0].strip() if "(" in call else call
                    if call_name in function_map:
                        call_trace = {
                            "caller": {
                                "file": particle["path"],
                                "particle_id": particle.get("id", particle["path"]),
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
    else:
        for file_key, file_data in files_data.items():
            if isinstance(file_data, dict) and "particles" in file_data:
                for particle in file_data.get("particles", []):
                    for call in particle.get("calls", []):
                        if isinstance(call, dict) and "name" in call:
                            call_name = call["name"]
                        elif isinstance(call, str):
                            call_name = call.split("(")[0].strip() if "(" in call else call
                        else:
                            continue
                        if call_name in function_map:
                            call_trace = {
                                "caller": {
                                    "file": file_key,
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
    
    traced_graph["reasoning_traces"] = call_traces
    logger.info(f"Traced reasoning in graph: {len(call_traces)} function call traces")
    return traced_graph