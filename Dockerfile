FROM python:3.10
RUN apt-get update && apt-get install -y nodejs npm
WORKDIR /app
COPY server.py particle_utils.py addSubParticle.py createParticle.py loadGraph.py listGraph.py updateParticle.py exportGraph.py deleteParticle.py list_dir.py check_root.py babel_parser.js file_handler.py tech_stack.py createCodebaseParticle.py loadCodebaseGraph.py exportCodebaseGraph.py ./
RUN pip install fastmcp lark pathspec
RUN npm install @babel/parser
CMD ["python", "server.py"]