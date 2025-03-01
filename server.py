import json
import sqlite3
from fastmcp import FastMCP
import os
import logging
from config_loader import ConfigLoader
from watchdog_service import WatchdogService
import shutil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PracticalGraph")

# SQLite setup
conn = sqlite3.connect("/tmp/graph.db")
conn.execute("""
    CREATE TABLE IF NOT EXISTS entities (
        name TEXT PRIMARY_KEY,
        type TEXT,
        tags TEXT,
        relations TEXT,
        version INTEGER DEFAULT 0
    )
""")
conn.commit()
conn.close()

class PracticalGraphServer:
    def __init__(self):
        self.config_loader = ConfigLoader('/path/to/config.json')
        self.config = self.config_loader.load_config()
        self.watchdog = WatchdogService(self.config)
        self.mcp = FastMCP('practical-graph')
        self.version = 0

    def start(self):
        logger.info('Starting Practical Graph server')
        self.watchdog.start()
        self.mcp.run()

    def stop(self):
        logger.info('Stopping Practical Graph server')
        self.watchdog.stop()

    def _backup_database(self):
        """Create a backup of the database before updating"""
        backup_path = f"/tmp/graph.db.backup.{self.version}"
        try:
            shutil.copy("/tmp/graph.db", backup_path)
            logger.info(f"Database backed up to {backup_path}")
        except Exception as e:
            logger.error(f"Failed to backup database: {e}")

    @self.mcp.tool()
    def get_context() -> dict:
        """Retrieve the graph context of the application"""
        logger.info("Running get_context")
        conn = sqlite3.connect("/tmp/graph.db")
        folder_lookup = {}
        for group, folders in self.config["folder_groups"].items():
            for folder in folders:
                folder_lookup[folder] = group
        
        entities = []
        self._backup_database()
        for dirpath, _, filenames in os.walk(self.config["app_path"]):
            folder = os.path.basename(dirpath).lower()
            group = folder_lookup.get(folder, "misc")
            
            for filename in filenames:
                full_path = os.path.join(dirpath, filename)
                tags = [f"@ref:{full_path}"]
                if folder in folder_lookup:
                    tags.append(f"@folder:{folder}")
                for doc_key, doc_path in self.config["docs"].items():
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

                # Conflict resolution: check version before update
                cursor = conn.execute("SELECT version FROM entities WHERE name = ?", (entity["name"],))
                result = cursor.fetchone()
                if result:
                    existing_version = result[0]
                    if existing_version < self.version:
                        conn.execute(
                            "INSERT OR REPLACE INTO entities (name, type, tags, relations, version) VALUES (?, ?, ?, ?, ?)",
                            (entity["name"], entity["type"], json.dumps(entity["tags"]), json.dumps(entity["relations"]), self.version)
                        )
                else:
                    conn.execute(
                        "INSERT OR REPLACE INTO entities (name, type, tags, relations, version) VALUES (?, ?, ?, ?, ?)",
                        (entity["name"], entity["type"], json.dumps(entity["tags"]), json.dumps(entity["relations"]), self.version)
                    )

        conn.commit()
        conn.close()
        
        self.version += 1
        
        return {"entities": entities, "version": self.version}
        
    @self.mcp.tool()
    def export_graph(target_path: str) -> dict:
        """Export the graph database to a user-specified location"""
        logger.info(f"Exporting graph database to {target_path}")
        try:
            # Make sure the parent directory exists
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            
            # Create a copy of the database
            shutil.copy("/tmp/graph.db", target_path)
            return {"success": True, "path": target_path}
        except Exception as e:
            logger.error(f"Failed to export graph: {e}")
            return {"success": False, "error": str(e)}

    @self.mcp.tool()
    def import_graph(source_path: str) -> dict:
        """Import a graph database from a user-specified location"""
        logger.info(f"Importing graph database from {source_path}")
        try:
            if not os.path.exists(source_path):
                logger.error(f"Source file not found: {source_path}")
                return {"success": False, "error": "Source file not found"}
                
            # Backup current database first
            self._backup_database()
            
            # Replace the current database
            shutil.copy(source_path, "/tmp/graph.db")
            
            # Reset version to avoid conflicts
            self.version += 1
            
            return {"success": True}
        except Exception as e:
            logger.error(f"Failed to import graph: {e}")
            return {"success": False, "error": str(e)}

    @self.mcp.tool()
    def get_graph_snapshot() -> dict:
        """Get a JSON representation of the current graph"""
        logger.info("Creating graph snapshot")
        conn = sqlite3.connect("/tmp/graph.db")
        cursor = conn.execute("SELECT name, type, tags, relations FROM entities")
        entities = []
        
        for row in cursor:
            name, entity_type, tags_json, relations_json = row
            entities.append({
                "name": name,
                "type": entity_type,
                "tags": json.loads(tags_json),
                "relations": json.loads(relations_json)
            })
            
        conn.close()
        return {"entities": entities}

if __name__ == "__main__":
    server = PracticalGraphServer()
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()