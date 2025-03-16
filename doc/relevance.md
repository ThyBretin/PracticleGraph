##babel_parser_core.js

const { parse } = require('@babel/parser');
const fs = require('fs');
const path = require('path');

function parseFile(filePath) {
  try {
    const absolutePath = filePath.startsWith('/project/') ? filePath : path.join('/project', filePath);
    console.error(`Reading file from: ${absolutePath}`);
    const code = fs.readFileSync(absolutePath, 'utf-8');

    // TypeScript heuristic
    const hasTypeScriptSyntax =
      code.includes(': ') ||
      code.includes('<T>') ||
      code.includes('interface ') ||
      code.includes('type ') ||
      absolutePath.endsWith('.ts') ||
      absolutePath.endsWith('.tsx');

    const plugins = ['jsx', 'decorators-legacy'];
    if (hasTypeScriptSyntax) {
      plugins.push('typescript');
    } else {
      plugins.push('flow');
    }

    const ast = parse(code, {
      sourceType: 'module',
      plugins,
      tokens: true,
      comments: true,
    });

    return { ast, code }; // Return code for existing Particle merge later
  } catch (error) {
    console.error(`Error parsing ${filePath}: ${error.message}`);
    throw error; // Let caller handle
  }
}

if (require.main === module) {
  const filePath = process.argv[2];
  if (!filePath) {
    console.error('No file path provided');
    process.exit(1);
  }
  const { ast, code } = parseFile(filePath);
  console.log(JSON.stringify({ ast, code }));
}

module.exports = { parseFile };


## metadata_extractor.js


const path = require('path');
const fs = require('fs');

