# Use an official Python runtime as a parent image
FROM python:3.11

LABEL maintainer="Psychevus"
LABEL description="Django WebSocket Chat App"
LABEL version="1.0"

WORKDIR /app/WebSocketChatApp

COPY . /app/

RUN apt-get update && apt-get upgrade -y && apt-get install -y gcc libffi-dev libssl-dev

COPY ./requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

EXPOSE 8000

ENV NAME World

CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "WebSocketChatApp.asgi:application"]

