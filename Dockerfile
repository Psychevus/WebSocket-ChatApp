# Use an official Python runtime as a parent image
FROM python:3.11

LABEL maintainer="Psychevus"
LABEL description="Django WebSocket Chat App"
LABEL version="1.0"

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y gcc libffi-dev libssl-dev && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies first to leverage Docker layer caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

WORKDIR /app/WebSocketChatApp

EXPOSE 8000

CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "WebSocketChatApp.asgi:application"]

