# Particle-Graph Architecture Document

## Project Overview

### Core Purpose
- Extract 95% of the application's narrative directly from the codebase
- Provide maximum context and relevancy for developers
- Optimize token usage efficiency
- Maintain up-to-date graph representation of code relationships

### Core Features

Particle-Graph is a system designed to analyze and generate graph representations of code components, particularly focusing on JavaScript/JSX codebases. The system extracts metadata ("particles") from source files, builds relationship graphs between components, and provides APIs for creating, updating, loading, and exporting these graphs that can be used for code analysis, onboarding and AI assistance.

### Core Aggregation

#### addParticle():
Focus: File-level metadata.
- Looks For: 
  - routes: Routes definition and usage patterns
  - props: Component props and their types
  - hooks: React hooks (e.g., useState, useEffect, useContext)
  - calls: API calls and function invocations
  - logic: Conditions + actions (e.g., if → console.error)
  - depends_on: Import/export relationships
  - jsx: JSX elements and component usage
  - comments: Documentation, TODOs, and code annotations

Aggregation type: Granular, per-file metadata collection.

#### exportGraph():
Focus: Aggregated graph—features or codebase.
- Looks For: 
  - nodes: Files with Particle data
  - edges: Dependency and relationship links
  - files: Comprehensive file dictionary
  - tech_stack: Libraries and frameworks used
  - state_machine: Application state logic
  - dependencies: Dependency counts and connections
  - metadata: Statistical information (e.g., node_count, file_count)
  - coverage_percentage: Analysis coverage metrics

Aggregation type: Big picture, relational data structure.

## Docker Implementation

Particle-Graph is designed to run both locally and in a Docker container, providing flexibility and consistent behavior across different environments. Docker containerization provides isolation, dependency management, and portability.

### Docker Container Structure

┌─────────────────────────────────────────────────────────────────┐
│                     Docker Container                            │
│                                                                 │
│  ┌─────────────────┐         ┌───────────────────────────────┐  │
│  │                 │         │                               │  │
│  │  Particle-Graph │         │ Project Files (Mounted Volume)│  │
│  │     Services    │◀────────│    /project/thy/today/        │  │
│  │                 │         │                               │  │
│  └─────────────────┘         └───────────────────────────────┘  │
│           │                                                      │
│           ▼                                                      │
│  ┌─────────────────┐                                             │
│  │                 │                                             │
│  │  Cache Storage  │                                             │
│  │                 │                                             │
│  └─────────────────┘                                             │
│                                                                  │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               │ JSON-RPC API
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│                       MCP Client/Host                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

### Path Resolution System

The PathResolver component is a critical part of the system that handles the complex path translations between the host machine and the Docker container. It ensures that file operations work seamlessly regardless of where the code is running.

#### Key PathResolver Responsibilities

1. **Environment Detection**:
   - Automatically detects whether the code is running in Docker or locally
   - Sets appropriate base paths and prefixes based on the detected environment

2. **Path Translation**:
   - Translates paths between host format (e.g., `/Users/Thy/project/`) and Docker format (e.g., `/project/thy/today/`)
   - Handles both absolute and relative path resolution

3. **Path Normalization**:
   - Ensures consistent path formats across different operations
   - Removes duplicate slashes, resolves parent directory references

4. **Cache Directory Management**:
   - Maintains isolated cache directories for Docker and local environments
   - Ensures cache persistence across container restarts

#### Path Resolution in Docker Context

When running in Docker, the PathResolver handles the following path transformations:

- **Host to Container**: `/Users/Thy/myproject/src/components` → `/project/thy/today/src/components`
- **Container to Host**: `/project/thy/today/src/components` → `/Users/Thy/myproject/src/components`

This bidirectional translation is crucial for operations like:
- Reading source files from mounted volumes
- Writing cache files to persistent storage
- Reporting file locations in logs and error messages

## MCP Client/Host Integration

The Particle-Graph system integrates with the MCP (Model Control Protocol) client/host architecture to provide a seamless interface for AI assistants and other tools.

### Communication Flow

┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│                 │ JSON-RPC │                 │         │                 │
│   MCP Client    │─────────▶│  Particle-Graph │─────────▶│  File System    │
│                 │◀─────────│  (Docker)       │◀─────────│                 │
└─────────────────┘         └─────────────────┘         └─────────────────┘

### MCP Integration Components

1. **JSON-RPC API Layer**:
   - Exposes standardized functions like `createGraph`, `loadGraph`, `exportGraph`, and `listGraph`
   - Provides consistent response formatting suitable for MCP client consumption
   - Handles error conditions with structured error messages

