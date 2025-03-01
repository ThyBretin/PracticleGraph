import json
import sqlite3
from fastmcp import FastMCP
import os
import logging
from config_loader import ConfigLoader
from watchdog_service import WatchdogService
import shutil
import fnmatch
import re
from datetime import datetime

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
        version INTEGER DEFAULT 0,
        last_updated TEXT
    )
""")
conn.commit()
conn.close()

class PracticalGraphServer:
    def __init__(self):
        self.config_loader = ConfigLoader()  # Let it auto-detect config
        self.config = self.config_loader.load_config()
        
        if not self.config:
            logger.error("Failed to load configuration")
            raise ValueError("No valid configuration found")
            
        self.watchdog = WatchdogService(self.config, update_callback=self._on_files_changed)
        self.mcp = FastMCP('practical-graph')
        self.version = 0
        
        # Run initial file scan to populate the graph
        self._initial_scan()

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
            
    def _initial_scan(self):
        """Run an initial scan of the app directory on startup"""
        logger.info("Running initial file scan")
        try:
            self.get_context()
            logger.info("Initial file scan complete")
        except Exception as e:
            logger.error(f"Error during initial scan: {e}")
            
    def _on_files_changed(self, changed_files):
        """Callback when files are changed, triggers a graph update"""
        logger.info(f"Files changed, updating graph: {len(changed_files)} files")
        try:
            self.get_context()
        except Exception as e:
            logger.error(f"Error updating graph after file changes: {e}")

    @self.mcp.tool()
    def get_context(query: str = None) -> dict:
        """Retrieve the graph context of the application
        
        Parameters:
        - query: Optional. When provided, only returns entities matching the query.
                 Examples: "events.jsx", "auth/*", "features:profile"
        """
        logger.info(f"Running get_context with query: {query}")
        conn = sqlite3.connect("/tmp/graph.db")
        
        # If a query is provided, filter the results
        if query:
            return self._query_context(conn, query)
        
        # Otherwise, perform a full scan and update
        folder_lookup = {}
        for group, folders in self.config["folder_groups"].items():
            for folder in folders:
                folder_lookup[folder] = group
        
        entities = []
        self._backup_database()
        
        # Get the current timestamp
        timestamp = datetime.now().isoformat()
        
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
                            "INSERT OR REPLACE INTO entities (name, type, tags, relations, version, last_updated) VALUES (?, ?, ?, ?, ?, ?)",
                            (entity["name"], entity["type"], json.dumps(entity["tags"]), json.dumps(entity["relations"]), self.version, timestamp)
                        )
                else:
                    conn.execute(
                        "INSERT OR REPLACE INTO entities (name, type, tags, relations, version, last_updated) VALUES (?, ?, ?, ?, ?, ?)",
                        (entity["name"], entity["type"], json.dumps(entity["tags"]), json.dumps(entity["relations"]), self.version, timestamp)
                    )

        conn.commit()
        conn.close()
        
        self.version += 1
        
        return {"entities": entities, "version": self.version}
    
    def _query_context(self, conn, query: str) -> dict:
        """Internal method to query the graph context with a filter"""
        cursor = conn.cursor()
        entities = []
        
        # Determine the type of query
        if ':' in query:
            # Group or full path query
            parts = query.split(':')
            if len(parts) == 2:
                group, rest = parts
                if '*' in rest:
                    # Wildcard search within group
                    pattern = f"{group}:{rest.replace('*', '%')}"
                    cursor.execute("SELECT name, type, tags, relations FROM entities WHERE name LIKE ?", (pattern,))
                else:
                    # Exact folder or file in group
                    cursor.execute("SELECT name, type, tags, relations FROM entities WHERE name LIKE ?", (f"{group}:{rest}%",))
            elif len(parts) == 3:
                # Fully qualified query
                group, folder, file = parts
                pattern = f"{group}:{folder}:{file}".replace('*', '%')
                cursor.execute("SELECT name, type, tags, relations FROM entities WHERE name LIKE ?", (pattern,))
        elif '/' in query or '*' in query:
            # Path-like query
            if query.endswith('/*'):
                # All files in a folder
                folder = query[:-2]
                cursor.execute("SELECT name, type, tags, relations FROM entities WHERE name LIKE ?", (f"%:{folder}:%",))
            else:
                # Specific file by path
                cursor.execute("SELECT name, type, tags, relations FROM entities WHERE tags LIKE ?", (f"%@ref:%{query}%",))
        else:
            # Simple filename search
            cursor.execute("SELECT name, type, tags, relations FROM entities WHERE name LIKE ?", (f"%:{query}",))
        
        rows = cursor.fetchall()
        
        for row in rows:
            name, entity_type, tags_json, relations_json = row
            entities.append({
                "name": name,
                "type": entity_type,
                "tags": json.loads(tags_json),
                "relations": json.loads(relations_json)
            })
        
        return {"entities": entities, "count": len(entities), "query": query}
        
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
    
    @self.mcp.tool()
    def create_reference_doc(filename: str = "codebase_reference.md") -> dict:
        """Create a markdown reference document based on the current graph
        
        Parameters:
        - filename: The name of the reference file to create (default: codebase_reference.md)
        """
        logger.info(f"Creating reference document: {filename}")
        try:
            # Get the full graph data
            graph_data = self.get_graph_snapshot()
            entities = graph_data["entities"]
            
            # Group entities by their group and folder
            grouped_entities = {}
            for entity in entities:
                parts = entity["name"].split(":")
                if len(parts) >= 3:
                    group, folder, file = parts
                    if group not in grouped_entities:
                        grouped_entities[group] = {}
                    if folder not in grouped_entities[group]:
                        grouped_entities[group][folder] = []
                    grouped_entities[group][folder].append({
                        "file": file,
                        "tags": entity["tags"],
                        "relations": entity["relations"]
                    })
            
            # Create the markdown content
            content = "# Codebase Reference\n\n"
            content += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            content += "## Structure Overview\n\n"
            
            # Add TOC
            for group in sorted(grouped_entities.keys()):
                content += f"- [{group.capitalize()}](#{group})\n"
                for folder in sorted(grouped_entities[group].keys()):
                    content += f"  - [{folder}](#{group}-{folder})\n"
            
            content += "\n## Detailed Structure\n\n"
            
            # Add detailed content
            for group in sorted(grouped_entities.keys()):
                content += f"### {group.capitalize()}\n\n"
                content += f"<a id='{group}'></a>\n"
                
                for folder in sorted(grouped_entities[group].keys()):
                    content += f"#### {folder}\n\n"
                    content += f"<a id='{group}-{folder}'></a>\n"
                    content += "| File | Relations | Documentation |\n"
                    content += "|------|-----------|---------------|\n"
                    
                    for item in sorted(grouped_entities[group][folder], key=lambda x: x["file"]):
                        file = item["file"]
                        relations = ", ".join([r for r in item["relations"]])
                        docs = ""
                        for tag in item["tags"]:
                            if tag.startswith("@doc:"):
                                docs += f"[Docs]({tag[5:]})"
                        
                        content += f"| {file} | {relations} | {docs} |\n"
                    
                    content += "\n"
                
            # Write the file
            target_path = os.path.join(self.config["app_path"], filename)
            with open(target_path, "w") as f:
                f.write(content)
                
            # Add the reference doc to the config if it's not already there
            ref_path = os.path.join("/", filename)
            if "reference" not in self.config["docs"]:
                self.config["docs"]["reference"] = ref_path
                # This change won't persist unless we save the config
                # We'll just note this in the return so the user can update manually
                
            return {
                "success": True, 
                "path": target_path,
                "note": "Reference document created. To permanently add to docs configuration, add: 'reference': '" + ref_path + "'"
            }
        except Exception as e:
            logger.error(f"Failed to create reference document: {e}")
            return {"success": False, "error": str(e)}

if __name__ == "__main__":
    server = PracticalGraphServer()
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()