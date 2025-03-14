# Particle-Graph Architecture Document

## Project Overview

### Core Purpose
- Extract 95% of the application's narrative directly from the codebase
Provide maximum context and relevancy for developers
Optimize token usage efficiency
Maintain up-to-date graph representation of code relationships

### Core Features

Particle-Graph is a system designed to analyze and generate graph representations of code components, particularly focusing on JavaScript/JSX codebases. The system extracts metadata ("particles") from source files, builds relationship graphs between components, and provides APIs for creating, updating, loading, and exporting these graphs that can be used for code analysis, onboarding and AI assistance.

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
│       └── particle_support.py  # Support functions for particles
│       └── js/                  # JavaScript utilities    
│         ├── babel_parser_core.js  # Parse JS/JSX files with Babel
│         └── metadata_extractor.js # Extract metadata from parsed code
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
| `create_graph.py` | Generate new particle graphs from source files or directories |
| `delete_graph.py` | Remove graphs from the cache and disk |
| `export_graph.py` | Export graphs to JSON files for external use |
| `list_graph.py` | List all available graphs in the cache |
| `load_graph.py` | Load graphs from cache or parse from files |
| `update_graph.py` | Update existing graphs with new information |

### Core Layer (`src/core/`)

The core layer handles the fundamental operations and data transformations.

| File | Responsibility |
|------|----------------|
| `cache_manager.py` | Centralized cache management with in-memory/disk storage, thread safety, and automatic persistence |
| `file_processor.py` | Process directories and files, including filtering by extension and handling gitignore rules |
| `path_resolver.py` | Handle path resolution, normalization, directory management, and translation between host and container paths |

### Graph Layer (`src/graph/`)

The graph layer handles building and analyzing relationships between components.

| File | Responsibility |
|------|----------------|
| `aggregate_app_story.py` | Aggregate related app components into a coherent story structure |
| `graph_support.py` | Enhance and process graph structures with dependency linking and reasoning traces |
| `tech_stack.py` | Analyze code to identify technologies and libraries used |

### Helpers (`src/helpers/`)

Supporting utilities for the overall system.

| File | Responsibility |
|------|----------------|
| `config_loader.py` | Load and parse configuration settings |
| `data_cleaner.py` | Clean and filter data structures including removing empty values |
| `dir_scanner.py` | Scan directories with pattern matching and filtering |
| `gitignore_parser.py` | Parse gitignore files for pattern matching |
| `project_detector.py` | Detect and validate project root directories |

### Particle Layer (`src/particle/`)

The particle layer manages the creation and handling of code metadata.

| File | Responsibility |
|------|----------------|
| `dependency_tracker.py` | Track and analyze dependencies between components |
| `file_handler.py` | Handle file operations like reading and writing files |
| `particle_generator.py` | Generate particle metadata by parsing source code |
| `particle_support.py` | Utilities for particle operations and support functions |

### JavaScript Utilities (`js/`)

JavaScript tools used by the Python code.

| File | Responsibility |
|------|----------------|
| `babel_parser.js` | Parse JavaScript/JSX files using Babel to extract component information |

## Key Functions by File

This section provides a list of the main functions defined in each file of the Particle-Graph codebase.

### API Layer (`src/api/`)

#### `add_particle.py`
- `addParticle(file_path: str)` - Add particle metadata to a specific file
- `addParticleByExtension(path: str, extension: str)` - Process multiple files by extension

#### `create_graph.py`
- `createGraph(path: str)` - Create a particle graph for a given path
- `processFiles(files: List[str], prefix: str)` - Process a list of files

#### `delete_graph.py`
- `deleteGraph(path: str)` - Delete a graph by feature name or path

#### `export_graph.py`
- `exportGraph(path: str)` - Export a graph to a JSON file

#### `list_graph.py`
- `listGraph()` - List all available graphs with timestamps

#### `load_graph.py`
- `loadGraph(path: str)` - Load a graph for a specified feature
- `sanitize_graph(graph: Dict)` - Clean up a graph for presentation

