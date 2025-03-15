You’re a Python dev tasked with updating a graph generation system. The goal: every graph (feature, multi-feature, "all") includes a full `tech_stack` reflecting the entire codebase’s architecture, recomputed fresh on every `createGraph()` call, cached globally, and reused everywhere. No per-feature filtering—just one `tech_stack` overwritten each time. Below are the current files—update them per the plan.

---

**Plan**:
1. **`create_graph.py`**:
   - Input: `path` ("Events", "Events,Navigation", "all").
   - Scan `path` (split commas for multi-features) → build `processed_files`.
   - Compute full `tech_stack` with `get_tech_stack(processed_files)` → cache as `"tech_stack"`.
   - Build manifest: `"tech_stack": full_tech_stack`, `"files"`, `"file_count"`, etc.
   - Multi-features: Add `"aggregate": True`, `"features": [list]`.
   - Cache manifest: `"__codebase__" for "all"`, else `"_".join(features)`.
   - Use `filter_empty(manifest, preserve_tech_stack=True)`.
2. **`load_graph.py`**:
   - `"all"/"codebase"`: Fetch `__codebase__` from cache.
   - Single feature: Fetch `feature_name` from cache.
   - Multi-features (e.g., "Events,Navigation"): Merge `files` from each feature’s cache, use `"tech_stack"` for `tech_stack`.
   - Return manifest with `"aggregate": True` for multi-features.
3. **`export_graph.py`**:
   - Load manifest via `loadGraph(path)`.
   - Fallback: If `"tech_stack"` missing, fetch `"tech_stack"`; if not found, recompute and cache it.
   - Add `"exported_at"` for `"all"`.
   - Use `filter_empty(manifest, preserve_tech_stack=True)`.
   - Write JSON, keep summary with `tech_stack` list.
4. **`data_cleaner.py`**:
   - Ensure `filter_empty(obj, preserve_tech_stack=False)` keeps `"tech_stack"` if `preserve_tech_stack=True`.
5. **`tech_stack.py`**: No changes—assume it works.

**Current Files**:
[Insert your latest `create_graph.py`, `load_graph.py`, `export_graph.py`, `tech_stack.py`, `data_cleaner.py`]

**Output**:
- Updated `create_graph.py`, `load_graph.py`, `export_graph.py`, `data_cleaner.py`.
- Brief explanation of changes.