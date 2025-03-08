FROM python:3.10-slim
WORKDIR /app
COPY server.py particule_utils.py createParticule.py loadGraph.py listGraph.py updateParticule.py exportGraph.py deleteParticule.py addSubParticule.py list_dir.py check_root.py tech_stack.py ./
RUN pip install fastmcp lark
EXPOSE 8000
CMD ["python", "server.py"]