#### `update_graph.py`
- `updateGraph(path: str)` - Update an existing graph

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
- `process_directory(root_dir: str, rich: bool)` - Process all files in a directory with extension filtering
- `filter_files_by_extension(files: List[str], extension: str)` - Filter a list of files by extension
- `is_ignored(path: str, ignore_patterns: List)` - Check if a path matches ignore patterns

#### `path_resolver.py`
- `ensure_dir(directory: Path)` - Ensure a directory exists
- `translate_host_path(path: str)` - Translate host machine paths to container paths
- `resolve_path(path: str, base: Path)` - Resolve a path to an absolute path
- `relative_to_project(path: Union[str, Path])` - Get a path relative to the project root
- `cache_path(filename: str)` - Get a path in the cache directory
- `export_path(filename: str)` - Get a path in the export directory
- `get_particle_path(file_path: Union[str, Path])` - Get the path for a particle file
- `get_graph_path(feature_name: str)` - Get the path for a graph file

### Graph Layer (`src/graph/`)

#### `aggregate_app_story.py`
- `aggregate_app_story(manifest: Dict)` - Aggregate app components into a story

#### `graph_support.py`
- `postProcessGraph(graph: Union[Dict[str, Any], List, Any])` - Enhance a graph with metadata and dependency information
- `linkDependencies(graph: Union[Dict[str, Any], List, Any])` - Establish connections between particles based on imports and exports
- `traceReasoning(graph: Union[Dict[str, Any], List, Any])` - Trace function call chains and data flow within the graph

#### `tech_stack.py`
- `analyze_tech_stack(files: List[str])` - Analyze tech stack from files
- `detect_frameworks(files: List[str])` - Detect frameworks used in files
- `detect_libraries(imports: List[str])` - Detect libraries from imports

### Helpers (`src/helpers/`)

#### `config_loader.py`
- `load_config(config_path: str)` - Load configuration from a file
- `get_config_value(key: str, default: Any)` - Get a configuration value

#### `data_cleaner.py`
- `filter_empty(obj: Union[Dict, List])` - Recursively remove empty values from data structures

#### `dir_scanner.py`
- `scan_directory(path: str, pattern: str)` - Scan directory contents with a pattern
- `scan_files(path: str, pattern: str)` - Scan for files matching a pattern
- `scan_dirs(path: str, pattern: str)` - Scan for directories matching a pattern

#### `gitignore_parser.py`
- `parse_gitignore(gitignore_path: str)` - Parse a gitignore file into a list of patterns
- `matches_gitignore(path: str, patterns: List[str])` - Check if a path matches any gitignore patterns

#### `project_detector.py`
- `detect_project_root(path: str)` - Detect the root directory of a project
- `is_project_root(path: str)` - Check if a directory is a project root

### Particle Layer (`src/particle/`)

#### `dependency_tracker.py`
- `track_dependencies(file_path: str)` - Track dependencies for a file
- `extract_dependencies(file_path: str)` - Extract dependencies from a file
- `analyze_imports(content: str)` - Analyze import statements
- `build_dependency_graph(files: List[str])` - Build a dependency graph

#### `file_handler.py`
- `read_file(file_path: str)` - Read a file's contents
- `write_file(file_path: str, content: str)` - Write content to a file
- `read_json(file_path: str)` - Read and parse a JSON file
- `write_json(file_path: str, data: Any)` - Write data to a JSON file

#### `particle_generator.py`
- `generate_particles(file_path: str)` - Generate particles from a file
- `parse_js_file(file_path: str)` - Parse a JavaScript file
- `extract_components(ast: Dict)` - Extract components from an AST
- `extract_functions(ast: Dict)` - Extract functions from an AST

#### `particle_support.py`
- `get_logger()` - Get a configured logger
- `init_particle_system()` - Initialize the particle system
- `get_particle_cache()` - Get the particle cache

## Data Flows

### AddParticle Data Flow

