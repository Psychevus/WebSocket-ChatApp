# WebSocket Chat Application

## Overview

This project showcases a real-time chat platform built with Django and Django Channels. Redis is used for transient message queuing while conversations and messages are persisted in a relational database. Docker Compose provides a reproducible environment so the app can be launched with minimal setup.

## Features

- Bidirectional messaging over WebSockets
- Persistent conversation and message history
- Rate limiting on both HTTP views and WebSocket endpoints
- Robust form validation and error logging
- Containerised services for the application, database and Redis

## Quick Start

### Prerequisites
- Docker installed on your machine

### Run with Docker
```bash
git clone https://github.com/Psychevus/WebSocket-ChatApp.git
cd WebSocket-ChatApp
docker-compose build
docker-compose up
```
The application will be available at `http://localhost:8000`.

## Usage
- Register for an account then log in
- Start a conversation with any other user
- Chat in real time via an interactive WebSocket interface

## Running Tests
Use SQLite and the in-memory channel layer when executing tests:
```bash
docker-compose exec chatapp-django python manage.py test ChatApp.tests --settings=WebSocketChatApp.test_settings
```

## Deployment
Adjust environment variables to suit your production environment and deploy using your preferred platform. The provided Docker configuration can be adapted for cloud container services.

## Contributing
We welcome contributions! Please open pull requests against the `work` branch and ensure the test suite passes.

## License
This project is available under the [MIT License](LICENSE).