function extractMetadata(ast, code, filePath, rich = false) {
  const fileExt = path.extname(filePath);
  let particle = {
    path: path.relative('/project', filePath),
    type: fileExt === '.jsx' || fileExt === '.tsx' ? 'component' : 'file',
    purpose: `Handles ${path.basename(filePath, fileExt).toLowerCase()} functionality`,
    props: [],
    hooks: [],
    calls: [],
    logic: [],
    depends_on: [],
    jsx: [],
    state_machine: null,
    routes: [],
    comments: [],
    used_by: [],
  };

  // Comments (unchanged)
  if (ast.comments && ast.comments.length > 0) {
    ast.comments.forEach((comment) => {
      const text = comment.value.trim().replace(/^\*+\s*/gm, '').replace(/\n\s*\*\s*/g, '\n');
      if (text.toLowerCase().includes('todo') || text.toLowerCase().includes('fixme')) {
        particle.comments.push({ type: 'todo', text });
      } else if (comment.type === 'CommentBlock' && comment.loc.start.line <= 20) {
        particle.comments.push({ type: 'doc', text });
        if (text.includes('component') || text.includes('Component')) {
          particle.purpose = text.split('\n')[0].trim();
        }
      }
    });
  }

  function walk(node) {
    if (!node) return;

    if (node.type === 'ImportDeclaration') {
      const source = node.source.value;
      const specifiers = node.specifiers
        .map((spec) =>
          spec.type === 'ImportDefaultSpecifier' ? spec.local.name : spec.imported?.name || null
        )
        .filter(Boolean);
      particle.depends_on.push({ source, specifiers: specifiers.length > 0 ? specifiers : null });
      console.error(`Found import: ${source}`);
    }

    if (node.type === 'CallExpression') {
      const callee =
        node.callee.name ||
        (node.callee.property && `${node.callee.object?.name}.${node.callee.property.name}`);
      if (callee?.startsWith('use')) {
        particle.hooks.push({ name: callee });
      }
      if (callee === 'fetch' || ['axios', 'supabase'].includes(node.callee.object?.name)) {
        particle.calls.push({ name: callee });
      }
    }

    for (const key in node) if (node[key] && typeof node[key] === 'object') walk(node[key]);
  }

  function enhanceWalk(node) {
    if (!node) return;

    if (node.type === 'IfStatement' && node.test) {
      let condition = '';
      if (node.test.type === 'Identifier') {
        condition = node.test.name;
      } else if (node.test.type === 'UnaryExpression' && node.test.operator === '!') {
        if (
          node.test.argument?.type === 'CallExpression' &&
          node.test.argument.callee?.property?.name === 'includes'
        ) {
          const arg = node.test.argument.arguments[0];
          condition = arg?.name || arg?.value || 'check';
        }
      } else if (node.test.type === 'BinaryExpression') {
        condition = `${node.test.left?.name || node.test.left?.value || ''} ${node.test.operator} ${node.test.right?.name || node.test.right?.value || ''}`;
      } else if (node.test.type === 'LogicalExpression') {
        condition = `${node.test.left?.name || 'condition'} ${node.test.operator} ${node.test.right?.name || 'condition'}`;
      }

      if (condition) {
        let action = 'handles condition';
        if (node.consequent.type === 'BlockStatement') {
          node.consequent.body.forEach((stmt) => {
            if (stmt.type === 'ExpressionStatement' && stmt.expression?.type === 'CallExpression') {
              const callee =
                stmt.expression.callee?.name ||
                (stmt.expression.callee?.property?.name &&
                  `${stmt.expression.callee.object?.name}.${stmt.expression.callee.property.name}`);
              if (callee === 'console.error') {
                action = 'calls console.error';
              }
            }
          });
        }
        particle.logic.push({ condition, action });
        console.error(`Found logic: ${condition} -> ${action}`);
      }
    }

    for (const key in node) if (node[key] && typeof node[key] === 'object') enhanceWalk(node[key]);
  }

  walk(ast.program);
  if (rich) enhanceWalk(ast.program);

  // Merge with existing Particle
  const existingMatch = code.match(/export const Particle = \{[\s\S]*?\};/);
  if (existingMatch) {
    try {
      const cleanedCode = existingMatch[0].replace('export const Particle =', '').trim().replace(/;$/, '');
      const existing = eval(`(${cleanedCode})`);
      particle.purpose = existing.purpose || particle.purpose;
      ['props', 'hooks', 'calls', 'logic', 'depends_on', 'jsx', 'routes', 'comments'].forEach((field) => {
        if (existing[field]) {
          if (typeof existing[field][0] !== 'object') {
            particle[field] = [...new Set([...(existing[field] || []), ...particle[field]])];
          } else {
            const merged = [...existing[field]];
            particle[field].forEach((item) => {
              if (!merged.some((m) => JSON.stringify(m) === JSON.stringify(item))) merged.push(item);
            });
            particle[field] = merged;
          }
        }
      });
    } catch (e) {
      console.error(`Failed to parse existing Particle in ${filePath}: ${e.message}`);
    }
  }

  // Filter empty fields
  Object.keys(particle).forEach((key) => {
    if (Array.isArray(particle[key]) && particle[key].length === 0) delete particle[key];
    if (key === 'state_machine' && (!particle[key] || (particle[key].states && particle[key].states.length === 0)))
      delete particle[key];
  });

  return particle;
}

if (require.main === module) {
  const filePath = process.argv[2];
  if (!filePath) {
    console.error('No file path provided');
    process.exit(1);
  }
  let astInput = '';
  process.stdin
    .setEncoding('utf8')
    .on('data', (chunk) => (astInput += chunk))
    .on('end', () => {
      try {
        const ast = JSON.parse(astInput);
        const absolutePath = filePath.startsWith('/project/') ? filePath : path.join('/project', filePath);
        const code = fs.readFileSync(absolutePath, 'utf-8');
        const rich = process.env.RICH_PARSING === '1';
        const particle = extractMetadata(ast, code, filePath, rich);
        // Single-line JSON output
        console.log(JSON.stringify(particle));
      } catch (error) {
        console.error(`Error processing ${filePath}: ${error.message}`);
        process.exit(1);
      }
    });
}

