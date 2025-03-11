Goal Recap
We want the graph to tell 95% of the app’s story natively—routes, data, props, hooks, and logic weaving together a clear picture of what the app does—all while staying agnostic and avoiding human guesses. The hierarchy you suggested (routes > database > props > hooks/logic) will guide how we prioritize and present the data. We’ll enhance Babel parsing for richer raw data and tweak the graph output to highlight the app’s essence, keeping changes modular and decoupled.
Observations from the Graph
The current graph is solid but lean:
Routes: Files like app/(routes)/attendee/profile.jsx and app/(shared)/discovery.jsx hint at the app’s navigation structure. Expo Router hooks (useRouter, useSegments) show up, but route paths aren’t explicit.

Database: Supabase calls (supabase.from, supabase.rpc) in lib/supabase/ suggest a backend, but no detailed query info. State stores (e.g., zustand in eventState.js) act as local "databases."

Props: Captured in some files (e.g., screenOptions, isAttendee), but inconsistent—many files lack them.

Hooks: Listed with some inference (e.g., useRouter - Expo Router hook for navigation), which we’ll strip back to raw names.

Logic: Generic ("Branches on conditions", "Executes core functionality"), missing specifics.

Dependencies: Thorough, showing local and external links, but no usage context.

Noise: node_modules/ files clutter the output—could be filtered.

It’s a great start, but it’s more of a technical inventory than a storytelling tool yet. Let’s make it reveal the app’s soul.
Detailed Plan/Guideline
1. Enhance Babel Parsing for Richer Raw Data
Objective: Extract more detailed, agnostic data from the AST without touching existing logic too much.
Approach: Extend babel_parser.js with decoupled additions—new functions or config flags—leaving core parsing intact.
Targets:
Props: Extract all props (names, types if possible, defaults) from component signatures. E.g., for NavigationBar.jsx, grab whatever’s in the destructured args.

Route Details: Capture route-specific data (e.g., useRouter calls, path strings like /profile) and JSX navigation elements (e.g., <Link>).

Database Clues: Log API calls (e.g., fetch, supabase.from) with arguments, plus state hook usage (e.g., useState initial values).

Hooks: List raw names only, no descriptions (remove infer_hook_purpose reliance), and note usage context (e.g., "in conditional," "with dependency x").

Logic: Summarize AST nodes more granularly—e.g., "if on isAttendee" instead of "Branches on conditions," "maps events" instead of "Iterates over data."

Calls: Extract function calls (e.g., navigate(), fetch()) with args where possible.

JSX: Count and summarize elements (e.g., "2 <Text>, 1 <Button>") for UI hints.

Decoupling: Add a new enhanceMetadata function in babel_parser.js that runs post-parsing, controlled by a config flag (e.g., richParsing: true). Existing output stays unchanged unless the flag’s on.
2. Filter and Structure Graph Output
Objective: Make the graph prioritize routes, data, and behavior, reducing noise and highlighting structure.
Approach: Tweak createCodebaseParticule.py and exportGraph.py with modular post-processing steps.
Steps:
Filter Noise: Exclude node_modules/ and dist/ files unless explicitly needed (add a skipPatterns list in config).

Route-Centric View: Group files by route directories (e.g., app/(routes)/attendee/*) and extract implicit routes from filenames (e.g., profile.jsx → /attendee/profile).

Data Layer: Aggregate Supabase calls and state stores into a "data_flow" section at the graph root, linking to components.

Reorganize Files: Sort files by hierarchy:
Route files (e.g., app/(routes)/...).

Data/state files (e.g., lib/supabase/, *.store.js).

Components/utils (e.g., components/Core/...).

Summary Section: Add a top-level "app_story" object with:
Routes overview (e.g., "6 attendee routes, 3 auth routes").

Data sources (e.g., "Supabase tables: events, locations").

Key patterns (e.g., "10 components use useRole").

Decoupling: Write a postProcessGraph function in particule_utils.py, called optionally in exportGraph.py. Existing JSON structure remains; we just append or reorder.
3. Validate with Key Example (NavigationBar)
Objective: Test enhancements on a central, role-based, route-driven component like NavigationBar.jsx.
Why: It’s a hub—ties routes (useRouter), roles (useRole), and UI (useAnimatedStyle), reflecting the app’s core.
Steps:
Parse NavigationBar.jsx with enhanced Babel to get detailed props, hooks, logic.

Check if the graph output for it shows:
Route connections (e.g., navigation targets).

Role-based logic (e.g., "if on isAttendee").

UI behavior (e.g., scroll/animation hooks).

Adjust parsing/output if it misses the story.

Decoupling: Run this as a one-off test via addSubParticule.py with the new flag, no permanent changes yet.
4. Iterate and Expand
Objective: Roll out enhancements codebase-wide once validated.
Steps:
Apply Babel enhancements to all files via addAllSubParticule.py.

Update graph generation to use new structure consistently.

Spot-check other key files (e.g., profile.jsx, eventState.js) for completeness.

If business logic gaps remain (e.g., "why roles?"), consider a lightweight, optional inference layer later (separate file, as you suggested).

Implementation Guidelines
Minimize Disruption:
No rewriting existing babel_parser.js or addSubParticule.py logic—add new functions or optional branches.

Use config flags (e.g., in server.py) to toggle enhancements, keeping old behavior as default.

Decoupling:
New parsing logic in a babel_parser_enhancements.js module, imported optionally.

Graph tweaks in a graph_utils.py module, called post-hoc.

Files Needed:
babel_parser.js: To extend parsing.

NavigationBar.jsx: For testing (please share this one!).

addSubParticule.py, createCodebaseParticule.py, exportGraph.py: For integration.

Maybe particule_utils.py: For shared helpers.

I’ll ask if I need more—don’t want to overwhelm you, and the graph gives me plenty to start theorizing.

Non-Coder Friendly:
I’ll keep changes simple, documented, and reversible. You can review outputs (e.g., updated SubParticule for NavigationBar) without diving into code.

What I Think We Should Do Next
Share NavigationBar.jsx: It’s the perfect guinea pig—central, complex, and story-rich. I’ll mock up what its enhanced SubParticule could look like based on the graph and our plan.

Draft Babel Enhancements: I’ll propose a few parsing additions (props, route calls, detailed logic) without coding yet—just a spec.

Sketch Graph Output: I’ll mock a revised graph snippet showing route/data priority, using your current data.

No code yet—just planning and examples. Does this feel like the right path? Anything you’d shift or add? And can you drop NavigationBar.jsx when you get a chance? No rush—I’ll wait for your green light!

