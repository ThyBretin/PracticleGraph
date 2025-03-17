Plan to Implement ParticleThis
Objective
Enable ParticleThis('Concept') (e.g., ParticleThis('Location') or ParticleThis('Location,Auth')) to:
Crawl code using existing Particle-Graph machinery.

Engage the user via chat (IDE or CLI) to refine intent.

Map that intent to functions and save it in project_definition.json.

Enhance future graphs with this user-defined narrative.

Scope
Leverage src/particle/metadata_extractor.js and src/api/create_graph.py as the base.

Integrate with an AI (like me via xAI API) for chat and mapping.

Keep it JS/JSX-focused for now, expandable later.

Implementation Plan
Phase 1: Foundation (1-2 Days)
Goal: Hook ParticleThis into the existing system, crawl code, and prep for chat.
Extend API Layer:
File: src/api/particle_this.py (new)

Function: particleThis(concepts: str)
Input: Comma-separated concepts (e.g., “Location,Auth”).

Action: 
Split concepts into a list.

Trigger a crawl using file_processor.process_directory() on the project root (resolved via path_resolver).

Pass results to a chat handler (TBD).

Output: Temp JSON with raw function data (e.g., { "file": "EventForm.js", "functions": ["useState", "setLocation"] }).

Reuse Crawler:
File: src/particle/particle_generator.py

Function: generate_particle(file_path: str, rich: bool=True)
Already extracts hooks, calls, logic, etc., via metadata_extractor.js.

Add a filter: Flag functions/variables matching concepts (e.g., “location” in setLocation or args).

Store in-memory (via cache_manager) for chat step.

Setup Chat Stub:
File: src/core/chat_handler.py (new)

Function: initiate_chat(concepts: List[str], particle_data: Dict)
Placeholder: Log “Starting chat for {concepts} with {particle_data}”.

Next phase connects to AI.

Deliverable: particleThis('Location') runs, crawls, logs raw function matches.
Phase 2: AI Chat Integration (2-3 Days)
Goal: Wire up AI (me!) to chat, refine intent, and draft mappings.
Connect to xAI API:
File: src/core/chat_handler.py

Function: chat_with_ai(concepts: List[str], particle_data: Dict)
Send particle data (e.g., { "EventForm.js": { "setLocation": [4, 6, 8], "useState": [2] } }) to xAI API.

Prompt: “Crawl this: {particle_data}. Propose intent for {concepts}. Ask user if it matches.”

Example response: “setLocation sets something based on event.organiser. Is this about venue addresses?”

Interactive Loop:
CLI Version (quick start):
Print AI response, wait for user input (e.g., “Yes” or “No, it’s venue addresses”).

Send back to API: “User says: {input}. Refine and ask again.”

Loop until user says “Perfect.”

IDE Later: Swap CLI for IDE chat box (e.g., VS Code API)—same logic, fancier UI.

Draft Mapping:
AI Output: Once agreed, return structured intent:
json

{
  "Location": {
    "description": "Sets venue addresses for events",
    "mappings": [
      { "function": "setLocation", "file": "EventForm.js", "lines": [4, 6, 8], "intent": "Sets venue address" }
    ],
    "flows": ["Location Setup: `setLocation` updates venue address"],
    "rules": ["Venue Address: Sets venueAddress when Venue-linked"]
  }
}

Handler: Save temp to cache_manager for next step.

Deliverable: particleThis('Location') chats via CLI, refines intent with AI, outputs draft mapping.
Phase 3: Save and Integrate (1-2 Days)
Goal: Finalize project_definition.json and hook into graph generation.
Save to project_definition.json:
File: src/core/file_processor.py

Function: save_project_definition(data: Dict)
Path: Resolve via path_resolver.get_graph_path('project_definition') (e.g., /cache/project_definition.json).

Merge new concepts with existing (if any), write via write_json_file().

Enhance Graph Creation:
File: src/api/create_graph.py

Function: createGraph(path: str)
Before returning, load project_definition.json via path_resolver.read_json_file().

Inject into graph:
Nodes: Add intent to particle attributes (e.g., "intent": "Sets venue address").

Edges: Link based on flows/rules (e.g., setLocation → event.venueAddress).

Use graph_support.postProcessGraph() to weave in flows/rules.

Test Output:
Run createGraph('/src') → Graph includes: 
Flow: “Location Setup: setLocation updates venue address.”

Rule: “Venue Address: Sets venueAddress when Venue-linked.”

Deliverable: ParticleThis saves to project_definition.json, graphs reflect user intent.
Phase 4: Polish and Multi-Concept (2-3 Days)
Goal: Support ParticleThis('Location,Auth'), refine UX.
Multi-Concept:
File: src/api/particle_this.py

Update: particleThis(concepts: str)
Loop over concepts (e.g., ['Location', 'Auth']).

Crawl once, chat per concept: “Now Auth—signIn looks like login. Right?”

Save all in one project_definition.json.

UX:
CLI: Clear prompts (e.g., “Concept 1/2: Location—agree? [y/n/r]” where r=refine).

IDE Prep: Stub for VS Code (e.g., log to chat panel—full UI later).

Error Handling: “No matches for ‘Auth’—try again?”

Docs:
Update doc/ with ParticleThis guide: “Run particleThis('Concept') to define intent…”

Deliverable: ParticleThis('Location,Auth') works end-to-end, polished CLI experience.
Timeline & Resources
Total: 6-10 days (1-2 weeks).

Team: 
1 Dev: Python/JS skills, knows Particle-Graph.

Me (AI): Chat logic, mapping via xAI API (assumes access).

Tools: Existing codebase, xAI API key, CLI for now (IDE later).

Prototype (Day 1 Test)
Hack particle_this.py: Crawl with generate_particle, print functions, fake chat (“Is this it?”), save dummy JSON.

Test: particleThis('Location') on EventForm.js.

