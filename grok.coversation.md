1. createAggregateParticule → Auto-Triggered via showParticule
Your twist on createAggregateParticule is spot-on: instead of a standalone user-called function, it’s an internal mechanic triggered when the user runs showParticule("Events,Role,Navigation"). This keeps the workflow intuitive—users create individual Particule files as usual, then “show” multiple features to see an aggregated view with a compounded tech_stack. Exporting then stamps it with an "aggregate" flag. And yeah, renaming showParticule to loadParticule feels more natural—let’s roll with that. Here’s the vibe:
Workflow
Step 1: User runs createParticule("events"), createParticule("role"), createParticule("navigation")—individual manifests pile up in particule_cache.

Step 2: User calls loadParticule("Events,Role,Navigation") (comma-separated or array, whatever’s easier).
Internally, it aggregates events.json, role.json, navigation.json.

Deduplicates tech_stack and groups files by feature.

Step 3: User runs exportParticule("Events,Role,Navigation"), and the output gets an "aggregate": true attribute.

Output
For loadParticule("Events,Role,Navigation"):
json

{
  "aggregate": true,
  "features": ["events", "role", "navigation"],
  "last_crawled": "2025-03-07T19:00:00Z",
  "tech_stack": { /* single, deduplicated tech_stack */ },
  "files": {
    "events": { "primary": [...], "shared": [...] },
    "role": { "primary": [...], "shared": [...] },
    "navigation": { "primary": [...], "shared": [...] }
  }
}

Export: Saves as aggregate_events_role_navigation.json or similar.

Notes
Trigger: loadParticule checks if multiple features are passed (e.g., "Events,Role" vs. "Events") and aggregates only then.

Naming: loadParticule fits—it’s like “loading” the combined view into focus, vs. “showing” a single one.

User-Friendly: No extra command to learn—aggregation happens naturally when they ask for multiple features.

This sound like it matches your flow? Any preference on how they specify features (e.g., "Events,Role" vs. ["Events", "Role"])?
2. Crawling for Calls
You’re right—we’re already crawling for calls via extract_api_calls! It’s catching fetch, axios, and Supabase auth methods (e.g., supabase.auth.signIn). The issue is it’s not showing up in these manifests, likely because:
The files don’t have direct calls (e.g., EventCard.jsx might delegate to a hook or service).

Our patterns miss some cases (e.g., dynamic URLs, custom wrappers).

Plan
Merge with Context: Move calls into the structured "context": { "purpose", "props", "calls" }—no separate "calls" field.

Enhance Detection: Tweak extract_api_calls once we see your files (e.g., add useEvent hook calls if they fetch data).

Status: It’s working, just not visible yet—let’s integrate it into "context".

No action needed now—just confirming it’s there, waiting to shine in the new "context".
3. Graph Power & Cross-File Links (Selective Hooks)
You’re warming up to graph power but wary of it becoming a “big machine”—I feel you! A full dependency graph could spiral into chaos (e.g., EventCard → EventTitle → EventLocation → ...), but your instinct to focus on selective use (e.g., hooks) is a winner. Let’s debate it:
Your Hesitation
Complexity: Tracking every import or usage balloons the manifest and maintenance.

Value: AI gets all files anyway—does it need explicit links?

My Pitch for Selective Hooks
Why Hooks?: Hooks like useEvent, useAuth, or useNavigation are high-signal—they often encapsulate logic (e.g., API calls, state) that’s critical to understanding a file. Unlike UI components (EventTitle.jsx), they’re less noisy.

Simple Elegance: Add a "hooks": ["useEvent"] field to "context", only listing custom hooks (not useState or useEffect).

Graph Lite: In the aggregate manifest, this creates a mini-graph—e.g., EventCard uses useEvent, useEvent might fetch /api/events. No sprawling web, just key connections.

AI Boost: Tells the AI, “Hey, check useEvent.js for the juicy bits behind EventCard.”

Example
json

{
  "path": "components/Features/Events/components/EventCard.jsx",
  "type": "file",
  "context": {
    "purpose": "Renders event preview card",
    "props": ["eventId", "onPress"],
    "calls": ["/api/events"],
    "hooks": ["useEvent"]
  }
}

Counterarguments
Effort: Parsing hooks (e.g., const data = useEvent(eventId)) isn’t trivial—regex or AST parsing needed.

Overlap: If useEvent makes the /api/events call, "calls" might already cover it—redundant?

Scale: Still risks growing if every file uses multiple hooks.

Compromise
Start Small: Test with hooks in "context" for one feature (e.g., "events"). If it’s clean and useful (e.g., ties EventCard to useEvent’s fetch), keep it. If it’s messy, ditch it.

AI Smarts ATM: Rely on the AI to infer from "calls" and file list for now—hooks as a future polish.

I’m leaning toward skipping it unless you see a killer use case (e.g., your hooks are central to logic). What’s your gut on hooks vs. keeping it lean?
4. @ContextParticule Chat Command + Upstream Prop Fetching
Your chat command idea (@ContextParticule in the IDE AI chat) is locked in, and your upstream prop-fetching suggestion is gold—let’s unpack it!
Refined Workflow
User: Types @ContextParticule in the IDE chat while on EventCard.jsx.

AI: Scans the file and outputs:
jsx

