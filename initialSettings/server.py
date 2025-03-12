import json
import sqlite3
from fastmcp import FastMCP
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ParticleGraph")

# SQLite setup
conn = sqlite3.connect("/tmp/graph.db")
conn.execute("""
    CREATE TABLE IF NOT EXISTS entities (
        name TEXT PRIMARY_KEY,
        type TEXT,
        tags TEXT,
        relations TEXT
    )
""")
conn.commit()
conn.close()

# MCP Server
mcp = FastMCP("particle-graph")

@mcp.tool()
def get_context() -> dict:
    """Retrieve the graph context of the application"""
    logger.info("Running get_context")
    conn = sqlite3.connect("/tmp/graph.db")
    folder_groups = {
        "core": ["navigation", "state", "auth", "database"],
        "features": ["event", "discovery", "profile"],
        "api": ["endpoints"],
        "lib": ["supabase"]
    }
    docs = {
        "business": "/docs/business-rules.md",
        "event": "/docs/event-system.md"
    }
    
    folder_lookup = {}
    for group, folders in folder_groups.items():
        for folder in folders:
            folder_lookup[folder] = group
    
    entities = []
    for dirpath, _, filenames in os.walk("/path/to/your/app"):
        folder = os.path.basename(dirpath).lower()
        group = folder_lookup.get(folder, "misc")
        
        for filename in filenames:
            full_path = os.path.join(dirpath, filename)
            tags = [f"@ref:{full_path}"]
            if folder in folder_lookup:
                tags.append(f"@folder:{folder}")
            for doc_key, doc_path in docs.items():
                if folder.startswith(doc_key):
                    tags.append(f"@doc:{doc_path}")
            
            relations = []
            if filename.endswith(".jsx"):
                relations.append(">render:component")
            elif "service" in filename.lower() or folder in ["lib", "supabase"]:
                relations.append("#use:service")
            elif "db" in folder or "table" in filename.lower():
                relations.append("$db:unknown_table")
            elif "api" in folder or "endpoint" in filename.lower():
                relations.append("~fetch:api")
            if "event" in folder or "location" in filename.lower():
                relations.append("@business:engagement")
            
            entity = {
                "name": f"{group}:{folder}:{filename}",
                "type": "file",
                "tags": tags,
                "relations": relations
            }
            entities.append(entity)
            conn.execute(
                "INSERT OR REPLACE INTO entities (name, type, tags, relations) VALUES (?, ?, ?, ?)",
                (entity["name"], entity["type"], json.dumps(entity["tags"]), json.dumps(entity["relations"]))
            )
    conn.commit()
    conn.close()
    
    return {"entities": entities}

if __name__ == "__main__":
    logger.info("Starting ParticleGraph server")
    mcp.run()