```
┌───────────────────┐     ┌────────────────────┐     ┌────────────────┐
│                   │     │                    │     │                │
│  addParticle()    │─────▶ process_directory() ────▶ file_processor  │
│  (add_particle.py)│     │                    │     │                │
└───────┬───────────┘     └────────────────────┘     └────────┬───────┘
        │                                                     │
        │                                                     ▼
┌───────▼───────────┐     ┌────────────────────┐     ┌────────────────┐
│                   │     │                    │     │                │
│  normalize_path() │◀────┤  load_gitignore()  │◀────┤ filter by ext  │
│                   │     │                    │     │                │
└───────┬───────────┘     └────────────────────┘     └────────┬───────┘
        │                                                     │
        ▼                                                     ▼
┌─────────────────────┐   ┌────────────────────┐     ┌────────────────┐
│                     │   │                    │     │                │
│  babel_parser.js    │◀──┤ particle_generator │◀────┤ process files  │
│  (Parse JS/JSX)     │   │                    │     │                │
└─────────┬───────────┘   └────────────────────┘     └────────────────┘
          │
          ▼
┌─────────────────────┐   ┌────────────────────┐
│                     │   │                    │
│  Extract particles  │──▶│  Cache Manager     │
│  (Components, etc.) │   │  (Store results)   │
└─────────────────────┘   └────────────────────┘
```

### Graph Creation, Processing and Export Flow

```
┌───────────────────┐     ┌────────────────────┐     ┌────────────────┐
│                   │     │                    │     │                │
│  createGraph()    │─────▶ process_directory() ────▶ filter files    │
│ (create_graph.py) │     │   (file_utils.py)  │     │                │
└───────┬───────────┘     └────────────────────┘     └────────┬───────┘
        │                                                     │
        │                                                     ▼
┌───────▼───────────┐     ┌────────────────────┐     ┌────────────────┐
│                   │     │                    │     │                │
│ Aggregate story   │◀────┤ Extract particles  │◀────┤ Process files  │
│                   │     │ per file           │     │                │
└───────┬───────────┘     └────────────────────┘     └────────────────┘
        │
        ▼
┌─────────────────────┐   ┌────────────────────┐     ┌────────────────┐
│                     │   │                    │     │                │
│  Cache the graph    │──▶│   loadGraph()      │────▶│ exportGraph()  │
│  (Cache Manager)    │   │  (load_graph.py)   │     │(export_graph.py)│
└─────────────────────┘   └─────────┬──────────┘     └───────┬────────┘
                                    │                        │
                                    ▼                        ▼
                          ┌────────────────────┐     ┌────────────────┐
                          │                    │     │                │
                          │  postProcessGraph()│◀────┤ Write to file  │
                          │ (graph_support.py) │     │                │
                          └─────────┬──────────┘     └────────────────┘
                                    │
                                    ▼
                          ┌────────────────────┐     ┌────────────────┐
                          │                    │     │                │
                          │  linkDependencies()│────▶│traceReasoning()│
                          │ (graph_support.py) │     │(graph_support) │
                          └────────────────────┘     └────────────────┘
```

## Graph Support Functionality

The newly added `graph_support.py` module provides enhanced functionality for graph processing:

### Post-Processing Graphs

The `postProcessGraph()` function enhances graph structures with:

- Additional metadata like file counts and node counts
- Dependency linkage between components
- Reasoning traces for function calls and data flow
- Clean-up of unnecessary information

### Dependency Linking

The `linkDependencies()` function analyzes import/export relationships:

1. First pass: collects all exports across files
2. Second pass: links imports to their corresponding exports
3. Builds a comprehensive dependency graph showing how files and components connect

### Reasoning Tracing

The `traceReasoning()` function traces call chains and data flow:

1. Collects function definitions from all files
2. Identifies function calls across the codebase
3. Establishes caller-callee relationships
4. Enables tracing code execution paths and understanding component interactions

These graph support features create a richer, more connected representation of the codebase that can be used for analysis, visualization, and AI-assisted exploration.
