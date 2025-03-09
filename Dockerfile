FROM python:3.10
WORKDIR /app

# Install Node.js and Babel
RUN apt-get update && apt-get install -y nodejs npm
COPY babel_parser.js .
RUN npm install @babel/parser

# Install Python deps
COPY server.py particule_utils.py createParticule.py loadGraph.py listGraph.py updateParticule.py exportGraph.py deleteParticule.py addSubParticule.py list_dir.py check_root.py tech_stack.py prop_parser.py hook_analyzer.py call_detector.py logic_inferer.py dependency_tracker.py context_builder.py file_handler.py populate_and_graph.py populate.py ./
RUN pip install fastmcp lark pathspec

EXPOSE 8000
CMD ["python", "server.py"]