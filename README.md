# Practical Graph MCP Server

Practical Graph is a powerful Model Context Protocol (MCP) server that creates a living, intelligent graph representation of your codebase. It provides AI assistants with deep contextual understanding of your project structure, relationships, and architecture.

## Quick Start

1. Add the Practical Graph server to your MCP configuration:

```json
"mcpServers": {
  "practical-graph": {
    "command": "docker",
    "args": [
      "run",
      "--env-file", ".env",
      "-v", "${PWD}:/app",
      "-i",
      "practical-graph"
    ],
    "config": "${PWD}/practical-graph.config.json"
  }
}
```

2. Create a `practical-graph.config.json` file in your repository:

```json
{
  "folder_groups": {
    "core": ["navigation", "state", "auth"],
    "features": ["event", "discovery", "profile"],
    "api": ["endpoints"],
    "lib": ["utilities"]
  },
  "docs": {
    "business": "docs/business-rules.md",
    "architecture": "docs/architecture.md"
  },
  "watchdog": {
    "debounce_interval": 5,
    "batch_size": 10,
    "min_change_threshold": 3
  }
}
```

he server will automatically:
- Use your repository's .gitignore patterns for file exclusions
- Monitor your repository for changes
- Create a graph representation of your codebase

## Features

### 1. Codebase Understanding
- **Intelligent Code Navigation:** Creates a structured graph of your entire codebase with meaningful relationships between components
- **Contextual Awareness:** Enables AI assistants to understand how files relate to each other and your business domains
- **File Organization Insights:** Automatically classifies and categorizes your codebase structure

### 2. Relationship Mapping
- **Dependency Tracking:** Identifies which components use which services or libraries
- **Business Domain Mapping:** Links code to business concepts and documentation
- **Architecture Visualization:** Shows how your system is organized across feature areas

## Configuration

### Folder Groups
Define how your code is organized:
```json
"folder_groups": {
  "core": ["navigation", "state", "auth"],
  "features": ["event", "discovery", "profile"],
  "api": ["endpoints"],
  "lib": ["utilities"]
}
```

### Documentation Links
Connect your codebase to documentation:
```json
"docs": {
  "business": "docs/business-rules.md",
  "architecture": "docs/architecture.md"
}
```

### Watchdog Settings
Control how file changes are detected:
```json
"watchdog": {
  "debounce_interval": 5,  // Seconds between processing batches
  "batch_size": 10,        // Maximum events per batch
  "min_change_threshold": 3 // Minimum events to trigger processing
}
```

## Using Practical Graph

### Available MCP Tools

The Practical Graph server provides these MCP tools:

1. **get_context(query)** - Retrieve the graph context of your application
   - Optional query parameter for filtering results
   - Examples: `"events.jsx"`, `"auth/*"`, `"features:profile"`

2. **export_graph(target_path)** - Export the graph database to a location of your choice

3. **import_graph(source_path)** - Import a previously exported graph database

4. **get_graph_snapshot()** - Get a complete JSON representation of the current graph state

5. **create_reference_doc(filename)** - Generate a markdown reference document of your codebase structure

### Query Syntax for get_context

The `get_context` tool supports powerful query filtering:

- **Simple filename search**: `"events.jsx"` - Find files by name
- **Path-based search**: `"src/components/Button.jsx"` - Find by path
- **Wildcard folder search**: `"auth/*"` - All files in a folder
- **Group search**: `"features:profile"` - Files in a specific group and folder
- **Wildcard group search**: `"core:auth:*"` - All files in a group and folder

### Example Workflow

In your AI assistant conversation:

1. Ask for project structure understanding:
   ```
   What is the architecture of my project?
   ```

2. Get insights about specific components:
   ```
   What components depend on the authentication service?
   ```

3. Generate reference documentation:
   ```
   Please create a reference document for my codebase
   ```

## Benefits

- **Enhanced AI Understanding:** Your AI assistants gain deeper context about your specific codebase
- **Reduced Cognitive Overhead:** Less explaining your codebase structure to AI tools
- **Faster Onboarding:** New team members (human or AI) understand your project faster
- **Architectural Insights:** Discover unexpected dependencies and relationships
- **Automatic Documentation:** Generate comprehensive reference documentation

## Troubleshooting

If you encounter issues:

1. Check your MCP configuration settings
2. Verify the Docker container is running correctly
3. Ensure your volume mapping points to the correct project directory
4. Check that your practical-graph.config.json file exists and is valid

## License

MIT License
