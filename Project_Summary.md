# Particle-Graph Project Summary

## Intent
Particle-Graph is a tool to analyze and document React Native/Expo codebases by generating `SubParticle` objects—metadata summaries of components. It aims to:
- Extract props, hooks, API calls, key logic, and dependencies from individual files.
- Export this metadata as `export const SubParticle = {...}` directly into source files.
- Aggregate graphs for directories/features to map tech stacks, relationships, and business logic.
- Serve as a single source of truth—reflecting code, logic, and tech—for maintenance, debugging, onboarding, and AI context.

## Core Functionality
- **`addSubParticle(file_path, rich=True)`**: Analyzes a file, generates a `SubParticle`, writes it back.
- **`addAllSubParticle(root_dir="/project")`**: Populates `SubParticle`s across a codebase (e.g., 154 files).
- **`listGraph(features)`**: Lists available graphs (e.g., `Events,Navigation,Role`).
- **`loadGraph(features)`**: Loads a graph for specified features (e.g., `Events,Navigation,Role`).
- **`exportGraph(features)`**: Aggregates a graph for specified features (e.g., `Events,Navigation,Role`).
- **Output Format**: JSON-like object with `purpose`, `props`, `hooks`, `calls`, `key_logic`, `depends_on`.
- **Tools**: Dockerized MCP server, callable via CLI or IDE integration.

## Files
- **`addSubParticle.py`**: Orchestrates analysis, calls parsers, and exports via `file_handler`.
- **`file_handler.py`**: Reads/writes files, maps paths (`/project` root in Docker), ensures valid JSON.
- **`prop_parser.py`**: Extracts props (regex now; Tree-sitter in progress).
- **`hook_analyzer.py`**: Identifies hooks, infers purpose (e.g., `useRouter` → navigation).
- **`call_detector.py`**: Detects API calls (e.g., `supabase.from()`, `fetch`).
- **`logic_inferer.py`**: Infers `key_logic` (conditions, state, animations; some file-specific rules).
- **`dependency_tracker.py`**: Maps imports and runtime deps (e.g., hooks to files).
- **`context_builder.py`**: Builds `SubParticle` with `purpose` from file name/content.
- **`exportGraph.py`**: Aggregates graphs from populated `SubParticle`s.
- **`particle_utils.py`**: Logger, `app_path` (`/project`), caching (assumed).
- **`server.py`**: FastMCP server—registers tools (`addSubParticle`, `addAllSubParticle`, `exportGraph`).
- **`populate_and_graph.py`** (proposed): One-shot full-codebase graph script.
- **Docker**: `Dockerfile` builds `particle-graph`, mounts `/Users/Thy/Today:/project`.

## Constraints
- **Path Handling**: Supports absolute (IDE) and relative (CLI) paths, mapped to `/project`.
- **Prop Detection**: Must handle stateless components, hook-derived props, complex JSX (e.g., `NavigationBar.jsx`).
- **Scalability**: Works for single files and full codebase (154 files tested).
- **Accuracy**: Balances generic parsing (Tree-sitter) with optional specialization (prefs file TBD).
- **IDE Integration**: AI/IDE picks active file—path resolution must align (e.g., VS Code workspace).

## Current State (March 09, 2025)
- **Working**: 
  - `addSubParticle` generates/writes `SubParticle` for files (e.g., `NavigationBar.jsx`, `EventStatus.jsx`).
  - `addAllSubParticle` populates 154 files; `exportGraph` aggregates features (51 files in `Events,Navigation,Role`).
- **Accuracy**: 90%+ for GetReal with dedicated tweaks; ~60-70% agnostic.
- **Props**: Regex catches most (e.g., `onPress: function`); Tree-sitter WIP for edge cases.
- **Key Logic**: Mix of generic (e.g., `"Tracks current position"`) and specific (e.g., `"Renders tabs by role"`).
- **Next**: 
  - Polish `key_logic` (fix enums, capacity vs. position).
  - Full graph of 154 files via `populate_and_graph.py`.
  - Optional hybrid approach—agnostic core + prefs file.
- **To Fix**:
  - Enum parsing (`tabs` in `NavigationBar.jsx`).
  - Feature detection for all 154 files in `exportGraph`.

