FROM python:3.10
RUN apt-get update && apt-get install -y nodejs npm
WORKDIR /app
COPY server.py particule_utils.py addSubParticule.py createParticule.py loadGraph.py listGraph.py updateParticule.py exportGraph.py deleteParticule.py list_dir.py check_root.py babel_parser.js file_handler.py tech_stack.py ./
RUN pip install fastmcp lark pathspec
RUN npm install @babel/parser
CMD ["python", "server.py"]