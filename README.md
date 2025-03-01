# Practical Graph MCP Server

Practical Graph is a powerful Model Context Protocol (MCP) server that creates a living, intelligent graph representation of your codebase. It provides AI assistants with deep contextual understanding of your project structure, relationships, and architecture.

## What Can Practical Graph Do For You?

### 1. Codebase Understanding
- **Intelligent Code Navigation:** Creates a structured graph of your entire codebase with meaningful relationships between components
- **Contextual Awareness:** Enables AI assistants to understand how files relate to each other and your business domains
- **File Organization Insights:** Automatically classifies and categorizes your codebase structure

### 2. Relationship Mapping
- **Dependency Tracking:** Identifies which components use which services or libraries
- **Business Domain Mapping:** Links code to business concepts and documentation
- **Architecture Visualization:** Shows how your system is organized across feature areas

### 3. Seamless Integration
- **IDE Integration:** Works directly with your AI-enabled IDE
- **Real-time Updates:** Constantly monitors and updates as you modify your codebase
- **Export/Import Control:** Save and load graph snapshots whenever and wherever you want

## Getting Started

### 1. Installation
```bash
# Pull the Docker image
docker pull practical-graph-mcp

# Configure your MCP settings (see below)
```

### 2. Configuration
Add the Practical Graph server to your MCP configuration:

```json
"mcpServers": {
  "practical-graph": {
    "command": "docker",
    "args": [
      "run",
      "-v", "/path/to/your/project:/path/to/your/app",
      "-i",
      "practical-graph"
    ],
    "config": {
      "folder_groups": {
        "core": ["navigation", "state", "auth", "database"],
        "features": ["event", "discovery", "profile"],
        "api": ["endpoints"],
        "lib": ["utilities"]
      },
      "docs": {
        "business": "/docs/business-rules.md",
        "architecture": "/docs/architecture.md"
      },
      "watchdog": {
        "debounce_interval": 5,
        "batch_size": 10,
        "min_change_threshold": 3
      }
    }
  }
}
```

### 3. Customization Options

#### Folder Groups
Define how your code is organized by specifying folder groups:
```json
"folder_groups": {
  "core": ["navigation", "state", "auth", "database"],
  "features": ["event", "discovery", "profile"],
  "api": ["endpoints"],
  "lib": ["utilities"]
}
```

#### Documentation Links
Connect your codebase to formal documentation:
```json
"docs": {
  "business": "/docs/business-rules.md",
  "architecture": "/docs/architecture.md"
}
```

#### Watchdog Settings
Control how file changes are detected and processed:
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

1. **get_context()** - Retrieve the entire graph context of your application
2. **export_graph(target_path)** - Export the graph database to a location of your choice
3. **import_graph(source_path)** - Import a previously exported graph database
4. **get_graph_snapshot()** - Get a complete JSON representation of the current graph state

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

3. Export the graph for version control:
   ```
   Please export the graph to my project directory
   ```

## Benefits

- **Enhanced AI Understanding:** Your AI assistants gain deeper context about your specific codebase
- **Reduced Cognitive Overhead:** Less explaining your codebase structure to AI tools
- **Faster Onboarding:** New team members (human or AI) understand your project faster
- **Architectural Insights:** Discover unexpected dependencies and relationships

## Troubleshooting

If you encounter issues:

1. Check your MCP configuration settings
2. Verify the Docker container is running correctly
3. Ensure your volume mapping points to the correct project directory

## License

MIT License
