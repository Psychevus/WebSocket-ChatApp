# WebSocket Chat Application

## Overview
The WebSocket Chat Application demonstrates real-time messaging using Django, Django Channels and Redis. Conversations are stored in a relational database while Redis handles transient message queuing. Docker Compose orchestrates the services to provide a consistent environment with minimal setup.

## Features
- Live chat over WebSocket connections
- Persistent conversation and message history
- Rate limiting on HTTP views and WebSocket endpoints
- Robust form validation and logging
- Dockerised services for the application, MySQL database and Redis

## Quick Start
### Prerequisites
- Docker and Docker Compose

### Run with Docker
```bash
git clone <repo-url>
cd WebSocket-ChatApp
docker-compose build
docker-compose up
```
The application will be available at `http://localhost:8000`.

## Running Tests
Use SQLite and the in-memory channel layer when executing tests:
```bash
python manage.py test ChatApp.tests --settings=WebSocketChatApp.test_settings
```

## Deployment
Update environment variables as required for your platform. The provided Docker configuration can be adapted for cloud container services.

## Security Configuration
A checklist of common security considerations is available in [OWASP_SECURITY.md](OWASP_SECURITY.md). Sensitive settings are read from environment variables such as:
```
DJANGO_SECRET_KEY=<your secret key>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=example.com,www.example.com
DJANGO_SECURE_SSL_REDIRECT=True
DJANGO_SECURE_HSTS_SECONDS=3600
MYSQL_DATABASE=chatapp
MYSQL_USER=chatapp
MYSQL_PASSWORD=<db password>
MYSQL_HOST=chatapp-db
REDIS_HOST=chatapp-redis
```
Ensure HTTPS is enabled and cookies are transmitted securely.

## Contributing
Contributions are welcome! Please open pull requests and ensure the test suite passes.

## License
This project is available under the [MIT License](LICENSE).
