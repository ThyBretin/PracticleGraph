# Particle-Graph: Technical Architecture

## System Overview

Particle-Graph is a codebase analysis tool that automatically generates metadata for React Native/Expo components. It extracts props, hooks, API calls, key logic patterns, and dependencies, then embeds this information as structured `Particle` objects directly in source files. The system aggregates these objects to create comprehensive dependency graphs and tech stacks.

## Architecture

- **Containerized Environment**: Dockerized Python application with Node.js/Babel parser integration
- **Mounted Volume**: Maps host path `/Users/Thy/Today` to container path `/project`
- **MCP Server**: FastMCP-based tool server exposing key analysis functions

## Core Components

### Analysis Pipeline
1. **Input Processing**: Path mapping between host and container environments
2. **AST Parsing**: Babel parser extracts component metadata via abstract syntax tree analysis
3. **Metadata Generation**: Builds JSON structure with purpose, props, hooks, calls, logic, dependencies
4. **File Manipulation**: Embeds `Particle` objects directly in source files

### Key Files

- **babel_parser.js**: Node.js script using Babel AST to extract component metadata
- **addParticle.py**: Handles single-file analysis with subprocess communication to Babel
- **addAllParticle.py**: Implements recursive directory traversal with gitignore support
- **file_handler.py**: Manages file I/O with path translation and JSON formatting
- **particle_utils.py**: Contains shared utilities and logging infrastructure
- **createParticle.py**: Creates feature-based Particle Graphs by crawling directories
- **createCodebaseParticle.py**: Creates whole-codebase Particle Graph from all available Particles
- **loadGraph.py**: Loads specific feature graphs with support for feature aggregation
- **loadCodebaseGraph.py**: Loads the complete codebase graph with a single command
- **exportGraph.py**: Exports feature-based graphs to JSON files
- **exportCodebaseGraph.py**: Exports the entire codebase graph to a JSON file
- **server.py**: MCP server entry point that registers analysis tools
- **tech_stack.py**: Processes and categorizes dependencies from package.json files

## Technical Details

### Path Handling
- Smart path translation between host and container paths
- Support for both absolute and relative paths
- Respects `.gitignore` patterns during batch processing

### JSON Processing
- Automatic filtering of empty arrays in output (props, hooks, calls, key_logic, depends_on)
- Two-stage filtering approach (JS-side and Python-side) for reliability
- JSON validation to ensure consistent output format

### Particle Format
```javascript
export const Particle = {
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

1. **addParticle(file_path, rich=True)**
   - Analyzes single file
   - Returns detailed operation status with JSON metadata

2. **addAllParticle(root_dir="/project", rich=True)**
   - Processes all JS/JSX files in directory recursively
   - Handles path translation and respects gitignore
   - Returns summary with modified file count

3. **createParticle(feature_path)**
   - Creates a feature-based Particle Graph by crawling a specific directory
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

Particle-Graph supports two complementary approaches to codebase analysis:

1. **Feature-Based Workflow**:
   - Traditional approach organizing code by feature directories
   - Creates focused graphs for specific application domains
   - Useful for large projects with clear separation of concerns

2. **Codebase-Wide Workflow** (New):
   - Repository-agnostic approach for any folder structure
   - Works with standard layouts (src/, components/, etc.)
   - Creates a single comprehensive graph of the entire codebase
   - Commands: `createParticle("codebase")`, `loadGraph("codebase")`, `exportGraph("codebase")`

Both approaches share the same command interface with special parameter handling.

## Deployment Instructions

```bash
# Build the container
docker build -t particle-graph .

