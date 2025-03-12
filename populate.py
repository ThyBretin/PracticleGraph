import os
from pathlib import Path
import re
from addSubParticle import addSubParticle
import pathspec

def load_gitignore(root_dir):
    gitignore_path = Path(root_dir) / ".gitignore"
    if gitignore_path.exists():
        with open(gitignore_path, "r") as f:
            return pathspec.PathSpec.from_lines("gitwildmatch", f)
    return pathspec.PathSpec.from_lines("gitwildmatch", [])

def remove_existing_subparticle(content):
    return re.sub(r"^export const SubParticle = \{[^}]+\};\n\n?", "", content, flags=re.MULTILINE)

def populate_subparticles(root_dir="/project"):
    gitignore = load_gitignore(root_dir)
    root_path = Path(root_dir)
    modified_count = 0
    
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith((".jsx", ".js")):
                file_path = Path(root) / file
                rel_path = file_path.relative_to(root_path)
                
                if gitignore.match_file(rel_path):
                    print(f"Skipped (gitignore): {rel_path}")
                    continue
                
                try:
                    result = addSubParticle(str(rel_path))
                    if result["isError"]:
                        print(f"Failed {rel_path}: {result['error']}")
                        continue
                    
                    subparticle = result["content"][0]["text"]
                    with open(file_path, "r+") as f:
                        content = f.read()
                        content = remove_existing_subparticle(content)
                        f.seek(0)
                        f.write(f"{subparticle}\n{content}")
                        f.truncate()
                    
                    print(f"SubParticled: {rel_path}")
                    modified_count += 1
                except Exception as e:
                    print(f"Error {rel_path}: {e}")
    
    print(f"Total files modified: {modified_count}")

if __name__ == "__main__":
    populate_subparticles("/project")