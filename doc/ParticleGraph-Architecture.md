# Particle-Graph Architecture Document

## Project Overview

Particle-Graph is a system designed to analyze and generate graph representations of code components, particularly focusing on JavaScript/JSX codebases. The system extracts metadata ("particles") from source files, builds relationship graphs between components, and provides APIs for creating, updating, loading, and exporting these graphs that can be used for code analysis, onboarding and AI assistance.

## Directory Structure

```
/Users/Thy/Particle-Graph/
├── src/                         # Main source code directory
│   ├── api/                     # API endpoints for end-user operations
│   │   ├── add_particle.py      # Add particles to individual files
│   │   ├── aggregate_app_story.py # Aggregate related app components
│   │   ├── create_graph.py      # Create new particle graphs
│   │   ├── delete_graph.py      # Delete existing graphs
│   │   ├── export_graph.py      # Export graphs to JSON files
│   │   ├── list_graph.py        # List available graphs in cache
│   │   ├── load_graph.py        # Load graphs from cache or files
│   │   └── update_graph.py      # Update existing graphs
│   │
│   ├── core/                    # Core functionality and utilities
│   │   ├── cache_manager.py     # Centralized cache management system
│   │   ├── dependency_tracker.py # Track dependencies between components
│   │   ├── file_handler.py      # Handle file operations
│   │   ├── file_utils.py        # File-related utility functions
│   │   ├── particle_generator.py # Generate particle metadata from code
│   │   ├── particle_utils.py    # Utilities related to particles
│   │   ├── path_resolver.py     # Path resolution and management
│   │   └── utils.py             # General utility functions
│   │
│   ├── analysis/                # Code analysis modules
│   │   └── tech_stack.py        # Identify technology stack from code
│   │
│   └── utils/                   # Supporting utilities
│       ├── check_root.py        # Verify project root
│       ├── config_loader.py     # Load configuration
│       └── list_dir.py          # Directory listing utilities
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
| `aggregate_app_story.py` | Build relationships between related app components and features |
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
| `dependency_tracker.py` | Track and analyze dependencies between components |
| `file_handler.py` | Handle file operations like reading and writing files |
| `file_utils.py` | Utility functions for file operations like directory processing |
| `particle_generator.py` | Generate particle metadata by parsing source code |
| `particle_utils.py` | Utilities for particle operations and global particle cache |
| `path_resolver.py` | Handle path resolution, normalization, and directory management |
| `utils.py` | General utility functions used across the codebase |

### Analysis Layer (`src/analysis/`)

The analysis layer provides specialized code analysis capabilities.

| File | Responsibility |
|------|----------------|
| `tech_stack.py` | Analyze code to identify technologies and libraries used |

### Utilities (`src/utils/`)

Supporting utilities for the overall system.

| File | Responsibility |
|------|----------------|
| `check_root.py` | Verify and validate project root directories |
| `config_loader.py` | Load and parse configuration settings |
| `list_dir.py` | List directory contents with patterns and filters |

### JavaScript Utilities (`js/`)

JavaScript tools used by the Python code.

| File | Responsibility |
|------|----------------|
| `babel_parser.js` | Parse JavaScript/JSX files using Babel to extract component information |

## Key Architectural Patterns

### 1. Caching System

The caching system is implemented through the `CacheManager` class in `cache_manager.py` and provides:

- Thread-safe operations with reentrant locks
- Both in-memory caching and persistent disk storage
- Cache metadata tracking (access counts, timestamps)
- Automatic persistence with configurable intervals
- Cache invalidation for older entries

### 2. Path Resolution

Path handling is centralized in the `PathResolver` class which provides:

- Consistent path resolution across different environments (Docker, local)
- Path normalization and standardization
- Directory creation and management
- Specialized path formatting for different file types

### 3. Particle Generation

The particle generation process:

1. Parses JavaScript/JSX files using Babel parser
2. Extracts component metadata (props, hooks, dependencies, etc.)
3. Generates standardized particle JSON data
4. Stores particles in both memory cache and on disk

### 4. Graph Building

Graph building combines particles into relationship graphs by:

1. Collecting particles from source files
2. Analyzing dependencies between components
3. Building a hierarchical representation
4. Adding metadata like timestamps and coverage statistics

## Data Flow

1. **Particle Creation**:  
   Source Files → Babel Parser → Particle Generator → Cache

2. **Graph Building**:  
   Particles → Dependency Tracker → Graph Creation → Cache

3. **Graph Operations**:  
   User Request → API Layer → Core Operations → Cache/File Operations → Response

## Key Functions by File

This section provides a list of the main functions defined in each file of the Particle-Graph codebase.

### API Layer (`src/api/`)

#### `add_particle.py`
- `addParticle(file_path: str)` - Add particle metadata to a specific file
- `addParticleByExtension(path: str, extension: str)` - Process multiple files by extension

#### `aggregate_app_story.py`
- `aggregate_app_story(manifest: Dict)` - Aggregate app components into a story

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

#### `dependency_tracker.py`
- `extract_dependencies(file_path: str)` - Extract dependencies from a file
- `analyze_imports(content: str)` - Analyze import statements
- `build_dependency_graph(files: List[str])` - Build a dependency graph

#### `file_handler.py`
- `read_file(file_path: str)` - Read content from a file
- `write_particle(file_path: str, context: Dict)` - Write particle data to a file
- `is_binary_file(file_path: str)` - Check if a file is binary

#### `file_utils.py`
- `process_directory(root_dir: str, rich: bool)` - Process all JS/JSX files in a directory

#### `particle_generator.py`
- `generate_particle(file_path: str, rich: bool)` - Generate particle data from a file
- `extract_metadata(ast: Dict)` - Extract metadata from an AST
- `parse_jsx(content: str)` - Parse JSX content to AST

#### `particle_utils.py`
- `logger` - Configured logging instance
- `particle_cache` - Global particle cache dictionary
- `normalize_path(path: str)` - Normalize file paths
- `is_feature_path(path: str)` - Check if a path is a feature path

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

### Analysis Layer (`src/analysis/`)

#### `tech_stack.py`
- `analyze_tech_stack(files: List[str])` - Analyze tech stack from files
- `detect_frameworks(files: List[str])` - Detect frameworks used in files
- `detect_libraries(imports: List[str])` - Detect libraries from imports

### Utilities (`src/utils/`)

#### `check_root.py`
- `is_project_root(path: str)` - Check if a path is a project root
- `find_project_root(start_path: str)` - Find the project root from a path

#### `config_loader.py`
- `load_config(config_path: str)` - Load configuration from a file
- `get_config_value(key: str, default: Any)` - Get a configuration value

#### `list_dir.py`
- `list_directory(path: str, pattern: str)` - List directory contents with a pattern
- `filter_files(files: List[str], extensions: List[str])` - Filter files by extension

## Recent Architectural Improvements

The codebase has undergone several refactoring efforts to improve organization:

1. **Decoupled Components**:
   - Moved `aggregate_app_story` to a dedicated file
   - Relocated utility functions to appropriate utility modules
   - Separated file operations from business logic

2. **Centralized Cache Management**:
   - Created dedicated `CacheManager` to replace direct dictionary access
   - Implemented thread safety and persistence guarantees
   - Added cache statistics and monitoring

3. **Improved Path Handling**:
   - Created `PathResolver` for consistent path operations
   - Added environment detection (Docker vs. local)
   - Standardized path formatting and resolution

4. **Single Responsibility Principle**:
   - Each module now has a clearer, more focused responsibility
   - Reduced code duplication across the codebase
   - Improved maintainability and testability

## Future Architectural Directions

Based on the implementation plan, future improvements may include:

1. **SQLite Integration**:
   - Implement a SQLite-backed cache for improved query capabilities
   - Add schema creation and migration support

2. **Enhanced Caching Features**:
   - More sophisticated caching policies (LRU, TTL)
   - Cache compression for large graph structures
   - Partial graph loading capabilities

3. **Cache Analytics**:
   - Performance monitoring for cache operations
   - Cache hit/miss statistics
   - Visualization dashboard for cache performance
