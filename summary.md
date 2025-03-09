# Particule Graph Project Summary

## Core Features

### Tech Stack Analysis
- Simplified package.json-based analysis

### File Structure
- Component-based organization
- Feature-based manifests
- Aggregate manifests for multi-feature context

### Key Components

1. **addSubParticule**
   - Generates context for individual files
   - Extracts props, hooks, and API calls, purpose, key logic and depends on:
   - Analyzes file relationships

1. **createParticule**
   - Creates individual graph for a feature
   - Analyzes tech stack
   - Maps file relationships

2 - listGraph   
 - Lists available graphs

3 - loadGraph**
   - Loads and processes manifests
   - Handles feature aggregation
   - Manages tech stack deduplication

## Future Enhancements

1. **SQLite Integration**
   - Persistent storage
   - Improved context management
   - Cross-session data retention

2. **IDE Integration**
   - Direct VS Code extension support 
   - addSubParticule and createParticule could take ide path as input to localize the file and folder so path are streamlined by IDE. 
   - Improved developer experience
   - Seamless AI interaction

## Technical Implementation
- Docker-based deployment
- Python backend
- Modular architecture
- JSON-based manifest format
