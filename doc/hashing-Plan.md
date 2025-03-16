mplementation Plan: Linking addParticle() to createGraph() for Seamless Operation
Goal
Ensure createGraph(path) automatically generates and caches particles for JS/JSX files in a directory (e.g., components/features/Events) if they’re missing or stale, using file hashes for freshness. Build and export graphs seamlessly, keeping Particle-Graph as an in-house, file-based powerhouse for GetReal’s AI context.
Assumptions
Current setup: addParticle(file_path), createGraph(path), and exportGraph(path) work individually (particles cached as JSON, graphs built/exported).

Files are in /project/thy/today/ (Docker) or /Users/Thy/... (local), handled by PathResolver.

You want to stick with file-based caching (no SQLite/HTTP), agnostic design (JS/JSX now, extensible later), and a 3–4 month polish timeline.

Steps
Update Dependencies & Imports
Ensure create_graph.py imports necessary modules:
from src.particle.file_handler import read_particle, write_particle, read_file

from src.particle.particle_generator import generate_particle

from src.core.path_resolver import PathResolver

from src.helpers.dir_scanner import scan_directory

from src.particle.particle_support import logger

import hashlib (for file hashing).

Verify addParticle() in add_particle.py and particle generation in particle_generator.py are functional.

Design Hash-Based Freshness
Create a function to compute a file’s hash (e.g., MD5 of content) for freshness checks.

Store the hash in particle metadata or alongside the cached JSON file.

Compare file hash to cached hash (or file mtime) to determine if a particle is stale.

Modify create_graph.py
Update createGraph(path) to:
a. Use scan_directory() to list JS/JSX files in path (e.g., *.{js,jsx}).
b. For each file:
Resolve the full path with PathResolver.resolve_path().

Compute the file’s current hash.

Get the particle cache path with PathResolver.get_particle_path().

Check if a cached particle exists (file exists).

If cached, read it with read_particle() and check freshness:
Compare hash/mtime in particle metadata or file mtime to current hash.

If stale or no hash/mtime, regenerate the particle.

If no cache or stale, read file content with read_file(), generate particle with generate_particle(), and cache it with write_particle().

Add particle to graph nodes.
c. Build edges from depends_on and calls in particles (e.g., connect EventCard.jsx to react imports).
d. Post-process graph with graph_support.py (link dependencies, add tech stack, flows).
e. Cache the graph (e.g., /project/particle-graph/cache/graphs/components_features_Events.graph.json).
f. Return JSON-RPC response with graph data.

Update Particle Metadata for Hashes
Modify particle_generator.py’s generate_particle() to include a hash field in the particle dict (e.g., {"id": "EventCard.jsx", "hash": "md5_hash", ...}).

Update write_particle() in file_handler.py to store this hash in the cached JSON.

Test the Flow
Run createGraph("components/features/Events"):
Expect it to scan files (e.g., EventCard.jsx), generate/cache particles if missing/stale, build a graph, and cache it.

Run exportGraph("components/features/Events"):
Expect it to fetch the cached graph, export JSON, and feed it to your AI.

Verify:
No errors (particles generated, cached, graphed).

Graph includes 95% of GetReal’s narrative (nodes, edges, tech stack).

Performance is fast for GetReal’s codebase.

Keep It Agnostic & In-House
Use PathResolver for Docker/local paths.

Focus on JS/JSX files now, but design generate_particle() and createGraph() to handle other languages (e.g., Python) later with parser switches.

Stick with files—no SQLite/HTTP (overkill for now).

Document & Validate
Add comments in create_graph.py explaining the hash-based caching and particle generation flow.

Test on GetReal’s components/features/Events—does it map hooks, calls, dependencies correctly? Is the graph AI-ready?