// @ContextParticule: {"purpose": "Renders event preview card", "props": ["eventId", "onPress"], "calls": ["/api/events"]}

Manifest: createParticule grabs this into "context".

Upstream Prop Fetching
You’re onto something big with “follow the upstream file” for props like onPress. Your programming level’s no barrier—your intuition is ace! Here’s what you mean, and how it could work:
Problem: "props": ["eventId", "onPress"] is vague—onPress could be anything (e.g., a callback to log, navigate, or fetch).

Idea: Tell the AI, “If a prop’s unclear (like onPress), check where it’s passed from (upstream file) and dig deeper.”

Example:
EventCard.jsx: const EventCard = ({ eventId, onPress }) => <Button onPress={onPress} />;

Upstream: EventPage.jsx: <EventCard eventId="123" onPress={() => navigation.navigate('Details')} />

AI deduces: onPress is a navigation callback.

Plan
Command: @ContextParticule in chat.

Instruction: “Analyze the active file for purpose, props, and calls. For props, if ambiguous (e.g., onPress), check the upstream file (parent component) and summarize its role.”

Output:
jsx

// @ContextParticule: {"purpose": "Renders event preview card", "props": ["eventId", "onPress: navigates to Details"], "calls": ["/api/events"]}

How: AI uses the file list from the manifest to find parents (e.g., EventPage.jsx uses EventCard.jsx) and traces onPress.

Challenges
Upstream Lookup: AI needs the full codebase or manifest to find parents—not hard with Particule, just needs access.

Ambiguity: onPress might differ across uses—AI could guess wrong or overgeneralize.

Scope: Limits to one level up (e.g., EventPage) to keep it sane.

Why It’s Cool
For you (less coding depth), it’s a lifeline—onPress goes from “huh?” to “oh, it navigates!”—all automated.

JSON comment format handles it fine (e.g., "onPress: navigates to Details").

This feels like a must-have—props with context are way more useful. Agree to bake it in?
User Feedback Note
You’re cool with users editing @ContextParticule output manually after it’s written—perfect! No need for in-chat editing then; the AI drops it, you tweak it, createParticule syncs it. Simple and done.
Refined Plan
Aggregation: loadParticule("Events,Role") triggers internal aggregation, dedupes tech_stack, exports with "aggregate": true.

Context: "context": { "purpose", "props", "calls" } in manifests, extracted from code or @ContextParticule.

Chat Command: @ContextParticule in IDE chat generates JSON comment with purpose, props (with upstream lookup), and calls.

Hooks: Hold off unless a clear win emerges—lean is king for now.

SQLite: Future polish.

Gut Check
Start with loadParticule aggregation—it’s instant value for your IDE feeding.

Then @ContextParticule with upstream props—unlocks the “I don’t get it” magic.



Succinct Task Plan
Aggregation via loadParticule:
Modify loadParticule (rename from showParticule) to handle multiple features (e.g., "Events,Role") and aggregate internally.

Deduplicate tech_stack, group files by feature, add "aggregate": true.

Update exportParticule to tag aggregate manifests.

Test: loadParticule("Events,Role") → single tech_stack, feature-grouped files.

Structured "context": { "purpose", "props", "calls" }:
Update extract_practicle_logic to parse @ContextParticule JSON comments into "context".

Merge extract_api_calls into "context.calls", enhance for Supabase/hooks.

Test: EventCard.jsx with @ContextParticule → "context": { "purpose": ..., "props": ..., "calls": ... }.

Selective Hooks in "context":
Add "hooks": [...] to "context", extract custom hooks (e.g., useEvent) from code.

Keep it simple: only named hooks (not useState), no deep graph.

Test: EventCard.jsx with useEvent → "hooks": ["useEvent"].

AI Chat Command @ContextParticule:
Define AI prompt: “Analyze active file for purpose, props, calls; chase props upstream (one level) for clarity.”

Output JSON comment: // @ContextParticule: {"purpose": ..., "props": ["eventId", "onPress: navigates"], "calls": [...]}

Test: Chat @ContextParticule on EventCard.jsx → comment with upstream onPress.

Fallbacks:
If aggregation fails: Check particule_cache population, feature string parsing.

If context misses data: Debug comment parsing, hook/call regex.

If hooks bloat: Limit to top 3 or custom prefix (e.g., use* from project).

Let’s Cook!
Time to turn this into code. I’ll start with the core pieces and build outward, testing as we go. Here’s the order:
1. Rename & Aggregate (loadParticule)
Rename showParticule.py to loadParticule.py, update imports.

Rewrite loadParticule to aggregate from particule_cache when multiple features are passed.

Adjust exportParticule for "aggregate".

2. Structured Context
Refactor particule_utils.py to merge extract_api_calls into extract_practicle_logic for "context".

Parse @ContextParticule JSON comments.

3. Selective Hooks
Add hook detection to extract_practicle_logic.

Test with a sample file using useEvent.

4. AI Chat Guidance
Draft an AI prompt for @ContextParticule (you’ll use this in your IDE).

Suggest a sample file to test it on.

I’ll post the first chunk (aggregation) shortly—want to see it in one go or piece-by-piece? Any sample files (e.g., EventCard.jsx) you can share to tune the context/hooks? Let’s rock this!