module.exports = { extractMetadata };

## particle_generator.py

import subprocess
import json
import os
from pathlib import Path

from src.particle.file_handler import read_file, write_particle
from src.particle.particle_support import logger

PROJECT_ROOT = "/project"

def generate_particle(file_path: str = None, rich: bool = True) -> dict:
    """
    Generate Particle metadata for a single JavaScript/JSX file.
    
    Args:
        file_path: Path to the JS/JSX file to analyze (absolute or relative to PROJECT_ROOT)
        rich: If True, include detailed metadata including key_logic and depends_on
        
    Returns:
        dict: Result containing Particle data and operation status
    """
    logger.info(f"Starting generate particle with file_path: {file_path}")
    if not file_path:
        logger.error("No file_path provided to generate particle")
        return {"error": "No file_path provided"}

    # Handle paths that might contain the host machine path
    host_prefix = "/Users/Thy/Today/"
    if file_path.startswith(host_prefix):
        relative_path = file_path[len(host_prefix):]
        logger.warning(f"Converted host path '{file_path}' to relative: '{relative_path}'")
    elif file_path.startswith(PROJECT_ROOT):
        relative_path = file_path[len(PROJECT_ROOT) + 1:]  # Strip '/project/'
    else:
        relative_path = file_path

    absolute_path = Path(PROJECT_ROOT) / relative_path
    logger.debug(f"Computed relative_path: {relative_path}")
    logger.debug(f"Computed absolute_path: {absolute_path}")

    content, error = read_file(relative_path)
    if error:
        logger.error(f"File read failed for {relative_path}: {error}")
        return {"error": f"Read failed: {error}"}

    try:
        node_path = str(absolute_path)
        # Step 1: Generate AST with babel_parser_core.js
        cmd = ['node', '/app/src/particle/js/babel_parser_core.js', node_path]
        env = os.environ.copy()
        env['RICH_PARSING'] = '1'  # Always rich now, kept for compatibility
        ast_result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        if not ast_result.stdout.strip():
            logger.error(f"Empty AST output from Babel for {relative_path}")
            return {"error": "Babel AST generation produced empty output"}
        ast_data = json.loads(ast_result.stdout)
        
        # Step 2: Extract metadata with metadata_extractor.js
        cmd = ['node', '/app/src/particle/js/metadata_extractor.js', node_path]
        result = subprocess.run(
            cmd,
            input=json.dumps(ast_data['ast']),
            capture_output=True,
            text=True,
            check=True,
            env=env
        )
        if not result.stdout.strip():
            logger.error(f"Empty metadata output from Babel for {relative_path}")
            return {"error": "Babel metadata extraction produced empty output"}
        
        context = json.loads(result.stdout)
        filtered_context = {k: v for k, v in context.items() if v}  # Filter falsy values
        export_str, error = write_particle(relative_path, filtered_context)
        if error:
            return {"error": f"Write failed: {error}"}

        # Generate summary
        summary_fields = []
        for field_name, display_name in [
            ('props', 'props'),
            ('hooks', 'hooks'),
            ('calls', 'calls'),
            ('logic', 'logic conditions'),
            ('depends_on', 'dependencies'),
            ('jsx', 'JSX elements'),
            ('routes', 'routes'),
            ('comments', 'comments')
        ]:
            if field_name in filtered_context:
                count = len(filtered_context[field_name])
                if count > 0:
                    summary_fields.append(f"{count} {display_name}")
        
        if 'state_machine' in filtered_context:
            states_count = len(filtered_context['state_machine'].get('states', []))
            if states_count > 0:
                summary_fields.append(f"state machine with {states_count} states")
        
        summary = ", ".join(summary_fields) or "No significant elements found"
        logger.info(f"Generated summary: {summary}")

        return {
            "content": [{"type": "text", "text": export_str}],
            "summary": summary,
            "status": "OK",
            "isError": False,
            "note": "Particle applied to file",
            "post_action": "read",
            "context": filtered_context
        }
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Babel failed for {relative_path}: {e.stderr}")
        return {"error": f"Babel parse failed: {e.stderr}"}
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON from Babel for {relative_path}: {e}")
        return {"error": f"Invalid JSON: {e}"}