2. **Response Formatting**:
   - All API functions return responses in a standard format:
     ```json
     {
       "content": [{"type": "text", "text": "Operation result details"}],
       "isError": false
     }
     ```
   - Error responses include helpful diagnostic information:
     ```json
     {
       "content": [{"type": "text", "text": "Error: Failed to locate path"}],
       "isError": true
     }
     ```

3. **Path Context Preservation**:
   - The MCP client can provide paths in host format
   - PathResolver transparently translates these to the appropriate Docker paths
   - Results are translated back to host paths for display to the user

### Common Use Cases

1. **Creating Graphs from MCP Client**:
   - MCP client requests `createGraph("components/Features/Events")`
   - PathResolver resolves this to `/project/thy/today/components/Features/Events` in Docker
   - Results reference paths in host format for user-friendly output

2. **Exporting Graphs**:
   - MCP client requests `exportGraph("Events")`
   - System locates the cached graph, resolves all file paths to host format
   - Returns a structured response with the export location in host path format

3. **Listing Available Graphs**:
   - MCP client requests `listGraph()`
   - System returns formatted text listing all available graphs with their timestamps
   - Response is structured for direct display in MCP client UI

## Directory Structure

```
/Users/Thy/Particle-Graph/
├── src/                         # Main source code directory
│   ├── api/                     # API endpoints for end-user operations
│   │   ├── add_particle.py      # Add particles to individual files
│   │   ├── create_graph.py      # Create new particle graphs
│   │   ├── delete_graph.py      # Delete existing graphs
│   │   ├── export_graph.py      # Export graphs to JSON files
│   │   ├── list_graph.py        # List available graphs in cache
│   │   ├── load_graph.py        # Load graphs from cache or files
│   │   └── update_graph.py      # Update existing graphs
│   │
│   ├── core/                    # Core functionality and utilities
│   │   ├── cache_manager.py     # Centralized cache management system
│   │   ├── file_processor.py    # Process files and directories
│   │   └── path_resolver.py     # Handle path resolution, normalization, directory management, and translation between host and container paths
│   │   
│   │
│   ├── graph/                   # Graph generation and analysis
│   │   ├── aggregate_app_story.py # Aggregate related app components
│   │   ├── graph_support.py     # Functions for enhancing and processing graphs
│   │   └── tech_stack.py        # Identify technology stack from code
│   │
│   ├── helpers/                 # Helper utilities
│   │   ├── config_loader.py     # Load configuration
│   │   ├── data_cleaner.py      # Data cleaning and filtering utilities
│   │   ├── dir_scanner.py       # Directory scanning utilities
│   │   ├── gitignore_parser.py  # Parse gitignore files
│   │   └── project_detector.py  # Detect project roots
│   │
│   └── particle/                # Particle generation and handling
│       ├── dependency_tracker.py # Track dependencies between components
│       ├── file_handler.py      # Handle file operations
│       ├── particle_generator.py # Generate particle metadata from code
│       ├── particle_support.py  # Support functions for particles
│       └── js/                  # JavaScript utilities    
│           ├── babel_parser_core.js  # Parse JS/JSX files with Babel
│           └── metadata_extractor.js # Extract metadata from parsed code
│
├── doc/                         # Documentation
├── dev/                         # Development utilities
└── legacy/                      # Legacy code (for reference)
```

## Component Responsibilities

### API Layer (`src/api/`)

The API layer provides high-level functions for end-users to interact with the Particle-Graph system.

| File | Responsibility |
|------|----------------|
| `add_particle.py` | Create and attach particle metadata to individual source files |
| `create_graph.py` | Generate new particle graphs from source files or directories, with support for single features, multi-feature aggregation, and full codebase analysis |
| `delete_graph.py` | Remove graphs from the cache and disk |
| `export_graph.py` | Export graphs to JSON files for external use, with various filtering and formatting options |
| `list_graph.py` | List all available graphs in the cache with timestamp information |
| `load_graph.py` | Load graphs from cache or parse from files, with data validation and sanitization |
| `update_graph.py` | Update existing graphs with new information |

### Core Layer (`src/core/`)

The core layer handles the fundamental operations and data transformations.

| File | Responsibility |
|------|----------------|
| `cache_manager.py` | Centralized cache management with in-memory/disk storage, thread safety, automatic persistence, and comprehensive statistics tracking |
| `file_processor.py` | Process directories and files, including filtering by extension and handling gitignore rules |
| `path_resolver.py` | Handle path resolution, normalization, directory management, and translation between host and container paths |

### Graph Layer (`src/graph/`)

The graph layer handles building and analyzing relationships between components.

