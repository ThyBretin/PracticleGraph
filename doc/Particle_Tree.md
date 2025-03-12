Particle-Graph/
├── server.py                      # Main MCP server
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Docker build (root-level convention)
├── README.md                     # Project overview
├── src/                          # Source code
│   ├── api/                      # API endpoints
│   │   ├── add_particle.py       # addParticle(path, recursive)
│   │   ├── create_graph.py       # createGraph(path)
│   │   ├── delete_graph.py       # deleteGraph(path)
│   │   ├── export_graph.py       # exportGraph(path)
│   │   ├── list_graph.py         # listGraph()
│   │   ├── load_graph.py         # loadGraph(path)
│   │   └── update_graph.py       # updateGraph(path)
│   ├── core/                     # Core functionality
│   │   ├── dependency.py         # Dependency tracking (renamed)
│   │   ├── file_handler.py       # File I/O
│   │   └── particle_utils.py     # Shared utils
│   ├── analysis/                 # Analysis tools
│   │   └── tech_stack.py         # Tech stack analysis
│   └── utils/                    # Utilities
│       └── config_loader.py      # Config loading (if used)
├── legacy/                       # Pre-refactoring files
│   ├── addParticle.py
│   ├── addAllParticle.py
│   ├── createParticle.py
│   ├── createCodebaseParticle.py
│   ├── exportGraph.py
│   ├── exportCodebaseGraph.py
│   ├── loadGraph.py
│   ├── loadCodebaseGraph.py
│   ├── deleteParticle.py
│   ├── updateParticle.py
│   └── ...                      # Any other oldies
├── js/                           # JS utilities
│   └── babel_parser.js           # Babel AST parsing
├── dev/                          # Development tools
│   ├── debug_graph.py            # Debugging
│   └── docker-compose.yml        # Optional multi-container setup
└── doc/                          # Documentation
    ├── Particle.md               # Particle format
    ├── Project-Refactoring.md    # Refactoring notes
    └── README.md                 # Optional duplicate or symlink