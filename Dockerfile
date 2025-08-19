FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update -y && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY mcp_server ./mcp_server
COPY .env.example ./

EXPOSE 8080
CMD ["uvicorn", "mcp_server.main:app", "--host", "0.0.0.0", "--port", "8080", "--ws", "websockets"] 