# Run the MCP server with mounted volume
docker run -m 2g -v /Users/Thy/Today:/project -i particle-graph
```

## Implementation Considerations

- AST parsing handles complex React patterns including functional components, hooks, and JSX
- Optimized for accuracy over raw performance
- Minimal external dependencies for long-term maintainability
- Clear separation between parsing (Node.js) and orchestration (Python) layers
- Delegation pattern for extending functionality without modifying core components

## Current Architecture Analysis and Issues

The current architecture has several strengths but also exhibits signs of technical debt that require attention:

### Strengths
- **Effective Modularity**: Clean separation between Node.js parsing and Python orchestration
- **Docker Containerization**: Provides consistent environments across different host systems
- **Flexible API**: Both file-specific and directory-wide analysis options
- **Gitignore Support**: Respects standard development patterns for exclusions

### Pain Points and Issues
1. **Error Handling**: Many functions lack robust error handling, leading to crashes on edge cases:
   - Index errors when processing route data
   - Unhandled exceptions in sub-component processing
   - Missing type validation before accessing properties

2. **Path Translation Complexity**: Multiple approaches to path translation create confusion:
   - Inconsistent handling between addParticle and addAllParticle
   - Redundant path conversion logic scattered across files

3. **Tech Stack Analysis**: Current implementation has robustness issues:
   - Depends too heavily on package.json structure being consistent
   - Single point of failure in dependency categorization

4. **Code Organization**: Functionality is sometimes spread across multiple files in ways that make maintenance difficult:
   - Key utility functions duplicated across files
   - Inconsistent module interfaces

## Proposed Architecture Improvements

### 1. Code Structure Reorganization
```
Particle-Graph/
├── server.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── README.md
├── src/
│   ├── api/
│   │   ├── add_particle.py
│   │   ├── create_graph.py
│   │   ├── delete_graph.py
│   │   ├── export_graph.py
│   │   ├── list_graph.py
│   │   ├── load_graph.py
│   │   └── update_graph.py
│   ├── core/
│   │   ├── dependency_tracker.py  # Your name
│   │   ├── file_handler.py
│   │   └── particle_utils.py
│   ├── analysis/
│   │   └── tech_stack.py
│   └── utils/
│       ├── check_root.py        # Keep for now
│       ├── config_loader.py     # Add if not there
│       └── list_dir.py          # Keep for now
├── legacy/
│   ├── addParticle.py
│   ├── addAllParticle.py
│   ├── createParticle.py
│   ├── createCodebaseParticle.py
│   ├── exportGraph.py
│   ├── exportCodebaseGraph.py
│   ├── loadGraph.py
│   ├── loadCodebaseGraph.py
│   ├── deleteParticle.py
│   ├── updateParticle.py
├── js/
│   └── babel_parser.js
├── dev/
│   └── debug_graph.py
└── doc/
    ├── Particle.md
    ├── Project-Refactoring.md
```

### 2. Defensive Programming Strategy
- **Input Validation**: Implement validation for all public API functions
- **Type Checking**: Add type annotations and runtime checks for critical code paths
- **Consistent Error Handling**: Standardize error handling with custom exceptions
- **Graceful Degradation**: Allow partial results when full analysis fails

### 3. Technical Improvements
- **Path Abstraction**: Create a dedicated PathResolver class to handle all path translations
- **Caching Layer**: Implement smarter caching for parsed results
- **Memory Efficiency**: Reduce redundant data structures
- **Parallel Processing**: Add option for multi-threaded analysis of large codebases

### 4. Documentation and Testing
- **API Documentation**: Create comprehensive API docs for all public functions
- **Architecture Diagram**: Develop visual representation of system components
- **Test Suite**: Implement thorough unit and integration tests
- **Example Workflows**: Document common usage patterns with examples

### 5. Maintainability Focus
- **Config-Based Approach**: Move hardcoded values to configuration files
- **Plugin Architecture**: Enable extensions for custom analysis needs
- **Versioned API**: Properly version the API for backward compatibility
- **Telemetry**: Add optional usage statistics for error reporting

Implementing these changes would significantly improve robustness, maintainability, and extensibility of the Particle-Graph project, while keeping its core functionality intact.
