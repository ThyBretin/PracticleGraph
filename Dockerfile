FROM python:3.10-slim
WORKDIR /app
COPY server.py particule_utils.py createParticule.py loadParticule.py listParticule.py updateParticule.py exportParticule.py deleteParticule.py addContext.py list_dir.py check_root.py tech_stack.py ./
RUN pip install fastmcp
EXPOSE 8000
CMD ["python", "server.py"]