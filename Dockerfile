FROM python:3.10

WORKDIR /app

# Copy project files
COPY server.py particule_utils.py createParticule.py loadGraph.py listGraph.py updateParticule.py exportGraph.py deleteParticule.py addSubParticule.py list_dir.py check_root.py tech_stack.py prop_parser.py hook_analyzer.py call_detector.py logic_inferer.py dependency_tracker.py context_builder.py file_handler.py populate.py ./

# Copy pre-built parser
COPY tree-sitter-libs/javascript.so /app/tree-sitter-libs/javascript.so

# Install Python deps
RUN pip install fastmcp lark tree-sitter==0.20.1 pathspec

EXPOSE 8000
CMD ["python", "server.py"]