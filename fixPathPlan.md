Project Overview
Goal: Build a dependency graph for GetReal (/Users/Thy/Today), targeting 95%+ relevancy.

Setup: 
Directory: /Users/Thy/Particule-Graph/.

Docker mounts GetReal at /project in the container.

MCP (gRPC server) runs tools like createParticule, addSubParticule, exportGraph.

Current State: 
Pre-Babel: Worked—parsed files, built graphs.

Post-Babel: Added babel_parser.js, hit path and subprocess snags—reverted.

Now: MCP starts (server.py), logs show main loop, but localhost:8000 refuses connections.

What We’ve Done
Initial Debugging (Babel Era):
Problem: docker run errors—MODULE_NOT_FOUND, permission denied.

Fix: Added babel_parser.js, adjusted paths (/getreal → /project), merged into one container.

Result: Parsed HubContent.jsx, but exportGraph crashed (list.split()).

Revert to Pre-Babel:
Why: Babel overcomplicated things—worked fine before.

Changes: 
Dropped babel_parser.js from Dockerfile.

Simplified addSubParticule.py—no subprocess, basic parsing.

Result: docker-compose run worked up to exportGraph('app,components,lib').

Switch to MCP:
Goal: Run via server.py (FastMCP), use grpcurl for tools, watch docker logs.

Commands:
bash

docker build -t particule-graph .
docker run -d -m 2g -v /Users/Thy/Today:/project -p 8000:8000 --name particule-graph particule-graph

Logs: Server initialized, entering main loop—running, but nc -zv localhost 8000 fails.

Port Debugging:
Issue: connection refused—port 8000 not reachable.

Tried: 
Verified -p 8000:8000.

Checked docker ps, docker inspect.

Suggested netstat inside container, host port conflicts.

Status: Server’s up, but host can’t connect—port mapping or binding glitch.

How It Should Work
Flow:
MCP Server: server.py starts FastMCP on 0.0.0.0:8000, registers tools.

Tools:
createParticule: Initializes a feature graph (e.g., "app").

addSubParticule: Parses a file (e.g., HubContent.jsx), adds SubParticule.

addAllSubParticule: Scans /project, applies SubParticule to all .jsx/.js.

exportGraph: Loads graph from particule_cache, saves JSON (e.g., app_components_lib_graph_<timestamp>.json).

Client: grpcurl calls tools—e.g., grpcurl -d '{"tool": "createParticule", "args": "app"}' localhost:8000.

Output: Graph JSON in /app/particule-graph/—154 files, 95%+ depth.

Docker:
Build: docker build -t particule-graph .

Run: docker run -d -m 2g -v /Users/Thy/Today:/project -p 8000:8000 --name particule-graph particule-graph

Logs: docker logs -f particule-graph—shows tool execution.

gRPC:
List: grpcurl -plaintext localhost:8000 mcp.lowlevel.MCPServer/ListTools

Call: grpcurl -plaintext -d '{"tool": "<tool>", "args": "<args>"}' localhost:8000 mcp.lowlevel.MCPServer/CallTool

Key Files + Expected Content
1. Dockerfile
Path: /Users/Thy/Particule-Graph/Dockerfile

Content (Pre-Babel):
dockerfile

FROM python:3.10
WORKDIR /app
COPY server.py particule_utils.py createParticule.py loadGraph.py listGraph.py updateParticule.py exportGraph.py deleteParticule.py addSubParticule.py list_dir.py check_root.py tech_stack.py prop_parser.py hook_analyzer.py call_detector.py logic_inferer.py dependency_tracker.py context_builder.py file_handler.py populate_and_graph.py populate.py ./
RUN pip install fastmcp lark pathspec
EXPOSE 8000
CMD ["python", "server.py"]

Purpose: Builds Python-only image, runs MCP server.

2. server.py
Path: /Users/Thy/Particule-Graph/server.py

Content (Yours):
python

from fastmcp import FastMCP
import logging
from particule_utils import app_path
from check_root import check_root
from list_dir import list_dir
from addSubParticule import addSubParticule, addAllSubParticule
from createParticule import createParticule
from updateParticule import updateParticule
from deleteParticule import deleteParticule
from listGraph import listGraph
from loadGraph import loadGraph
from exportGraph import exportGraph

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("ParticuleGraph")

