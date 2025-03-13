# Cache Module Implementation Plan

This document outlines the plan for implementing a dedicated cache module for Particle-Graph.

## Proposed Structure

```
src/
  core/
    cache/
      __init__.py           # Exports the main interfaces and factory
      base.py               # Abstract base classes and interfaces
      memory_store.py       # In-memory implementation
      file_store.py         # JSON file-based implementation
      factory.py            # Factory to get the right store implementation
```

## Phase 1: Basic Implementation

### Step 1: Create Base Interface

Create `src/core/cache/base.py` with:
- An abstract `CacheStore` class
- Methods: `get(key)`, `put(key, value)`, `delete(key)`, `has(key)`, `list_keys()`

### Step 2: Memory Implementation

Create `src/core/cache/memory_store.py`:
- Implement `MemoryCacheStore` that uses a dictionary
- This will replace the current `particle_cache` in `particle_utils.py`

### Step 3: File Implementation

Create `src/core/cache/file_store.py`:
- Implement `FileCacheStore` that reads/writes to JSON files
- Include proper error handling and atomic file writes

### Step 4: Factory Implementation

Create `src/core/cache/factory.py`:
- Implement a factory function `get_cache_store(type='default')`
- Support different store types: 'memory', 'file', 'combined'

### Step 5: Integration

Update `__init__.py` to export a singleton store instance:
```python
from .factory import get_cache_store

# Default singleton cache store instance
default_store = get_cache_store('combined')
```

## Phase 2: Refactoring Existing Code

### Step 1: Update Core Files

- Modify `particle_utils.py` to use the new cache module
- Replace direct access to `particle_cache` dictionary

### Step 2: Update API Files 

- Refactor `create_graph.py`, `export_graph.py`, and `load_graph.py` to use the new cache

## Phase 3: SQLite Implementation (Future)

### Step 1: Add SQLite Store

Create `src/core/cache/sqlite_store.py`:
- Implement `SQLiteCacheStore` that stores/retrieves from SQLite
- Include schema creation, migration plan, and indexes

### Step 2: Enhanced Features

- Add caching policies (TTL, LRU)
- Implement querying capabilities
- Add transaction support

## Migration Strategy

1. Start with a hybrid approach - use both the old and new cache systems side-by-side
2. Gradually replace direct `particle_cache` access with cache store calls
3. Add tests to confirm both systems remain in sync
4. Once fully migrated, remove the original cache mechanism

This phased approach allows for continued operation while setting up a more robust architecture for future extensions, particularly for SQLite integration.
