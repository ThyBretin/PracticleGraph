FROM python:3.10
RUN apt-get update && apt-get install -y nodejs npm
WORKDIR /app

# Create necessary directories
RUN mkdir -p src/api src/core src/graph src/helpers src/particle/js

# Copy server.py from root
COPY server.py ./

# Copy API files
COPY src/api/add_particle.py src/api/create_graph.py src/api/load_graph.py src/api/list_graph.py src/api/update_graph.py src/api/export_graph.py src/api/delete_graph.py src/api/

# Copy core files
COPY src/core/utils.py src/core/path_resolver.py src/core/cache_manager.py src/core/file_processor.py src/core/

# Copy particle files
COPY src/particle/particle_support.py src/particle/file_handler.py src/particle/dependency_tracker.py src/particle/particle_generator.py src/particle/

# Copy particle JS files
COPY src/particle/js/babel_parser.js src/particle/js/

# Copy graph files
COPY src/graph/tech_stack.py src/graph/aggregate_app_story.py src/graph/

# Copy helpers
COPY src/helpers/project_detector.py src/helpers/dir_scanner.py src/helpers/config_loader.py src/helpers/

# Add app directory to Python path
ENV PYTHONPATH=/app

RUN pip install fastmcp lark pathspec
RUN npm install @babel/parser
CMD ["python", "server.py"]