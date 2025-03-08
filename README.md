# Particule-Graph

A powerful MCP (Memory Context Provider) server that analyzes your codebase to create an intelligent context graph for AI assistants.

## Overview

Particule-Graph is a tool designed to enhance AI assistance by providing deep understanding of your codebase. It works by:

1. **Crawling** your project directories to map all files
2. **Analyzing** code patterns and identifying components
3. **Extracting** purpose, props, hooks, and API calls 
4. **Creating** a structured knowledge graph
5. **Supplying** this context to your AI assistant

This enables your AI assistant to understand your code's structure, connections, and functionality on a deeper level, producing more accurate and contextually relevant assistance.

## Features

- **SubParticule Comments**: Add detailed annotations to files for AI context
- **Feature Crawling**: Analyze entire folders to extract code structure
- **Tech Stack Detection**: Automatically identifies libraries and frameworks in use
- **Graph Export**: Save code graphs as JSON for later use
- **Graph Aggregation**: Combine multiple feature graphs for comprehensive context
- **Docker Support**: Easy deployment through containerization

## Getting Started

### Prerequisites

- Docker installed on your system
- A compatible IDE with MCP support

### Installation

1. Pull the Particule-Graph Docker image:
   ```bash
   docker pull particule-graph:latest
   ```

   Or build it locally from this repository:
   ```bash
   docker build -t particule-graph .
   ```

2. Run the container:
   ```bash
   docker run -v /path/to/your/project:/project -p 8000:8000 particule-graph
   ```

3. Configure your IDE's MCP settings to use particule-graph

## Usage

### Setting Up Your IDE

Configure your IDE to use Particule-Graph as an MCP provider:

1. Open your IDE settings
2. Navigate to AI Assistant configuration
3. Add MCP configuration for particule-graph
4. Point to the running Docker container (usually `http://localhost:8000`)

### Creating a Graph for a Feature

To create a graph for a specific feature or folder in your codebase:

1. Use the `createParticule` tool with the path to your feature
2. View the generated graph with `listGraph`
3. Export the graph using `exportGraph` if needed

### Adding SubParticules (Code Annotations)

Enhance your code with detailed context for AI:

1. Use `addSubParticule` on a file to generate context
2. Review and update the generated SubParticule if needed
3. This provides deeper insights for AI about component purpose, props, hooks, etc.

### Exporting and Sharing Graphs

To preserve and share your code graphs:

1. Use `exportGraph` to save a JSON representation
2. Graphs are timestamped for version tracking
3. Share these files with team members or use them as reference points

## MCP Tools Reference

The server provides these tools for interaction:

- `addSubParticule`: Generate context for individual files
- `createParticule`: Crawl and analyze a feature directory
- `updateParticule`: Update existing particule data
- `deleteParticule`: Remove particule data
- `listGraph`: List available graphs
- `loadGraph`: Load a specific graph into memory
- `exportGraph`: Export graphs to JSON files

## How It Works

Particule-Graph analyzes your code by:

1. Parsing files to identify components, functions, and structures
2. Extracting props, hooks, and API calls using pattern recognition
3. Identifying dependencies and connections between components
4. Building a graph representation of code relationships
5. Detecting the tech stack from imports and dependencies

This creates a comprehensive map of your codebase that AI tools can use to provide more accurate assistance.

## Benefits for AI Assistance

- **Deeper Code Understanding**: AI gains insight into component relationships and purpose
- **Tech Stack Awareness**: AI knows which libraries and frameworks you're using
- **Feature Context**: AI understands how code fits into larger project features
- **Enhanced Suggestions**: More relevant code completions and suggestions
- **Better Documentation**: AI can reference your code structure more accurately

## Docker Configuration

The included Dockerfile:
- Uses Python 3.10
- Installs required dependencies (fastmcp, lark)
- Exposes port 8000
- Runs the server.py script as the entry point

## Project Structure

- `server.py`: Main MCP server entry point
- `addSubParticule.py`: Core logic for code analysis and context extraction
- `createParticule.py`: Directory crawling and graph creation
- `loadGraph.py`: Graph loading and aggregation
- `exportGraph.py`: Graph export and serialization
- `tech_stack.py`: Technology detection and classification
- `particule_utils.py`: Shared utilities and helper functions

## Contributing

Contributions to improve Particule-Graph are welcome. Please feel free to submit issues or pull requests.

## License

[Add your preferred license information here]
