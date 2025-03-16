Goal
Refactor Particle-Graph to use only createGraph(path) and exportGraph(path) as the core APIs, ensuring seamless particle generation, caching, graphing, and exporting for GetReal’s in-house context needs. Keep it file-based (no SQLite/HTTP), agnostic (JS/JSX now, extensible later), and within your 3–4 month timeline.
Assumptions
Current setup: createGraph() crawls directories, generates/caches particles (via hashes), builds graphs; exportGraph() exports cached graphs as JSON.

Particles cached as JSON files (e.g., /project/particle-graph/cache/...EventCard_jsx.particle.json); graphs cached as JSON (e.g., components_Features_Events.graph.json).

PathResolver, dir_scanner.py, file_handler.py, particle_generator.py, and graph_support.py are functional.

You want to skip listGraph(), updateGraph(), and other APIs for now.

Steps
Review Current Code
Open create_graph.py and export_graph.py—confirm createGraph(path) generates particles, caches graphs, and builds nodes/edges; exportGraph(path) fetches and exports cached graphs.

Ensure add_particle.py, delete_graph.py, list_graph.py, load_graph.py, and update_graph.py are no longer needed (remove or archive for reference).

Verify file_handler.py (read/write particles), particle_generator.py (generate particles), and graph_support.py (post-process graphs) work.

Refine create_graph.py
Update createGraph(path) to:
a. Use scan_directory(path, "*.{js,jsx}") to list JS/JSX files in the directory.
b. For each file:
Resolve full path with PathResolver.resolve_path().

Compute file hash (e.g., MD5 of content) using hashlib.md5() or file mtime.

Get particle cache path with PathResolver.get_particle_path().

Check if cached particle exists (file exists).

If cached, read with read_particle() and check freshness:
Compare hash/mtime in particle metadata (or file mtime) to current hash.

If stale or no hash/mtime, regenerate particle.

If no cache or stale, read file with read_file(), generate particle with generate_particle(), and cache with write_particle() (include hash in metadata).

Add particle to graph nodes.
c. Build edges from depends_on and calls in particles (e.g., connect EventCard.jsx to react imports).
d. Post-process graph with postProcessGraph() from graph_support.py (link dependencies, add tech stack, flows).
e. Cache graph as JSON (e.g., /project/particle-graph/cache/graphs/<normalized_path>.graph.json, where normalized_path is path.strip("/").replace("/", "_")).
f. Return JSON-RPC response: {"content": [{"type": "text", "text": "Graph created..."}], "status": "OK", "isError": False, "graph": graph}.

Ensure it handles Docker/local paths via PathResolver and skips gitignored files via dir_scanner.py.

Refine export_graph.py
Update exportGraph(path) to:
a. Accept a single path (e.g., "components/Features/Events") or handle special cases (e.g., "All"—see below).
b. Normalize path (e.g., path.strip("/").replace("/", "_")).
c. Check for cached graph at /project/particle-graph/cache/graphs/<normalized_path>.graph.json.
d. If graph exists, load with PathResolver.read_json_file(); if not, call createGraph(path) to generate it.
e. Export graph as JSON to /project/particle-graph/exports/<normalized_path>.graph.json.
f. Return JSON-RPC response: {"content": [{"type": "text", "text": "Graph exported..."}], "status": "OK", "isError": False, "note": f"Graph exported to {export_path}"}.

Add support for exportGraph("All"):
Use dir_scanner.py or PathResolver to list all .graph.json files in /project/particle-graph/cache/graphs/.

Load each graph, merge nodes/edges (deduplicate by id), update metadata (total files, tech stack).

Export as /project/particle-graph/exports/all.graph.json.

Optionally, add support for multiple paths (e.g., exportGraph("Events", "Navigation")):
Accept a list or comma-separated string, call createGraph() for each, merge particles/graphs, and export as one file (e.g., components_Features_Events_Core_Navigation.graph.json).

Remove Unused APIs
Archive or delete add_particle.py, delete_graph.py, list_graph.py, load_graph.py, and update_graph.py—no longer needed with createGraph()/exportGraph() handling everything.

Update any imports or references in other files (e.g., src/api/__init__.py) to point only to create_graph.py and export_graph.py.

Test the Flow
Run createGraph("components/Features/Events"):
Expect it to scan files, generate/cache particles (if missing/stale), build graph, and cache it.

Run exportGraph("components/Features/Events"):
Expect it to fetch/load the cached graph and export JSON.

Run exportGraph("All"):
Expect it to aggregate all cached graphs, export one file.

Run exportGraph("Events", "Navigation") (if implemented):
Expect it to merge particles/graphs from both, export one file.

Verify:
No errors, fast performance for GetReal’s codebase.

Graphs include 95% narrative (nodes, edges, tech stack).

JSON is AI-ready, no token cutoff issues.

Keep It Lean & In-House
Stick with file-based caching—no SQLite/HTTP (overkill for GetReal now).

Ensure PathResolver handles Docker/local paths.

Keep it agnostic (JS/JSX now, extensible to other languages later with parser switches).

Document & Validate
Add comments in create_graph.py and export_graph.py explaining the flow (crawling, caching, graphing, exporting).

Test on GetReal’s components/Features/Events and components/Core/Navigation—does it aggregate correctly? Are exports clean and fast?

