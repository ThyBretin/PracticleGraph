FROM python:3.10-slim
WORKDIR /app
RUN apt-get update && apt-get install -y git
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt
COPY . .
CMD ["fastmcp", "run", "server.py"]