| File | Responsibility |
|------|----------------|
| `aggregate_app_story.py` | Aggregate related app components into a coherent story structure |
| `graph_support.py` | Enhance and process graph structures with dependency linking, reasoning traces, and metadata enrichment |
| `tech_stack.py` | Analyze code to identify technologies and libraries used, with framework detection and version tracking |

### Helpers (`src/helpers/`)

Supporting utilities for the overall system.

| File | Responsibility |
|------|----------------|
| `config_loader.py` | Load and parse configuration settings from various sources |
| `data_cleaner.py` | Clean and filter data structures including removing empty values while preserving critical fields |
| `dir_scanner.py` | Scan directories with pattern matching, exclusion filters, and performance optimizations |
| `gitignore_parser.py` | Parse gitignore files for pattern matching and file exclusion |
| `project_detector.py` | Detect and validate project root directories based on structure markers |

### Particle Layer (`src/particle/`)

The particle layer manages the creation and handling of code metadata.

| File | Responsibility |
|------|----------------|
| `dependency_tracker.py` | Track and analyze dependencies between components with detailed relationship mapping |
| `file_handler.py` | Handle file operations including reading, writing, and caching particle data |
| `particle_generator.py` | Generate particle metadata by parsing source code with language-specific processors |
| `particle_support.py` | Utilities for particle operations, logging, and support functions |

### JavaScript Utilities (`js/`)

JavaScript tools used by the Python code.

| File | Responsibility |
|------|----------------|
| `babel_parser_core.js` | Parse JavaScript/JSX files using Babel to extract component information |
| `metadata_extractor.js` | Extract metadata from parsed code including imports, exports, hooks, and JSX structure |

## Key Functions by File

This section provides a list of the main functions defined in each file of the Particle-Graph codebase.

### API Layer (`src/api/`)

#### `add_particle.py`
- `addParticle(file_path: str)` - Add particle metadata to a specific file
- `addParticleByExtension(path: str, extension: str)` - Process multiple files by extension

#### `create_graph.py`
- `createGraph(path: str)` - Create a particle graph for a given path
- `processFiles(feature_path: str)` - Process files to build a list of files with particle data
- `count_js_files(feature_path: str)` - Count total JavaScript files for coverage calculation

#### `delete_graph.py`
- `deleteGraph(path: str)` - Delete a graph by feature name or path

#### `export_graph.py`
- `exportGraph(path: str)` - Export a graph to a JSON file with formatting options

#### `list_graph.py`
- `listGraph()` - List all available graphs in the cache with timestamps and statistics

#### `load_graph.py`
- `loadGraph(path: str)` - Load a graph for a specified feature
- `sanitize_graph(graph: Dict)` - Clean up a graph for presentation

#### `update_graph.py`
- `updateGraph(path: str)` - Update an existing graph with new information

### Core Layer (`src/core/`)

#### `cache_manager.py`
- `get(key: str)` - Retrieve a value from the cache
- `set(key: str, value: Any, persist: bool)` - Store a value in the cache
- `delete(key: str)` - Remove a value from the cache
- `has_key(key: str)` - Check if a key exists in the cache
- `keys()` - Get a list of all keys in the cache
- `persist_all()` - Save all cached data to disk
- `load_from_disk()` - Load all cache files into memory
- `clear_all()` - Clear all cached data
- `get_stats()` - Get cache statistics

#### `file_processor.py`
- `process_directory(directory: str, extensions: List[str])` - Process all files in a directory with given extensions
- `is_excluded(file_path: str, exclusion_patterns: List[str])` - Check if a file should be excluded
- `read_file_contents(file_path: str)` - Read and decode file contents safely

#### `path_resolver.py`
- `resolve_path(path: str)` - Resolve a path to an absolute path
- `relative_to_project(path: str)` - Get a path relative to the project root
- `get_particle_path(file_path: str)` - Get the cache path for a particle file
- `get_graph_path(feature_name: str)` - Get the cache path for a graph file
- `read_json_file(file_path: Path)` - Read and parse a JSON file
- `write_json_file(file_path: Path, data: Any)` - Write data to a JSON file

### Graph Layer (`src/graph/`)

#### `aggregate_app_story.py`
- `aggregate_app_story(particles: List[Dict])` - Aggregate particles into a coherent application story
- `identify_entry_points(particles: List[Dict])` - Identify main entry points of the application
- `extract_key_flows(particles: List[Dict])` - Extract key user flows from the application

#### `graph_support.py`
- `postProcessGraph(graph: Dict)` - Enhance a graph with metadata and post-processing
- `linkDependencies(graph: Dict)` - Establish connections between particles based on imports and exports
- `traceReasoning(graph: Dict)` - Trace function call chains and data flow within the graph