def main():
    mcp = FastMCP("particule-graph")
    mcp.tool()(addSubParticule) 
    mcp.tool()(addAllSubParticule)
    mcp.tool()(createParticule)
    mcp.tool()(updateParticule)
    mcp.tool()(deleteParticule)
    mcp.tool()(listGraph)
    mcp.tool()(loadGraph)
    mcp.tool()(exportGraph)
    mcp.tool()(list_dir)
    mcp.tool()(check_root)
    logger.info("Server initialized, entering main loop")
    mcp.run()  # Should bind to 0.0.0.0:8000

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Server crashed: {e}")
        raise

Purpose: Starts MCP, registers tools, listens on port 8000.

Expect: Logs show DEBUG:mcp.server.lowlevel.server:Initializing..., INFO:Server initialized.

3. addSubParticule.py
Path: /Users/Thy/Particule-Graph/addSubParticule.py

Content (Pre-Babel, Simplified):
python

from file_handler import read_file, write_subparticule
from particule_utils import logger
from pathlib import Path

PROJECT_ROOT = "/project"

def generate_subparticule(file_path: str = None, rich: bool = True) -> dict:
    logger.info(f"Starting generate_subparticule with file_path: {file_path}")
    if not file_path:
        logger.error("No file_path provided")
        return {"error": "No file_path provided"}

    if file_path.startswith(PROJECT_ROOT):
        relative_path = file_path[len(PROJECT_ROOT) + 1:]
    else:
        relative_path = file_path

    absolute_path = Path(PROJECT_ROOT) / relative_path
    logger.debug(f"Relative: {relative_path}, Absolute: {absolute_path}")

    content, error = read_file(relative_path)
    if error:
        logger.error(f"Read failed: {error}")
        return {"error": f"Read failed: {error}"}

    context = {
        "purpose": f"Handles {Path(relative_path).stem.lower()} functionality",
        "props": [],
        "hooks": [],
        "calls": [],
        "key_logic": ["Basic functionality"],
        "depends_on": ["react"]
    }
    export_str, error = write_subparticule(relative_path, context)
    if error:
        logger.error(f"Write failed: {error}")
        return {"error": f"Write failed: {error}"}

    summary = "Found 0 props, 0 hooks, 0 calls, 1 key logic, 1 dependency"
    logger.info(f"Summary: {summary}")
    return {
        "content": [{"type": "text", "text": export_str}],
        "summary": summary,
        "status": "OK",
        "isError": False,
        "note": "SubParticule applied",
        "post_action": "read"
    }

def addSubParticule(file_path: str = None, rich: bool = True) -> dict:
    return generate_subparticule(file_path, rich)

def addAllSubParticule(root_dir: str = PROJECT_ROOT, rich: bool = True) -> dict:
    from pathlib import Path
    import pathspec

    logger.info(f"Starting addAllSubParticule for {root_dir}")
    gitignore = pathspec.PathSpec.from_lines("gitwildmatch", [])
    root_path = Path(root_dir)
    modified_count = 0
    errors = []

    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith((".jsx", ".js")):
                file_path = Path(root) / file
                rel_path = file_path.relative_to(root_path)
                if gitignore.match_file(rel_path):
                    logger.debug(f"Skipped: {rel_path}")
                else:
                    try:
                        result = generate_subparticule(str(file_path), rich)
                        if result.get("isError", True):
                            errors.append(f"{rel_path}: {result['error']}")
                        else:
                            modified_count += 1
                            logger.info(f"SubParticuled: {rel_path}")
                    except Exception as e:
                        errors.append(f"{rel_path}: {e}")

    status = "OK" if not errors else "PARTIAL"
    summary = f"Modified {modified_count} files"
    if errors:
        summary += f", {len(errors)} errors: {', '.join(errors[:3])}" + (len(errors) > 3 and "..." or "")
    logger.info(f"Summary: {summary}")
    return {
        "content": [{"type": "text", "text": summary}],
        "summary": summary,
        "status": status,
        "isError": len(errors) > 0,
        "note": f"SubParticules applied to {modified_count} files"
    }

Purpose: Parses files, writes SubParticule blocks—replace context with your original parser (e.g., lark).

Expect: Logs like INFO:SubParticuled: components/....

4. exportGraph.py
Path: /Users/Thy/Particule-Graph/exportGraph.py

Content (Yours):
python

import json
from datetime import datetime
from pathlib import Path
from particule_utils import app_path, logger
from loadGraph import loadGraph

