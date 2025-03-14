# Particle-Graph Architecture Document

## Project Overview

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
│   │   ├── path_resolver.py     # Path resolution and management
│   │   └── utils.py             # General utility functions
│   │
│   ├── graph/                   # Graph generation and analysis
│   │   ├── aggregate_app_story.py # Aggregate related app components
│   │   └── tech_stack.py        # Identify technology stack from code
│   │
│   ├── helpers/                 # Helper utilities
│   │   ├── config_loader.py     # Load configuration
│   │   ├── dir_scanner.py       # Directory scanning utilities
│   │   ├── gitignore_parser.py  # Parse gitignore files
│   │   └── project_detector.py  # Detect project roots
│   │
│   └── particle/                # Particle generation and handling
│       ├── dependency_tracker.py # Track dependencies between components
│       ├── file_handler.py      # Handle file operations
│       ├── particle_generator.py # Generate particle metadata from code
│       └── particle_support.py  # Support functions for particles
│
├── js/                          # JavaScript utilities
│   └── babel_parser.js          # Parse JS/JSX files with Babel
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
| `path_resolver.py` | Handle path resolution, normalization, and directory management |
| `utils.py` | General utility functions used across the codebase, including path normalization, gitignore loading, and data filtering |

### Graph Layer (`src/graph/`)

The graph layer handles building and analyzing relationships between components.

| File | Responsibility |
|------|----------------|
| `aggregate_app_story.py` | Aggregate related app components into a coherent story structure |
| `tech_stack.py` | Analyze code to identify technologies and libraries used |

### Helpers (`src/helpers/`)

Supporting utilities for the overall system.

| File | Responsibility |
|------|----------------|
| `config_loader.py` | Load and parse configuration settings |
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
- `resolve_path(path: str, base: Path)` - Resolve a path to an absolute path
- `relative_to_project(path: Union[str, Path])` - Get a path relative to the project root
- `cache_path(filename: str)` - Get a path in the cache directory
- `export_path(filename: str)` - Get a path in the export directory
- `get_particle_path(file_path: Union[str, Path])` - Get the path for a particle file
- `get_graph_path(feature_name: str)` - Get the path for a graph file

#### `utils.py`
- `filter_empty(data: Union[Dict, List])` - Remove empty values from data structures
- `load_gitignore(path: str)` - Load gitignore patterns
- `normalize_path(path: str)` - Normalize file paths

### Graph Layer (`src/graph/`)

#### `aggregate_app_story.py`
- `aggregate_app_story(manifest: Dict)` - Aggregate app components into a story

#### `tech_stack.py`
- `analyze_tech_stack(files: List[str])` - Analyze tech stack from files
- `detect_frameworks(files: List[str])` - Detect frameworks used in files
- `detect_libraries(imports: List[str])` - Detect libraries from imports

### Helpers (`src/helpers/`)

#### `config_loader.py`
- `load_config(config_path: str)` - Load configuration from a file
- `get_config_value(key: str, default: Any)` - Get a configuration value

#### `dir_scanner.py`
- `scan_directory(path: str, pattern: str)` - Scan directory contents with a pattern
- `filter_by_extension(files: List[str], extensions: List[str])` - Filter files by extension

#### `gitignore_parser.py`
- `parse_gitignore(gitignore_file: str)` - Parse a gitignore file into pattern matchers
- `matches_pattern(path: str, pattern: str)` - Check if a path matches a gitignore pattern

#### `project_detector.py`
- `is_project_root(path: str)` - Check if a path is a project root
- `find_project_root(start_path: str)` - Find the project root from a path

### Particle Layer (`src/particle/`)

#### `dependency_tracker.py`
- `extract_dependencies(file_path: str)` - Extract dependencies from a file
- `analyze_imports(content: str)` - Analyze import statements
- `build_dependency_graph(files: List[str])` - Build a dependency graph

#### `file_handler.py`
- `read_file(file_path: str)` - Read content from a file
- `write_particle(file_path: str, context: Dict)` - Write particle data to a file
- `is_binary_file(file_path: str)` - Check if a file is binary

#### `particle_generator.py`
- `generate_particle(file_path: str, rich: bool)` - Generate particle data from a file
- `extract_metadata(ast: Dict)` - Extract metadata from an AST
- `parse_jsx(content: str)` - Parse JSX content to AST

#### `particle_support.py`
- `normalize_particle_path(path: str)` - Normalize paths for particles
- `get_particle_cache()` - Get the global particle cache
- `load_particle(file_path: str)` - Load a particle from disk

## Recent Architectural Improvements

The codebase has undergone several refactoring efforts to improve organization:

1. **Decoupled Components**:
   - Moved `aggregate_app_story` from `src/api/create_graph.py` to a dedicated file in `src/graph/`
   - Relocated utility functions to appropriate modules:
     - `filter_empty` moved to `src/core/utils.py`
     - `load_gitignore` and `normalize_path` moved to `src/core/utils.py`
     - `process_directory` moved to `src/core/file_processor.py`
   - Reorganized functionality into focused directories (graph, helpers, particle)

2. **Centralized Utility Functions**:
   - Common utilities now available in `src/core/utils.py`
   - File processing logic centralized in `src/core/file_processor.py`
   - Specialized helpers in the new `src/helpers/` directory

3. **Improved Path Handling**:
   - Enhanced path normalization and standardization
   - Gitignore pattern handling improved through dedicated parser

4. **Single Responsibility Principle**:
   - Each module now has a clearer, more focused responsibility
   - Reduced code duplication across the codebase
   - Improved maintainability and testability