## particle_support.py

import json
import logging
import os
import re
import fnmatch
from pathlib import Path
from typing import Dict, List, Set, Optional

app_path = os.getenv("PARTICLE_PATH", "/project")
particle_cache: Dict[str, dict] = {}
logger = logging.getLogger("ParticleGraph")

def infer_file_type(file_path: str) -> str:
    ext = Path(file_path).suffix.lower()
    if "test" in file_path.lower():
        return "test"
    if ext in (".jsx", ".tsx"):
        return "file"
    if "store" in file_path.lower():
        return "store"
    if "context" in file_path.lower():
        return "state"
    return "file"

def extract_particle_logic(file_path: str) -> dict:
    """Extract structured context (purpose, props, calls) from a file's Particle export."""
    full_path = Path(app_path) / file_path
    if not full_path.exists() or full_path.is_dir():
        return None
    
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Parse export const Particle
        context_match = re.search(r"export\s+const\s+Particle\s*=\s*(\{.*?\});", content, re.DOTALL)
        if context_match:
            try:
                context_str = context_match.group(1).replace("'", '"')
                context = eval(context_str, {"__builtins__": {}})
                return {
                    "purpose": context.get("purpose", ""),
                    "props": context.get("props", []),
                    "hooks": context.get("hooks", []),
                    "calls": context.get("calls", []),
                    "key_logic": context.get("key_logic", []),
                    "depends_on": context.get("depends_on", [])
                }
            except Exception as e:
                logger.debug(f"Invalid Particle in {file_path}: {e}")

        # Fallback: Infer from code
        context = {"purpose": "", "props": [], "hooks": [], "calls": []}
        # Props
        props = re.findall(r"const\s+\w+\s*=\s*\(\{([^}]*)\}\)", content)
        if props:
            context["props"] = [p.strip() for p in props[0].split(",") if p.strip()]
        for line in content.splitlines():
            if "fetch(" in line:
                url = re.search(r"fetch\(['\"]([^'\"]+)['\"]", line)
                if url:
                    context["calls"].append(url.group(1))
            if "supabase" in line:
                if "signIn" in line:
                    context["calls"].append("supabase.auth.signIn")
                elif "signOut" in line:
                    context["calls"].append("supabase.auth.signOut")
        return context if any(context.values()) else None

    except Exception as e:
        logger.debug(f"Error reading {file_path}: {e}")
        return None


## aggregate_app_story.py

from typing import Dict, List, Any, Union

