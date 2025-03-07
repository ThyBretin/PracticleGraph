FROM python:3.10-slim
WORKDIR /app
COPY server.py practicle_utils.py createPracticle.py showPracticle.py listPracticle.py updatePracticle.py exportPracticle.py deletePracticle.py list_dir.py check_root.py tech_stack.py ./
RUN pip install fastmcp
EXPOSE 8000
CMD ["python", "server.py"]