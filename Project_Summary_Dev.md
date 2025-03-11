# Particule-Graph: Technical Architecture

## System Overview

Particule-Graph is a codebase analysis tool that automatically generates metadata for React Native/Expo components. It extracts props, hooks, API calls, key logic patterns, and dependencies, then embeds this information as structured `SubParticule` objects directly in source files. The system aggregates these objects to create comprehensive dependency graphs and tech stacks.

## Architecture

- **Containerized Environment**: Dockerized Python application with Node.js/Babel parser integration
- **Mounted Volume**: Maps host path `/Users/Thy/Today` to container path `/project`
- **MCP Server**: FastMCP-based tool server exposing key analysis functions

## Core Components

### Analysis Pipeline
1. **Input Processing**: Path mapping between host and container environments
2. **AST Parsing**: Babel parser extracts component metadata via abstract syntax tree analysis
3. **Metadata Generation**: Builds JSON structure with purpose, props, hooks, calls, logic, dependencies
4. **File Manipulation**: Embeds `SubParticule` objects directly in source files

### Key Files

- **babel_parser.js**: Node.js script using Babel AST to extract component metadata
- **addSubParticule.py**: Handles single-file analysis with subprocess communication to Babel
- **addAllSubParticule.py**: Implements recursive directory traversal with gitignore support
- **file_handler.py**: Manages file I/O with path translation and JSON formatting
- **particule_utils.py**: Contains shared utilities and logging infrastructure
- **createParticule.py**: Creates feature-based Particule Graphs by crawling directories
- **createCodebaseParticule.py**: Creates whole-codebase Particule Graph from all available SubParticules
- **loadGraph.py**: Loads specific feature graphs with support for feature aggregation
- **loadCodebaseGraph.py**: Loads the complete codebase graph with a single command
- **exportGraph.py**: Exports feature-based graphs to JSON files
- **exportCodebaseGraph.py**: Exports the entire codebase graph to a JSON file
- **server.py**: MCP server entry point that registers analysis tools

## Technical Details

### Path Handling
- Smart path translation between host and container paths
- Support for both absolute and relative paths
- Respects `.gitignore` patterns during batch processing

### JSON Processing
- Automatic filtering of empty arrays in output (props, hooks, calls, key_logic, depends_on)
- Two-stage filtering approach (JS-side and Python-side) for reliability
- JSON validation to ensure consistent output format

### SubParticule Format
```javascript
export const SubParticule = {
  "purpose": "Component's inferred purpose",
  "props": ["prop1", "prop2"],       // Only present if non-empty
  "hooks": ["useState", "useEffect"], // Only present if non-empty
  "calls": ["api.getData()"],         // Only present if non-empty
  "key_logic": ["Conditional rendering logic"], // Only present if non-empty
  "depends_on": ["react", "package-name"]  // Only present if non-empty
};
```

## API Reference

### Main Functions

1. **addSubParticule(file_path, rich=True)**
   - Analyzes single file
   - Returns detailed operation status with JSON metadata

2. **addAllSubParticule(root_dir="/project", rich=True)**
   - Processes all JS/JSX files in directory recursively
   - Handles path translation and respects gitignore
   - Returns summary with modified file count

3. **createParticule(feature_path)**
   - Creates a feature-based Particule Graph by crawling a specific directory
   - Special values: "codebase" or "all" to create a whole-codebase graph

4. **listGraph()**
   - Lists all available feature graphs in the codebase

5. **loadGraph(features)**
   - Loads specific feature graphs (comma-separated)
   - Merges multiple features when requested
   - Special values: "codebase" or "all" to load the whole-codebase graph

6. **exportGraph(features)**
   - Exports graph data to JSON for external consumption
   - Special values: "codebase" or "all" to export the whole-codebase graph

## Feature-Based vs. Codebase-Wide Analysis

Particule-Graph supports two complementary approaches to codebase analysis:

1. **Feature-Based Workflow**:
   - Traditional approach organizing code by feature directories
   - Creates focused graphs for specific application domains
   - Useful for large projects with clear separation of concerns

2. **Codebase-Wide Workflow** (New):
   - Repository-agnostic approach for any folder structure
   - Works with standard layouts (src/, components/, etc.)
   - Creates a single comprehensive graph of the entire codebase
   - Commands: `createParticule("codebase")`, `loadGraph("codebase")`, `exportGraph("codebase")`

Both approaches share the same command interface with special parameter handling.

## Deployment Instructions

```bash
# Build the container
docker build -t particule-graph .

# Run the MCP server with mounted volume
docker run -m 2g -v /Users/Thy/Today:/project -i particule-graph
```

## Implementation Considerations

- AST parsing handles complex React patterns including functional components, hooks, and JSX
- Optimized for accuracy over raw performance
- Minimal external dependencies for long-term maintainability
- Clear separation between parsing (Node.js) and orchestration (Python) layers
- Delegation pattern for extending functionality without modifying core components