def aggregate_app_story(particle_data: List[Dict]) -> Dict:
    """
    Aggregate routes, data, and components from particle data into an app_story.
    
    Args:
        particle_data: List of particle contexts from processed files
        
    Returns:
        Dict with routes, data, and components
    """
    routes = set()
    data = set()
    components = {}

    for particle in particle_data:
        # Extract routes from the routes field (added in enhanced parser)
        for route_entry in particle.get("routes", []):
            if isinstance(route_entry, dict) and "path" in route_entry:
                routes.add(route_entry["path"])
            elif isinstance(route_entry, str):
                routes.add(route_entry)

        # Extract routes from calls (supporting both old and new formats)
        for call in particle.get("calls", []):
            if isinstance(call, dict):
                # New format: calls as objects with name and args
                if "name" in call and call["name"] in ["router.push", "router.replace", "navigate", "navigateToTab"]:
                    if call.get("args") and isinstance(call["args"], list) and len(call["args"]) > 0:
                        routes.add(call["args"][0])
            elif isinstance(call, str):
                # Old format: calls as strings
                if call.startswith("router.push"):
                    route = call.split("router.push('")[1].rstrip("')") if "router.push('" in call else call
                    routes.add(route)

        # Data (agnostic—any fetch-like or query calls)
        for call in particle.get("calls", []):
            if isinstance(call, dict):
                # New format: calls as objects
                if "name" in call:
                    call_name = call["name"]
                    if any(kw in call_name for kw in ["fetch", "axios", "supabase"]):
                        if call.get("args"):
                            data_entry = f"{call_name}({', '.join(map(str, call['args']))})"
                        else:
                            data_entry = call_name
                        data.add(data_entry)
            elif isinstance(call, str):
                # Old format: calls as strings
                if any(kw in call for kw in ["fetch", "axios", ".from(", ".query("]):
                    data.add(call)

        # Components from JSX usage (supporting both old and new formats)
        for jsx in particle.get("jsx", []):
            if isinstance(jsx, dict):
                # New format: JSX as objects with tag
                if "tag" in jsx:
                    component = jsx["tag"]
                    components[component] = components.get(component, 0) + 1
            elif isinstance(jsx, str):
                # Old format: JSX as strings
                component = jsx.split(" on ")[-1] if " on " in jsx else jsx
                components[component] = components.get(component, 0) + 1

    return {
        "routes": list(routes),
        "data": list(data),
        "components": components
    }

## graph_support.py

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

## graph_support.py


import json
from pathlib import Path
import os
from src.particle.particle_support import app_path, logger

# Configurable tech categories (unchanged)
TECH_CATEGORIES = {
    "expo_sdk": {
        "packages": ["expo"],
        "format": lambda v: f"~{v}"
    },
    "core_libraries": {
        "packages": ["react", "react-dom", "react-native", "expo-router", "expo-.*"],
        "format": lambda v: v
    },
    "state_management": {
        "subcategories": {
            "global": ["zustand", "redux", "@reduxjs/toolkit", "mobx", "jotai"],
            "local": ["react"]  # React state inferred if React is present
        },
        "format": lambda v: f"{v['name']} {v['version']}" if v.get("name") else "React state"
    },
    "ui_libraries": {
        "packages": ["react-native-unistyles", "@mui/.*", "@material-ui/.*", "@shopify/.*"],
        "format": lambda v: v
    },
    "backend": {
        "subcategories": {
            "database": ["supabase", "@supabase/.*"],
            "http": ["axios", "fetch"]
        },
        "format": lambda v: f"{v['name']} {v['version']}" if "database" in v.get("subcategory", "") else v
    },
    "key_dependencies": {
        "packages": [],  # Populated dynamically with all significant deps
        "format": lambda v: v
    }
}

# get_tech_stack(entities: list) -> dict
# [x] What: Extracts a categorized tech stack with versions from package.json and file hints—e.g., Expo SDK, Core Libraries, State Management.
# Inputs: List of file entities (e.g., [{"path": "components/Core/Auth/hooks/useAuth.js", "type": "file"}, ...]).
# Actions: Loads dependencies from package.json, categorizes them using TECH_CATEGORIES config, infers additional tech from file extensions (e.g., .jsx -> React), and builds a structured tech stack dict.
# Output: Categorized tech stack JSON (e.g., {"expo_sdk": "~52.0.36", "core_libraries": {"react": "18.3.1"}, ...}).

