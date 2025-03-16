What We’ve Already Implemented
Here’s the foundation we’ve laid, distilled from our journey so far:
1. Enhanced extractMetadata (The Engine)
Purpose: Parses code (JS-focused but extensible) to extract essence.

Features:
Fields: path, type, purpose, depends_on, jsx, hooks, calls, logic, core_rules, props, routes, comments.

Logic Extraction: Grabs if conditions and actions (e.g., "maleMeetsMin && femaleMeetsMin" → "handles condition").

Dynamic Core Rules: Replaced hardcoded keywords (capacity, stage) with a scoring heuristic:
Impact (+3): Redirects, calls, state changes.

Complexity (+2): Logical ops (&&, ||).

Context (+2): Ties to imports.

Threshold: Score ≥ 5 → core_rules.

References: Line numbers for hooks, calls, logic (e.g., useRouter: {line: 21}).

Output: Feeds a 28K-token JSON for Today (154 files), capturing tech, routes, logic.

2. Particle Graph (The Map)
Purpose: Compresses codebase into a ~600-token, universal structure.

Structure:
Nodes: root, feature, file, rule, service (e.g., "eventState.js", "Supabase").

Edges: contains, implements, defines, interacts (e.g., "events → eventState.js").

Highlights:
Essence: core_rules like "Capacity Drives Stage".

Refs: Line numbers (e.g., eventState.js:120).

Tech: root lists stack (e.g., react-native 0.76.7).

Example: Today’s graph—9 nodes, 9 edges, ~600 tokens.

3. Key Achievements
Lean: 28K (full JSON) → ~600 (graph)—massive compression.

Universal: Dynamic core_rules and abstract nodes fit any language.

Actionable: Refs and rules guide devs/AI to the good stuff.

New Master Plan (ChatGPT’s Suggestions)
Here’s what we’re adding to make it a “100% app reveal,” per your last message:
1. Business Logic Overview
Goal: Explain why behind core_rules (e.g., event states, revenue, referrals).

Plan: Add a business_rules node with high-level descriptions inferred from core_rules and comments.

Today Example:
"maleMeetsMin && femaleMeetsMin" → "Gender-balanced capacity triggers stage shift".

Revenue split (inferred from payment logic, if present).

2. User Flow Documentation
Goal: Map user journeys (onboarding, booking, role-switching).

Plan: Add a flows section in root, stitching routes and calls into narratives.

Today Example:
"Onboarding": /(auth)/login → discovery.

"Booking": discovery → event/[id] → ticket.

3. API Endpoints
Goal: List key APIs (auth, events, payments, QR).

Plan: Add an endpoints field in service nodes, inferred from depends_on (e.g., supabase.from).

Today Example:
"GET /events": Fetch events.

"POST /events/update": Update state.

4. Environment Configuration
Goal: Document env vars (Supabase, Stripe, flags).

Plan: Add an env field in root, pulled from tech_stack and dotenv usage.

Today Example:
SUPABASE_URL: DB access.

STRIPE_KEY: Payments.

5. Permissions Matrix
Goal: Show role-based access (CRUD, navigation).

Plan: Add a permissions node, built from core_rules and role logic.

Today Example:
Attendee: events: read, tickets: create.

Organizer: events: CRUD.

