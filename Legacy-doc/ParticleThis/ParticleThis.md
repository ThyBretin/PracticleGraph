The AI that graphs your project’s soul.”



Particle-Graph: AI-Powered Project Clarity
The Pitch
Imagine this: You type ParticleThis('Location,Auth') into your IDE. An AI chats with you, maps your intent to your code, and builds a graph that nails your project’s story—95% of the narrative, straight from the source. No more vague docs, endless meetings, or misaligned builds. Particle-Graph turns code into a living, trustworthy blueprint for devs, PMs, and teams. It’s easy, enjoyable, and reliable—ready to rock in-house or hit the market.
The Problem
Docs Drift: Requirements get lost, skewed, or ignored—PMs (like you) repeat themselves, devs guess, chaos creeps in.

Code Blindness: Newbies drown, legacy code confuses, intent hides in raw files.

Tools Miss Intent: Static analyzers spot bugs, not why the code exists. AI copilots fix, not explain.

Teams waste time bridging the gap between vision and execution. Clarity shouldn’t be this hard.
The Solution: Particle-Graph
Particle-Graph is an AI-driven system that graphs your project’s soul:
Extracts Everything: Scans JS/JSX (more soon) for hooks, routes, logic, dependencies—95% of the narrative, no fluff.

ParticleThis Magic: Chat with AI—ParticleThis('Location')—to refine intent (“It’s venue addresses!”). It maps your words to functions, saves it in project_definition.json.

Living Graphs: Nodes (files), edges (relationships), flows (“Location Setup: setLocation → venue address”), rules (“Venue-linked? Use venueAddress”). Always fresh via hash-based caching.

Docker-Ready: Runs anywhere—local or containerized—with smart path resolution.

Result: A graph you trust—your vision, tied to code, no drift.
How It Works
Step 1: Point it at your code (createGraph('/src')). It auto-scans, caches particles (metadata), and builds graphs.

Step 2: Run ParticleThis('Location,Auth'). AI crawls, chats (“setLocation sets venue stuff?”), you refine, it saves intent.

Step 3: Export or explore—JSON, visuals, stats. See your app’s story in 5 minutes.

Tech: Babel parses JS, Python orchestrates, AI (like me!) bridges human and code. Docker keeps it portable.

Example: 
Code: if (event.organiser === 'Venue') { setLocation(event.venueAddress); }

Chat: “Is this venue addressing?” → “Yes, for events.”

Graph: Flow: “Location Setup: setLocation → venue address.” Rule: “Venue Address: Uses venueAddress when Venue.”

Why It’s Killer
For PMs: Define “Location” once—graph enforces it. No more re-explaining.

For Devs: Onboard fast—see why code exists, not just what.

For Teams: Sync intent and execution—less talk, more build.

Market Edge: Easy (chat-driven), enjoyable (AI co-creation), reliable (code-tied). Docs can’t compete; static tools don’t dream this big.

Market Play
Who: Non-dev PMs, small dev teams, enterprises, educators—anyone craving clarity.

How: VS Code plugin, freemium ($10/mo for multi-concept, teams), demos that dazzle.

Why Now: AI’s ripe, teams are stretched, first-mover window’s open.

Pitch: “Graph your project’s soul in 5 minutes—code meets intent, powered by AI.”

