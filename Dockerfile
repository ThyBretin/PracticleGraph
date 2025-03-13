FROM python:3.10
RUN apt-get update && apt-get install -y nodejs npm
WORKDIR /app

# Create necessary directories
RUN mkdir -p src/api src/core src/analysis src/utils js

# Copy server.py from root
COPY server.py ./

# Copy API files
COPY src/api/add_particle.py src/api/create_graph.py src/api/load_graph.py src/api/list_graph.py src/api/update_graph.py src/api/export_graph.py src/api/delete_graph.py src/api/aggregate_app_story.py src/api/

# Copy core files
COPY src/core/particle_utils.py src/core/file_handler.py src/core/dependency_tracker.py src/core/utils.py src/core/file_utils.py src/core/particle_generator.py src/core/path_resolver.py src/core/

# Copy analysis files
COPY src/analysis/tech_stack.py src/analysis/

# Copy JS files
COPY js/babel_parser.js js/

# Copy utils
COPY src/utils/check_root.py src/utils/list_dir.py src/utils/config_loader.py src/utils/

# Add app directory to Python path
ENV PYTHONPATH=/app

RUN pip install fastmcp lark pathspec
RUN npm install @babel/parser
CMD ["python", "server.py"]