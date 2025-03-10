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

3. **listGraph()**
   - Lists all available feature graphs in the codebase

4. **loadGraph(features)**
   - Loads specific feature graphs (comma-separated)
   - Merges multiple features when requested

5. **exportGraph(features)**
   - Exports graph data to JSON for external consumption

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