## Setup
- **Docker**: 
  ```bash
  docker build -t particle-graph .
  docker run -m 2g -v /Users/Thy/Today:/project -i particle-graph

____________________
( march 09, 2025)

Comprehensive Plan: Babel in Docker with Subprocess Sync
Objective
Goal: Parse GetReal JS/JSX files with Babel for max accuracy (SubParticles with props, hooks, logic), sync to Python Particle-Graph MCP via subprocess, build a rich full_codebase_graph.json.

Focus: Relevancy (95%+ depth)—time/scale secondary.

Setup: Two Docker containers—Python MCP (Particle-Graph) + Node.js Babel parser—via Docker Compose.

Project Structure
Particle-Graph (/Users/Thy/Today):
Python MCP server—runs server.py, addSubParticle.py, etc.

Dockerized, mounts GetReal as /project.

GetReal (/Users/Thy/Today or subdir):
JS/React Native codebase—154 files now, growing slow (chat, ticketing, i18n later).

No Node/Babel deps—stays clean.

Sync: Python → Babel Docker (file path) → JSON → writes SubParticle to GetReal files.

Step-by-Step Implementation
1. Prep Your Environment
Dir: Work in /Users/Thy/Today—assumes Particle-Graph lives here, GetReal mounts in.

Tools:
Docker + Docker Compose installed (docker --version, docker-compose --version).

Python 3.9+ (for MCP).

Node.js (local dev, optional—Docker handles it).

2. Babel Parser Container
File: babel_parser.js—parses JS/JSX, outputs SubParticle JSON.
Location: /Users/Thy/Today/babel_parser.js.

Content: 
Reads file path from process.argv[2].

Uses @babel/parser (JSX, modern JS).

Extracts props, hooks, calls, logic, deps.

Merges with existing SubParticle if present.

Outputs JSON.

Key Features:
Props from destructuring ({ title, sections }).

Hooks (useState, etc.).

Logic (if, loops, React Native imports).

Accurate—95%+ depth.

Dockerfile: Dockerfile.babel—builds Babel Node image.
Location: /Users/Thy/Today/Dockerfile.babel.

Content:
Base: node:16-slim.

Copy babel_parser.js.

Install @babel/parser.

CMD: node babel_parser.js.

Build:
bash

docker build -f Dockerfile.babel -t babel-parser .

3. Particle-Graph MCP Container
File: addSubParticle.py—calls Babel, writes SubParticle.
Location: /Users/Thy/Today/addSubParticle.py.

Content:
Reads file via file_handler.

Runs docker run -v /Users/Thy/Today:/app babel-parser /app/path/to/file.

Parses JSON output.

Writes export const SubParticle = {...} to file.

Key Features:
Subprocess sync—file path handoff.

Error handling—logs fails, skips gracefully.

Dockerfile: Dockerfile—updates existing MCP image.
Location: /Users/Thy/Today/Dockerfile.

Content:
Base: python:3.9.

Copy all MCP files.

Install requirements.txt.

CMD: python server.py.

4. Docker Compose Setup
File: docker-compose.yml—ties it together.
Location: /Users/Thy/Today/docker-compose.yml.

Content:
Service: particle-graph—Python MCP.
Build: . (uses Dockerfile).

Volume: /Users/Thy/Today:/project.

Service: babel-parser—Babel Node.
Build: . (uses Dockerfile.babel).

Volume: /Users/Thy/Today:/app (syncs with MCP).

Run:
bash

docker-compose up --build

5. Execution Flow
Test Single File:
bash

docker-compose run particle-graph python -c "from addSubParticle import addSubParticle; addSubParticle('/project/components/Features/Hub/components/shared/HubContent.jsx')"

Expect: HubContent.jsx gets:
javascript

export const SubParticle = {
  "purpose": "Handles hubcontent functionality",
  "props": ["title", "sections"],
  "hooks": [],
  "calls": [],
  "key_logic": ["Branches on conditions", "Responds to scroll events"],
  "depends_on": ["react", "react-native"]
};

Full Graph:
bash

docker-compose run particle-graph python -c "from addSubParticle import addAllSubParticle; from exportGraph import exportGraph; addAllSubParticle('/project'); exportGraph(['app', 'components', 'lib'])"

Expect: 154 files parsed, full_codebase_graph.json in /project/particle-graph.

6. Validation
Logs: Check particle_utils.logger—“Added SubParticle to /path” or errors.

Graph: Open full_codebase_graph.json—props, hooks, logic should reflect GetReal’s intent.

Accuracy: Spot-check NavigationBar.jsx—tabs, currentTab props, role-based logic.

Key Details
Volume Sync: 
MCP: /Users/Thy/Today:/project.

Babel: /Users/Thy/Today:/app.

Ensures Babel reads raw GetReal files—100% parse accuracy.

Dependencies:
MCP: requirements.txt—no change (maybe docker if Python lib used).

Babel: @babel/parser—install in Dockerfile.babel.

Performance: 3-5 mins for 154 files—subprocess spin-up (1-2s/file)—time’s no rush.

Future: Babel Node container—add plug-ins (e.g., ESLint) later.

Troubleshooting
Docker Run Fails: Check volume path—/Users/Thy/Today must exist, match GetReal root.

JSON Errors: Subprocess output garbled—ensure babel_parser.js prints clean JSON.

File Write Fails: Permissions—file_handler.py needs write access to /project.

Logs Silent: particle_utils.logger misconfigured—test with print.

Why This Works
Relevancy: Babel’s 95%+—props (nested, spreads), hooks, logic—graph’s deep.

Accuracy: File path handoff—no JSON escaping risks, raw JS/JSX parsed.

Two Containers: MCP pure, Babel isolated—future plug-ins slot in.

Breeze: Subprocess—simplest sync, no server/pipe overhead.

Your Next Moves
Files:
babel_parser.js—Babel parsing logic.

Dockerfile.babel—Node image.

addSubParticle.py—Subprocess call.

docker-compose.yml—Two-container glue.

Build & Run: docker-compose up --build.

Test: Single file → full graph.

Check: Logs, SubParticles, graph—95%+ relevancy?


__________
10.03.25

Updated Setup Plan: Babel in Docker with Subprocess Sync
Context
Particle-Graph Repo: /Users/Thy/Particle-graph—Python MCP, all .py files.

GetReal Repo: /Users/Thy/today—JS/React Native codebase, mounts as /project.

Goal: Replace Tree-sitter with Babel for 95%+ relevancy—props, hooks, logic—via subprocess.

1. Babel Parser Container
babel_parser.js:
Path: /Users/Thy/Particle-graph/babel_parser.js.

Content: (Already shared—parses file, returns JSON with purpose, props, hooks, calls, key_logic, depends_on).

Key: Matches your generate_subparticle output—Babel handles all extraction.

Dockerfile.babel:
Path: /Users/Thy/Particle-graph/Dockerfile.babel.

Content:
dockerfile

FROM node:16-slim
WORKDIR /app
COPY babel_parser.js .
RUN npm install @babel/parser
CMD ["node", "babel_parser.js"]

Build:
bash

cd /Users/Thy/Particle-graph
docker build -f Dockerfile.babel -t babel-parser .

2. Update Particle-Graph MCP
addSubParticle.py (reworked):
Path: /Users/Thy/Particle-graph/addSubParticle.py.

Content:
python

import subprocess
from file_handler import read_file, write_subparticle
from particle_utils import logger
import json
import os

def generate_subparticle(file_path: str = None, rich: bool = True) -> dict:
    """
    Generate SubParticle for a given file using Babel Docker.
    """
    if not file_path:
        return {"error": "No file_path provided"}

    content, error = read_file(file_path)
    if error:
        return error

    # Call Babel container
    try:
        result = subprocess.run(
            ['docker', 'run', '--rm', '-v', '/Users/Thy/today:/app', 'babel-parser', file_path],
            capture_output=True,
            text=True,
            check=True
        )
        context = json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        logger.error(f"Babel parse failed for {file_path}: {e.stderr}")
        return {"error": f"Babel parse failed: {e.stderr}"}
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON from Babel for {file_path}: {e}")
        return {"error": f"Invalid JSON: {e}"}

    # Extract counts for summary
    props = context.get("props", [])
    hooks = context.get("hooks", [])
    calls = context.get("calls", [])
    key_logic = context.get("key_logic", [])
    depends_on = context.get("depends_on", [])

    export_str, error = write_subparticle(file_path, context)
    if error:
        return error

    summary = f"Found {len(props)} props, {len(hooks)} hooks, {len(calls)} calls"
    if rich:
        summary += f", {len(key_logic)} key logic, {len(depends_on)} dependencies"

    return {
        "content": [{"type": "text", "text": export_str}],
        "summary": summary,
        "status": "OK",
        "isError": False,
        "note": "SubParticle applied directly to file",
        "post_action": "read"
    }

def addSubParticle(file_path: str = None, rich: bool = True) -> dict:
    return generate_subparticle(file_path, rich=rich)

def addAllSubParticle(root_dir: str = "/project", rich: bool = True) -> dict:
    """
    Generate SubParticles for all .jsx/.js files in the root directory, respecting .gitignore.
    """
    from pathlib import Path
    import pathspec

    def load_gitignore(root_dir):
        gitignore_path = Path(root_dir) / ".gitignore"
        if gitignore_path.exists():
            with open(gitignore_path, "r") as f:
                return pathspec.PathSpec.from_lines("gitwildmatch", f)
        return pathspec.PathSpec.from_lines("gitwildmatch", [])

    gitignore = load_gitignore(root_dir)
    root_path = Path(root_dir)
    modified_count = 0
    errors = []

    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith((".jsx", ".js")):
                file_path = Path(root) / file
                rel_path = file_path.relative_to(root_path)
                
                if gitignore.match_file(rel_path):
                    logger.debug(f"Skipped (gitignore): {rel_path}")
                    continue
                
                try:
                    result = generate_subparticle(str(file_path), rich)  # Use absolute path
                    if result.get("isError", True):
                        errors.append(f"{rel_path}: {result['error']}")
                    else:
                        modified_count += 1
                        logger.info(f"SubParticled: {rel_path}")
                except Exception as e:
                    errors.append(f"{rel_path}: {e}")

    status = "OK" if not errors else "PARTIAL"
    summary = f"Modified {modified_count} files"
    if errors:
        summary += f", {len(errors)} errors: {', '.join(errors[:3])}" + (len(errors) > 3 and "..." or "")
    
    return {
        "content": [{"type": "text", "text": summary}],
        "summary": summary,
        "status": status,
        "isError": len(errors) > 0,
        "note": f"SubParticles applied to {modified_count} files in {root_dir}"
    }

if __name__ == "__main__":
    addSubParticle("/Users/Thy/today/components/Features/Hub/components/shared/HubContent.jsx")

Changes:
Drop imports for prop_parser, hook_analyzer, etc.—Babel does it all.

Subprocess calls Babel Docker—file path handoff.

Keep write_subparticle, logger, addAllSubParticle logic—structure intact.

Dockerfile (updated):
Path: /Users/Thy/Particle-graph/Dockerfile.

Content:
dockerfile

FROM python:3.10
WORKDIR /app
COPY server.py particle_utils.py createParticle.py loadGraph.py listGraph.py updateParticle.py exportGraph.py deleteParticle.py addSubParticle.py list_dir.py check_root.py tech_stack.py prop_parser.py hook_analyzer.py call_detector.py logic_inferer.py dependency_tracker.py context_builder.py file_handler.py populate_and_graph.py populate.py ./
RUN pip install fastmcp lark pathspec
EXPOSE 8000
CMD ["python", "server.py"]

Notes: Drops tree-sitter—not needed with Babel.

3. Docker Compose
docker-compose.yml:
Path: /Users/Thy/Particle-graph/docker-compose.yml.

Content:
yaml

version: '3'
services:
  particle-graph:
    build: .
    volumes:
      - /Users/Thy/today:/project
  babel-parser:
    build:
      context: .
      dockerfile: Dockerfile.babel
    volumes:
      - /Users/Thy/today:/app

Build & Run:
bash

cd /Users/Thy/Particle-graph
docker-compose up --build

4. Test & Scale
Test Single File:
bash

docker-compose run particle-graph python -c "from addSubParticle import addSubParticle; addSubParticle('/project/components/Features/Hub/components/shared/HubContent.jsx')"

Full Graph:
bash

docker-compose run particle-graph python -c "from addSubParticle import addAllSubParticle; from exportGraph import exportGraph; addAllSubParticle('/project'); exportGraph(['app', 'components', 'lib'])"

5. Validate
Logs: Check logger—“SubParticled: ...” or errors.

File: HubContent.jsx—SubParticle with props, logic, etc.

Graph: full_codebase_graph.json—154 files, deep insights.

Key Notes
Volumes: 
/Users/Thy/today:/project (MCP), /Users/Thy/today:/app (Babel)—syncs GetReal.

Deps: 
MCP: fastmcp, lark, pathspec.

Babel: @babel/parser (Docker-only).

Backup: Save old addSubParticle.py—Tree-sitter’s your fallback.

Troubleshooting
Subprocess Fail: Test docker run -v /Users/Thy/today:/app babel-parser /app/path—check stderr.

Path Error: file_path must be absolute—/project/... in Docker.

Write Fail: file_handler.py perms—/project writable?

Why It Fits
Relevancy: Babel’s 95%+—replaces your modular parsers with one shot.

Structure: Keeps generate_subparticle, addAllSubParticle—just swaps the engine.

Sync: Subprocess—simple, accurate, file path handoff.

Next Steps
Add: babel_parser.js, Dockerfile.babel, docker-compose.yml.

Update: addSubParticle.py, Dockerfile.

Run: docker-compose up --build, then test.

