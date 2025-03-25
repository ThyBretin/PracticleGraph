The Lay of the Land

Here’s how I see the pieces fitting together based on what you’ve shared:
metadata_extractor.js:

What It Does: Parses JS/JSX files via Babel, extracts raw metadata—hooks (useRole), calls (StyleSheet.create), variables, props, logic (if conditions), dependencies (imports), comments, etc.

Hardcoding Alert: Lines 202-215 add “rich” extras (flows like “Onboarding: /(auth)/login → discovery”, business rules like “Capacity drives stage”). This biases it toward specific app logic (e.g., Stripe, Supabase), not generic use.

Output: A particle object with attributes (hooks, calls, etc.)—feeds into the graph.

dependency_tracker.py:
What It Does: Maps hooks to dependencies (e.g., useRole → components/Core/Role/hooks/useRole.js). Adds extras if expo-router is in the content.

Hardcoding Alert: Hook-to-file mappings are fixed (hook_deps dict). Misses dynamic imports or non-hook dependencies.

Output: A depends_on list—tacked onto the particle’s metadata.

particle_generator.py:
What It Does: Orchestrates metadata extraction for a file. Runs babel_parser_core.js for AST, then metadata_extractor.js, adds a file hash, caches the result, and summarizes it (e.g., “3 props, 2 hooks”).

Role: Middleman—takes a file path, produces a particle, no hardcoding here.

Output: A particle dict with attributes, file_hash, and a summary.

particle_support.py:
What It Does: Helpers for particle logic. extract_particle_logic() looks for export const Particle = {...} in files, falls back to inferring props/calls from code (e.g., fetch, supabase). infer_file_type() tags files (test, store, etc.).

Role: Backup metadata source if no explicit Particle export—keeps things flexible.

Output: A context dict (purpose, props, hooks, etc.)—merges into the particle.

project_definition.json:
What It Does: Your human-defined intent—concepts like Location with description, mappings (file, intent, props, logic).

Role: Meant to overlay meaning onto raw metadata (e.g., EventLocation.jsx → “Displays venue address”).

Issue: Not integrated into the graph yet.

ParticleThis() (The Goal):
Vision: Replace hardcoded bits with a dynamic, accurate system. Map hooks, functions, props, etc., explicitly, using project_definition.json and code signals, not fixed rules.