def get_tech_stack(entities: list) -> dict:
    """Extract a categorized tech stack with versions from package.json, using configurable categories."""
    # Initialize with empty dicts for all categories to prevent None values
    tech_stack = {
        cat: {} if "subcategories" in TECH_CATEGORIES[cat] or cat in ["core_libraries", "ui_libraries", "key_dependencies"] else {}
        for cat in TECH_CATEGORIES
    }
    key_deps = {}

    # Determine package.json path based on app_path
    pkg_path = Path(app_path) / "package.json"
    
    # Check if we're in Docker and adjust path if needed
    if not pkg_path.exists() and os.path.exists("/project"):
        # Try Docker container path
        for possible_path in [
            Path("/project/thy/today/package.json"),
            Path("/project/package.json"),
            Path("/project/thy/package.json")
        ]:
            if possible_path.exists():
                pkg_path = possible_path
                logger.info(f"Found package.json at Docker path: {pkg_path}")
                break
    
    # Load package.json
    deps = {}
    try:
        if pkg_path.exists():
            with open(pkg_path, "r", encoding="utf-8") as f:
                pkg = json.load(f)
                deps = pkg.get("dependencies", {})
                logger.debug(f"Loaded {len(deps)} dependencies from {pkg_path}")
        else:
            logger.warning(f"Could not find package.json at {pkg_path}. Using fallback dependencies.")
            # Fallback dependencies for common js frameworks
            deps = {
                "react": "^18.0.0",
                "react-dom": "^18.0.0"
            }
    except Exception as e:
        logger.error(f"Failed to load {pkg_path}: {e}")
        # Still continue with empty deps

    # Categorize dependencies
    for dep, version in deps.items():
        matched = False
        for category, config in TECH_CATEGORIES.items():
            if category == "key_dependencies":
                continue
            if "subcategories" in config:
                for subcat, patterns in config["subcategories"].items():
                    if any(p == dep or (p.endswith(".*") and dep.startswith(p[:-2])) for p in patterns):
                        tech_stack[category][subcat] = config["format"]({"name": dep, "version": version, "subcategory": subcat})
                        matched = True
                        break
                if matched:
                    key_deps[dep] = version
                    break
            elif "packages" in config:
                if any(p == dep or (p.endswith(".*") and dep.startswith(p[:-2])) for p in config["packages"]):
                    if category == "expo_sdk":
                        tech_stack[category] = config["format"](version.lstrip("~^"))  # Strip ~ or ^ to avoid double ~
                    else:
                        tech_stack[category][dep] = config["format"](version)
                    matched = True
                    key_deps[dep] = version
                    break
        if not matched:
            key_deps[dep] = version

    # File extension hints
    react_detected = False
    js_detected = False
    
    # Only process entities if we have them
    if entities:
        for entity in entities:
            if isinstance(entity, dict) and "path" in entity:
                path = entity["path"]
                ext = Path(path).suffix.lower()
                if ext in (".js", ".jsx", ".tsx"):
                    js_detected = True
                if ext in (".jsx", ".tsx"):
                    react_detected = True
                    if "react" not in deps:
                        tech_stack["core_libraries"]["react"] = "unknown"
                if ext == ".tsx" and "typescript" not in deps:
                    key_deps["typescript"] = "unknown"

    # Infer React state if React is present
    if react_detected or "react" in deps:
        tech_stack["state_management"]["local"] = TECH_CATEGORIES["state_management"]["format"]({})
    
    # If we detected JavaScript files but no deps, add a default entry
    if js_detected and not deps:
        tech_stack["core_libraries"]["javascript"] = "detected"

    # Populate key_dependencies
    tech_stack["key_dependencies"] = {k: TECH_CATEGORIES["key_dependencies"]["format"](v) for k, v in key_deps.items()}

    # Clean up empty categories, but ensure we always return at least one category
    empty_categories = []
    for category in tech_stack.keys():
        if not tech_stack[category] or (isinstance(tech_stack[category], dict) and not any(tech_stack[category].values())):
            empty_categories.append(category)
    
    # Only remove empty categories if we'll have at least one left
    for category in empty_categories:
        if len(tech_stack) > len(empty_categories):
            del tech_stack[category]
    
    # If everything is empty, add a placeholder
    if not any(tech_stack.values()):
        tech_stack["detected"] = {"javascript": "files"}
    
    logger.info(f"Tech stack extracted: {list(tech_stack.keys())}")
    return tech_stack

    path
    type
    purpose
    depends_on
    jsx
    hooks
    calls
    logic
    core_rules
    props
    routes
    comments

    