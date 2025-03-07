Practicle
Goal

Particule is an mcp server that let you aggregate a context file for each feature of your codebase. The Particule created by the mcp let your AI assistant have a context of the feature you are working on. 
The Partciule file is a json file that contains the context of the feature you are working on : Tech Stack, API calls, file structure, and business logic. 


Business logic is tied to each file and extracted from the file content by a simple export: export const Particule = "..."
File structure is extracted from the file path.
API calls are extracted from the file content.
Tech stack is extracted from the package.json.


If you need a new Particule, you can use the createParticule("components/Core/Navigation") tool.

This will create a new Particule file for the Navigation feature that the AI can use to have a context of the feature you are working on.
You can export the Particule file with the exportParticule("Navigation") tool.
You can show the Particule file with the showParticule("Navigation") tool.
You can update the Particule file with the updateParticule("Navigation") tool.
You can delete the Particule file with the deleteParticule("Navigation") tool.
You can list all Particule files with the listParticule() tool.






Build a suite of MCP tools (Practicle) to crawl, manage, and serve manifests for codebases's features—capturing file structure, context (Practicle exports), API calls, and tech stack—stored in memory, exportable on demand.

Tools & Workflow
createPracticle(feature_path: str, save: bool = False)
What: Crawls a feature directory (e.g., components/Features/Events), builds a manifest.

Inputs: Path relative to /project (e.g., components/Features/Events).

Actions:
[x] Recursively crawls, respects .gitignore.
[x] Extracts export const Practicle = "..." → "context".
[ ] Scans fetch, axios → "calls".
[x] Scans imports → "tech" (e.g., react, expo-*).
[x] Adds last_crawled timestamp.
[x] Stores in practicle_cache (in-memory dict).
[x] If save=True, writes <feature>_practicle.json (e.g., events_practicle.json).

showPracticle(feature: str)
[x] What: Fetches the latest manifest from cache—e.g., showPracticle:Events.
Inputs: Feature name (e.g., Events).
Actions: Returns practicle_cache[feature]; recrawls via createPracticle if missing.
Output: Manifest JSON.

listPracticle()
[x] What: Lists all cached manifests—e.g., { "Events": "2025-03-05T08:00:00Z", ... }.
Actions: Scans practicle_cache, returns feature names and timestamps.
Output: JSON list/dict of cached manifests.

[x]updatePracticle(feature: str)
What: Recrawls and updates a manifest—e.g., updatePracticle("Events").
Actions: Runs createPracticle(f"components/Features/{feature}"), updates cache.
Output: Updated manifest JSON.

exportPracticle(feature: str)
[x] What: Saves a manifest to disk—e.g., exportPracticle("Events") → events_practicle.json.
Actions: Writes practicle_cache[feature] to file.
Output: Confirmation message (e.g., "Saved events_practicle.json").

deletePracticle(feature: str)
[x] What: Removes a manifest from cache—e.g., deletePracticle("Events").
Actions: Deletes practicle_cache[feature].
Output: Confirmation message (e.g., "Deleted Events").

get_tech_stack(entities: list) -> dict
[x] What: Extracts a categorized tech stack with versions from package.json and file hints—e.g., Expo SDK, Core Libraries, State Management.
Inputs: List of file entities (e.g., [{"path": "components/Core/Role/guards/RoleGuard.jsx", "type": "file"}, ...]).
Actions: Loads dependencies from package.json, categorizes them using TECH_CATEGORIES config, infers additional tech from file extensions (e.g., .jsx -> React), and builds a structured tech stack dict.
Output: Categorized tech stack JSON (e.g., {"expo_sdk": "~52.0.36", "core_libraries": {"react": "18.3.1"}, ...}).


Manifest Structure
json

{
  "feature": "Events",
  "last_crawled": "2025-03-05T08:00:00Z",
  "files": [
    {
      "path": "components/Features/Events/components/EventCard.jsx",
      "type": "file",
      "context": "Renders event preview with title, date, and RSVP button",
      "tech": ["react", "expo-router"]
    },
    {
      "path": "components/Features/Events/api/eventService.js",
      "type": "file",
      "calls": ["/api/events"],
      "tech": ["axios"]
    },
    ...
  ]
}

[x] Rules: Omit "context", "calls", "tech" if empty/null—keeps it clean.

Storage
[x] practicle_cache: In-memory dict—e.g., {"Events": {...}, "Chat": {...}}.
[x] Backup: Via exportPracticle—users save JSON files manually.

[x] Future: SQLite if persistence needed (e.g., practicle.db).

Existing Tools
[x] list_dir(path: str): Debugging—lists dirs/files (e.g., list_dir("components/Features")).

[x] check_root(): Sanity check—verifies /project contents.
[ ] techStack(): Returns tech stack from package.json.

