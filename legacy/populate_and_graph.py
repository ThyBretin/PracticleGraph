import os
from pathlib import Path
import json
import re
from addParticle import addAllParticle
from file_handler import read_file
from particle_utils import logger

def populate_and_graph(root_dir="/project"):
    # Step 1: Populate
    logger.info("Running addAllParticle...")
    result = addAllParticle(root_dir)
    logger.info(f"Population result: {result}")

    # Step 2: Crawl and log
    files = {}
    root_path = Path(root_dir)
    file_count = 0
    for root, _, filenames in os.walk(root_dir):
        logger.info(f"Scanning dir: {root}")
        for file in filenames:
            if file.endswith((".jsx", ".js")):
                file_count += 1
                file_path = Path(root) / file
                rel_path = file_path.relative_to(root_path)
                logger.info(f"Found: {file_path}")
                
                content, error = read_file(str(rel_path))
                if error or not content:
                    logger.warning(f"Skipped {file_path}: {error or 'No content'}")
                    continue
                
                if "export const Particle =" not in content:
                    logger.warning(f"No Particle in {file_path}")
                    continue
                
                # Extract Particle JSON with regex
                match = re.search(r"export const Particle = (\{.*?\});", content, re.DOTALL)
                if not match:
                    logger.warning(f"No valid Particle JSON in {file_path}")
                    continue
                
                try:
                    context = json.loads(match.group(1))
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid Particle in {file_path}: {e}")
                    continue

                # Group by feature
                feature = str(rel_path.parts[0]).lower() if rel_path.parts else "other"
                if feature not in files:
                    files[feature] = {"primary": [], "shared": []}
                category = "shared" if "shared" in str(rel_path) or "_test_" in str(rel_path) else "primary"
                files[feature][category].append({
                    "path": str(rel_path),
                    "type": "test" if "_test_" in str(rel_path) else "file",
                    "context": context
                })
                logger.info(f"Added {rel_path} to {feature}/{category}")

    # Step 3: Tech stack
    tech_stack = {"core": [], "deps": []}
    pkg_path = root_path / "package.json"
    if pkg_path.exists():
        with open(pkg_path, "r") as f:
            pkg = json.load(f)
            tech_stack["core"] = pkg.get("dependencies", {})
            tech_stack["deps"] = pkg.get("devDependencies", {})

    # Step 4: Graph
    from datetime import datetime
    graph = {
        "aggregate": True,
        "graph": list(files.keys()),
        "last_crawled": datetime.utcnow().isoformat() + "Z",
        "tech_stack": tech_stack,
        "files": files
    }
    
    # Step 5: Save
    output_path = root_path / "particle-graph" / "full_codebase_graph.json"
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(graph, f, indent=2)
    logger.info(f"Graph saved: {output_path} with {file_count} files scanned, {sum(len(f['primary']) + len(f['shared']) for f in files.values())} added")

if __name__ == "__main__":
    populate_and_graph("/project")