def exportGraph(features: str) -> dict:
    manifest = loadGraph(features)
    if "error" in manifest:
        return {"error": manifest["error"]}

    feature_str = "_".join(manifest.get("features", [features])).lower()
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    filename = f"{feature_str}_graph_{timestamp}.json" if not manifest.get("aggregate") else f"aggregate_{feature_str}_{timestamp}.json"
    output_path = Path(app_path) / "particule-graph" / filename

    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    
    logger.info(f"Exported {output_path}")
    return {"content": [{"type": "text", "text": f"Saved {output_path}"}], "isError": False}

Purpose: Exports graph JSON to /app/particule-graph/.

Expect: File like app_components_lib_graph_2025...json.

5. loadGraph.py
Path: /Users/Thy/Particule-Graph/loadGraph.py

Content (Yours):
python

from datetime import datetime
from particule_utils import particule_cache, logger

def loadGraph(features: str) -> dict:
    feature_list = [f.strip().lower() for f in features.split(",")]
    logger.debug(f"Loading Particule Graphs: {feature_list}")

    if len(feature_list) == 1:
        feature = feature_list[0]
        if feature not in particule_cache:
            logger.error(f"Particule Graph '{feature}' not found in cache")
            return {"error": f"Particule Graph '{feature}' not found"}
        logger.info(f"Loaded single Particule Graph: {feature}")
        return particule_cache[feature]

    missing = [f for f in feature_list if f not in particule_cache]
    if missing:
        logger.error(f"Particles Graphs not found in cache: {missing}")
        return {"error": f"Particles Graphs not found: {missing}"}

    aggregated_tech = {}
    for feature in feature_list:
        tech = particule_cache[feature]["tech_stack"]
        for category, value in tech.items():
            if isinstance(value, dict):
                if category not in aggregated_tech:
                    aggregated_tech[category] = {}
                aggregated_tech[category].update(value)
            else:
                aggregated_tech[category] = value

    aggregated_files = {}
    for feature in feature_list:
        aggregated_files[feature] = particule_cache[feature]["files"]

    manifest = {
        "aggregate": True,
        "graph": feature_list,
        "last_crawled": datetime.utcnow().isoformat() + "Z",
        "tech_stack": aggregated_tech,
        "files": aggregated_files
    }
    logger.info(f"Aggregated Particules Graph: {feature_list}")
    return manifest

Purpose: Loads graph from particule_cache—needs createParticule to populate it.

Expect: Logs like INFO:Aggregated Particules Graph: ['app', 'components', 'lib'].

6. createParticule.py (Assumed)
Path: /Users/Thy/Particule-Graph/createParticule.py

Content (Guess—Adjust):
python

from particule_utils import logger, particule_cache

def createParticule(feature: str) -> dict:
    logger.info(f"Creating Particule for feature: {feature}")
    if not feature:
        logger.error("No feature provided")
        return {"error": "No feature provided"}

    particule_cache[feature] = {
        "tech_stack": {"framework": "react"},
        "files": []
    }
    logger.info(f"Particule created: {feature}")
    return {"content": [{"type": "text", "text": f"Created {feature}"}], "isError": False}

Purpose: Initializes a feature in particule_cache—loadGraph needs this.

Current Problem
Symptoms: 
docker logs: Server initialized, entering main loop.

nc -zv localhost 8000: connection refused.

Cause: 
Port 8000 not exposed (-p 8000:8000 missed or failed).

Possible host port conflict.

Fix:
bash

docker rm -f particule-graph
docker run -d -m 2g -v /Users/Thy/Today:/project -p 8000:8000 --name particule-graph particule-graph
nc -zv localhost 8000

Instructions for Claude
Context: 
MCP server (server.py) uses fastmcp—should bind to 0.0.0.0:8000.

Docker maps /Users/Thy/Today to /project—all paths use /project.

Goal: Run tools via grpcurl, see logs, export graph JSON.

Steps:
Build: docker build -t particule-graph .

Run: docker run -d -m 2g -v /Users/Thy/Today:/project -p 8000:8000 --name particule-graph particule-graph

Logs: docker logs -f particule-graph

Test: nc -zv localhost 8000—if refused, check lsof -i :8000, try -p 8001:8000.

Tools: grpcurl -plaintext localhost:8000 mcp.lowlevel.MCPServer/ListTools, then call createParticule, addAllSubParticule, exportGraph.

Files: Use above contents—adjust createParticule.py and file_handler.py parsing if needed.

