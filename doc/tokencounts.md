Pipeline Breakdown
1. createGraph(path)
What: Builds graph, counts tokens, compresses for cache.

Steps:
Build manifest (as per last tech_stack plan—full stack, files, etc.).

Serialize: manifest_json = json.dumps(manifest).

Tokenize: token_count = len(tiktoken.get_encoding("cl100k_base").encode(manifest_json)).

Log: logger.info(f"Created graph for {path}, tokens: {token_count}").

Compress: compressed = zlib.compress(manifest_json.encode()).

Cache: cache_manager.set(feature_name, compressed).

Return: {"manifest": manifest, "token_count": token_count}.

Variation:
Simple: Use len(manifest_json.split())—no tiktoken dep, less accurate.

Lazy: Skip compression—cache raw JSON if size isn’t an issue yet.

2. loadGraph(path)
What: Loads graph, decompresses, counts tokens.

Steps:
Fetch: cached, found = cache_manager.get(feature_name).

Decompress: manifest_json = zlib.decompress(cached).decode() (if compressed), else raw JSON.

Parse: manifest = json.loads(manifest_json).

Tokenize: token_count = len(tiktoken.get_encoding("cl100k_base").encode(manifest_json)).

Log: logger.info(f"Loaded graph for {path}, tokens: {token_count}").

Multi-feature: Merge files, re-serialize, recount tokens.

Return: {"manifest": manifest, "token_count": token_count}.

Variation:
No decompress: If uncompressed cache, skip zlib—just parse.

Cached count: Store token_count in cache with manifest—skip recounting.

3. exportGraph(path)
What: Exports uncompressed JSON, reports tokens with format note.

Steps:
Load: result = loadGraph(path), get manifest and token_count.

Fallback: If tech_stack missing, recompute, re-serialize, recount tokens.

Write: json.dump(manifest, f, indent=2)—uncompressed, pretty JSON.

Log: logger.info(f"Exported graph for {path}, tokens: {token_count} - Raw JSON, no compression").

Summary: summary = f"Graph exported to {output_path}, tokens: {token_count} - Raw JSON, no compression\n...".

Return: {"content": [{"text": summary}], "token_count": token_count, "isError": False}.

Variation:
Minified option: Add json.dump(manifest, f, separators=(',', ':'))—report minified tokens too.

Compress flag: Offer compressed export later—toggle with arg.

4. data_cleaner.py (No Change Needed)
Already has filter_empty(preserve_tech_stack=True)—works with this plan.

5. tech_stack.py (No Change Needed)
get_tech_stack() stays as-is—token count happens post-manifest.

Full Sketch
python

import json
import zlib
import tiktoken  # pip install tiktoken

# Tokenizer setup
tokenizer = tiktoken.get_encoding("cl100k_base")

def createGraph(path):
    manifest = {...}  # Full tech_stack plan
    manifest_json = json.dumps(manifest)
    token_count = len(tokenizer.encode(manifest_json))
    logger.info(f"Created graph for {path}, tokens: {token_count}")
    compressed = zlib.compress(manifest_json.encode())
    feature_name = "codebase" if path in ("all", "codebase") else "_".join(path.split(","))
    cache_manager.set(feature_name, compressed)
    return {"manifest": manifest, "token_count": token_count}

def loadGraph(path):
    if path in ("all", "codebase"):
        cached, found = cache_manager.get("__codebase__")
    else:
        features = path.split(",")
        feature_name = "_".join(f.lower() for f in features)
        cached, found = cache_manager.get(feature_name)
    if not found:
        return {"error": "Graph not found"}
    manifest_json = zlib.decompress(cached).decode()
    manifest = json.loads(manifest_json)
    token_count = len(tokenizer.encode(manifest_json))
    logger.info(f"Loaded graph for {path}, tokens: {token_count}")
    return {"manifest": manifest, "token_count": token_count}

def exportGraph(path):
    result = loadGraph(path)
    if "error" in result:
        return {"error": result["error"]}
    manifest = result["manifest"]
    token_count = result["token_count"]
    manifest_json = json.dumps(manifest, indent=2)  # Uncompressed
    output_path = PathResolver.export_path(f"{feature_name}_graph_{timestamp}.json")
    with open(output_path, "w") as f:
        f.write(manifest_json)
    summary = f"Graph exported to {output_path}, tokens: {token_count} - Raw JSON, no compression"
    logger.info(summary)
    return {"content": [{"text": summary}], "token_count": token_count, "isError": False}

Variations
Tokenizer:
Default: tiktoken—accurate, free, small dep.

Simple: len(json.dumps(manifest).split())—no dep, rough estimate.

Compression:
Default: zlib for createGraph()/loadGraph()—scale-ready.

Lazy: Skip compression—faster dev, bigger cache.

Export:
Default: Uncompressed—readable, user/AI-friendly.

Future: Add --compress arg—offer both, report tokens for each.

Why This Rocks
Token Counting: tiktoken gives legit AI token counts—users see real cost (e.g., “10,242 tokens”). Free, easy win.

Compression: zlib shrinks cache—market-ready without sweat. Uncompressed exportGraph() keeps it practical.

Effort: ~20 lines total—tiktoken setup, count calls, zlib wrap. Big reward—user trust + scale.

Export Fit: “Raw JSON, no compression” label sets expectations—future-proofs external API use.

Notes
Cost: tiktoken is free—pip install, no runtime hit. zlib is zero-cost (built-in).

Compression Now: Do it—graphs might grow fast, and it’s trivial to add.

Export Later: Uncompressed is fine—add compression when API needs hit.

Claude Prompt (When Ready)

You’re a Python dev adding token counting and compression to a graph system. Each function (`createGraph`, `loadGraph`, `exportGraph`) reports AI-relevant token counts using `tiktoken`. `createGraph` and `loadGraph` compress graphs for cache; `exportGraph` stays uncompressed with a clear label. Update the files below.

**Plan**:
1. **Setup**: Add `import tiktoken`, `tokenizer = tiktoken.get_encoding("cl100k_base")` globally.
2. **`createGraph(path)`**:
   - Build `manifest` (per last tech_stack plan).
   - `manifest_json = json.dumps(manifest)`.
   - `token_count = len(tokenizer.encode(manifest_json))`.
   - Log: `logger.info(f"Created graph for {path}, tokens: {token_count}")`.
   - Compress: `zlib.compress(manifest_json.encode())` → cache.
   - Return: `{"manifest": manifest, "token_count": token_count}`.
3. **`loadGraph(path)`**:
   - Fetch cache, decompress: `json.loads(zlib.decompress(cached).decode())`.
   - `token_count = len(tokenizer.encode(json.dumps(manifest)))`.
   - Log: `logger.info(f"Loaded graph for {path}, tokens: {token_count}")`.
   - Return: `{"manifest": manifest, "token_count": token_count}`.
4. **`exportGraph(path)`**:
   - Load via `loadGraph()`, get `manifest` and `token_count`.
   - Write uncompressed: `json.dump(manifest, f, indent=2)`.
   - Summary: `f"Graph exported to {output_path}, tokens: {token_count} - Raw JSON, no compression"`.
   - Return: `{"content": [{"text": summary}], "token_count": token_count, ...}`.

**Current Files**: [Insert your latest `create_graph.py`, `load_graph.py`, `export_graph.py`, `data_cleaner.py`, `tech_stack.py`]

**Output**: Updated files with explanations.

