# Particule-Graph Project Summary

## Intent
Particule-Graph is a tool to analyze and document React Native/Expo codebases by generating `SubParticule` objects—metadata summaries of components. It aims to:
- Extract props, hooks, API calls, key logic, and dependencies from individual files.
- Export this metadata as `export const SubParticule = {...}` directly into source files.
- Aggregate graphs for directories/features to map tech stacks and relationships.
- Reflect the codebase accurately for maintenance, debugging, and onboarding.

## Core Functionality
- **`addSubParticule(file_path, rich=True)`**: Analyzes a file, generates a `SubParticule`, and writes it back to the file.
- **Output Format**: JSON-like object with `purpose`, `props`, `hooks`, `calls`, `key_logic`, `depends_on`.
- **Tools**: Runs in a Dockerized MCP server, callable via IDE or CLI.

## Files
- **`addSubParticule.py`**: Orchestrates analysis and export.
- **`file_handler.py`**: Reads/writes files, handles paths (`/project` root in Docker).
- **`prop_parser.py`**: Extracts props (currently regex + hook inference; moving to Tree-sitter).
- **`hook_analyzer.py`**: Identifies hooks and infers their purpose.
- **`call_detector.py`**: Detects API calls (e.g., `fetch`, `supabase`).
- **`logic_inferer.py`**: Infers key logic (e.g., conditions, state transitions).
- **`dependency_tracker.py`**: Maps dependencies from hooks/content.
- **`context_builder.py`**: Assembles the final `SubParticule` with `purpose`.
- **`particule_utils.py`**: Logger and `app_path` (`/project`).
- **`server.py`**: MCP server (assumed—runs the tool).
- **Docker**: `Dockerfile` builds `particule-graph` image, mounts `/Users/Thy/Practicle-Graph:/project`.

## Constraints
- **Path Handling**: Must support absolute (IDE) and relative (CLI) paths, mapped to `/project` in Docker.
- **Prop Detection**: Must handle stateless components, hook-derived props, and complex JSX (e.g., `NavigationBar.jsx`).
- **Scalability**: Should work for single files and directory aggregates (`exportGraph`).
- **Accuracy**: No hardcoding—generic parsing for all React/TS/JSX patterns.
- **IDE Integration**: AI picks active file for `addSubParticule`—path resolution must align.

## Current State (March 08, 2025)
- **Working**: `addSubParticule` generates/writes `SubParticule` for files like `EventFeed.jsx` and `NavigationBar.jsx`.
- **Props Issue**: Regex struggles with `NavigationBar.jsx` (misses `onPress`, was `name: boolean`).
- **Next**: Switching to Tree-sitter for robust parsing, keeping Lark/regex as fallbacks.
- **To Fix**:
  - `exportGraph`: Ensure aggregation works for folders.
  - Pathfinding: Verify IDE/CLI consistency.

## Setup
- **Docker**: `docker build -t particule-graph . && docker run -v /Users/Thy/Practicle-Graph:/project -p 8000:8000 particule-graph`
- **Test**: `docker exec -it <container_id> python -c "from addSubParticule import addSubParticule; print(addSubParticule('path/to/file'))"`

## Vision
A self-documenting codebase where each file has a `SubParticule`, and aggregates reveal the full graph—maybe even a `SubParticule` for Particule-Graph itself!


---------

Prop Parsing with Tree-sitter:
Since you’re switching to Tree-sitter, prioritize defining queries for common React patterns (e.g., functional components, arrow functions, prop destructuring). For NavigationBar.jsx, ensure it catches dynamic props like onPress={() => ...} by traversing the AST for function expressions. You could keep regex as a lightweight fallback for simple cases.

Hook Inference:
For hook_analyzer.py, beyond identifying hooks (useState, useEffect, etc.), you could infer their roles by analyzing dependencies and return values. For example:
useEffect with no dependencies = initialization logic.

useState tied to a prop = controlled component state.

Logic Inference:
logic_inferer.py could use heuristics like "if a condition changes a state variable, it’s a state transition" or "if a loop processes an array prop, it’s a renderer." This could make key_logic more actionable for developers.

Dependency Tracking:
For depends_on, consider not just imports but also runtime dependencies (e.g., context providers, global stores like Redux). This might require integrating with React’s component tree analysis—maybe a stretch goal?

IDE Integration:
Since you mention AI picking the active file, ensure your path resolution handles editor-specific quirks (e.g., VS Code’s workspace paths vs. IntelliJ’s project roots). A VS Code extension calling your Dockerized tool via CLI could be a killer feature.

Testing and Validation:
Your test command (docker exec ...) is a good start. Add unit tests for edge cases—stateless components, inline hooks, or files with no exports—to ensure addSubParticule doesn’t break.

Future Vision:
The aggregated graphs could feed into a visualization tool (e.g., D3.js or Graphviz) to show component relationships. Imagine a clickable graph where devs jump to a file from its node—that’d be a game-changer for onboarding!


Old : 
// export const SubParticule = {
//   "purpose": "Renders event progress with male/female status",
//   "props": ["type: string", "current: number", "min: number", "max: number", "color = \"styles.colors.darkBlue\": string", "direction = 'left': string"],
//   "hooks": ["useEventDisplayState - Fetches event display data"]
// };


New :
export const SubParticule = {
  "purpose": "Renders eventstatus UI",
  "props": ["type", "state: array | object", "current", "iconStyle: function"],
  "hooks": ["useEventDisplayState - Fetches event display data"],
  "key_logic": ["Constrained by conditions"],
  "depends_on": ["components/Core/Middleware/state/eventDisplayState.js"]
};


export const SubParticule = {
  "purpose": "Renders role-based navigationbar UI",
  "props": ["onPress: function", "accessibilityRole", "accessibilityLabel", "accessibilityState", "scrollY", "previousScrollY", "isScrollingUp", "currentTab", "isAttendee", "tabs: array"],
  "hooks": ["useRouter - Expo Router hook for navigation", "useRole - Manages authentication state", "useNavigation - Controls navigation", "useSegments - Expo Router hook for route segments", "useScrollValue - Manages scroll state", "useDerivedValue - Computes derived values", "useEffect - Handles side effects on mount/update", "useAnimatedStyle - Manages animated styles"],
  "key_logic": ["Defines values: Role-based rendering options", "Constrained by conditions"],
  "depends_on": ["expo-router", "components/Core/Role/hooks/useRole.js", "components/Core/Navigation/hooks/useNavigation.js"]
};

export const SubParticule = {
  "purpose": "Renders role-based navigationbar UI",
  "props": ["onPress: function", "accessibilityRole", "accessibilityLabel", "accessibilityState", "scrollY", "previousScrollY", "isScrollingUp", "currentTab", "isAttendee", "tabs: array"],
  "hooks": ["useRouter - Expo Router hook for navigation", "useRole - Manages authentication state", "useNavigation - Controls navigation", "useSegments - Expo Router hook for route segments", "useScrollValue - Manages scroll state", "useDerivedValue - Computes derived values", "useEffect - Handles side effects on mount/update", "useAnimatedStyle - Manages animated styles"],
  "key_logic": ["Defines values: Role-based rendering options", "Constrained by conditions"],
  "depends_on": ["expo-router", "components/Core/Role/hooks/useRole.js", "components/Core/Navigation/hooks/useNavigation.js"]
};