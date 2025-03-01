FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y git
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV RUNNING_IN_DOCKER=true
ENV PYTHONUNBUFFERED=1

CMD ["python", "server.py"]