#### `tech_stack.py`
- `get_tech_stack(files: List[Dict])` - Analyze files to identify the technology stack
- `identify_frameworks(imports: List[str])` - Identify frameworks from import statements
- `classify_dependencies(deps: Dict)` - Classify dependencies by type and importance

### Helpers (`src/helpers/`)

#### `config_loader.py`
- `load_config(config_path: str)` - Load configuration from a file
- `get_config_value(key: str, default: Any)` - Get a configuration value with fallback
- `set_config_value(key: str, value: Any)` - Set a configuration value

#### `data_cleaner.py`
- `filter_empty(data: Any, preserve_tech_stack: bool)` - Remove empty values from data structures
- `sanitize_strings(data: Any)` - Clean and normalize string values

#### `dir_scanner.py`
- `scan_directory(directory: str, pattern: str)` - Scan a directory for files matching a pattern
- `scan_with_exclusion(directory: str, pattern: str, exclusions: List[str])` - Scan with exclusion patterns

#### `gitignore_parser.py`
- `load_gitignore(directory: str)` - Load and parse gitignore rules
- `match_file(path: str)` - Check if a file matches gitignore patterns

#### `project_detector.py`
- `find_project_root(directory: str)` - Find the root directory of a project
- `is_project_directory(directory: str)` - Check if a directory is a project root

### Particle Layer (`src/particle/`)

#### `dependency_tracker.py`
- `track_dependencies(particle: Dict)` - Track dependencies in a particle
- `map_dependency_network(particles: List[Dict])` - Create a dependency network map

#### `file_handler.py`
- `read_particle(file_path: str)` - Read particle data for a file
- `write_particle(file_path: str, particle: Dict)` - Write particle data to cache
- `read_file(file_path: str)` - Read a file's contents
- `write_file(file_path: str, contents: str)` - Write contents to a file

#### `particle_generator.py`
- `generate_particle(file_path: str, file_content: str)` - Generate particle metadata from file content
- `extract_imports(ast: Dict)` - Extract import statements from AST
- `extract_hooks(ast: Dict)` - Extract React hooks from AST
- `extract_jsx(ast: Dict)` - Extract JSX elements from AST

#### `particle_support.py`
- `setup_logging()` - Configure logging system
- `clean_particle(particle: Dict)` - Clean up particle data
- `merge_particles(particles: List[Dict])` - Merge multiple particles

## Data Flow Diagram

The following diagram illustrates the flow of data through the Particle-Graph system:

```
┌─────────────────┐   ┌────────────────────┐     ┌────────────────┐
│                 │   │                    │     │                │
│  Source Files   │──▶│  particle_generator│────▶│  Particle Data │
│  (.js, .jsx)    │   │                    │     │                │
└─────────────────┘   └────────────────────┘     └────────────────┘
                                                         │
                                                         ▼
┌─────────────────┐   ┌────────────────────┐     ┌────────────────┐
│                 │   │                    │     │                │
│   Graph API     │◀──│    graph_support   │◀────│  Cache Manager │
│                 │   │                    │     │                │
└─────────────────┘   └────────────────────┘     └────────────────┘
          │
          ▼
┌─────────────────────┐   ┌────────────────────┐
│                     │   │                    │
│  Graph JSON Output  │   │   exportGraph()    │
│                     │◀──│                    │
└─────────────────────┘   └────────────────────┘
```

## Key Processing Flows

### Particle Generation Flow

1. File is read from the filesystem
2. Content is parsed using appropriate parser (e.g., Babel for JS/JSX)
3. AST is analyzed for metadata:
   - Imports and exports
   - Component definitions
   - Hook usage
   - JSX elements
   - Logic blocks
4. Metadata is assembled into a "particle"
5. Particle is cached for future use

### Graph Generation Flow

1. Target path (feature/directory) identified
2. Files are scanned and filtered
3. Each file's particle data is retrieved or generated
4. Files are categorized (primary, shared, tests)
5. Technology stack is analyzed
6. Dependencies are linked between components
7. App story is aggregated from particles
8. Reasoning traces are established
9. Graph metadata is calculated (coverage, counts)
10. Final graph is cached and returned

## Graph Post-Processing

The `postProcessGraph()` function enhances raw graph data with:

1. Additional metadata and statistics
2. File and node counts
3. Dependency links between components
4. Reasoning traces through the codebase

The `linkDependencies()` function establishes connections by:

1. Mapping all exports across the codebase
2. Connecting imports to their source exports
3. Creating a dependency network between files
4. Adding bi-directional relationships to the graph

The `traceReasoning()` function traces call chains and data flow:

1. Collects function definitions from all files
2. Identifies function calls across the codebase
3. Establishes caller-callee relationships
4. Maps data transformation paths
5. Connects state mutations and side effects
