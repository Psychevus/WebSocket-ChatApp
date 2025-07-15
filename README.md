# WebSocket Chat Application

[![GitHub stars](https://img.shields.io/github/stars/Psychevus/WebSocket-ChatApp?style=social)](https://github.com/Psychevus/WebSocket-ChatApp/stargazers)
[![Docker Build](https://img.shields.io/github/actions/workflow/status/Psychevus/WebSocket-ChatApp/ci.yml?label=Docker%20Build)](https://github.com/Psychevus/WebSocket-ChatApp/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/Psychevus/WebSocket-ChatApp)](LICENSE)
![Coverage](.github/badges/coverage.svg)
[![Coverage Status](https://img.shields.io/badge/coverage-passing-brightgreen)](#)
[![Render Deploy](https://img.shields.io/badge/Render-Demo-blue)](#)

## 🚀 Live Demo on Render
A stripped-down profile is deployed on **Render Free Tier**
👉 https://your-demo.onrender.com


## Project Overview

This repository contains a modular, production-grade real-time chat system built on Django and Django Channels, leveraging Redis as the asynchronous message broker and WebSockets for real-time bidirectional communication. The system prioritizes encryption, resilience, and observability—making it suitable for secure, scalable deployments in enterprise environments.

## Architectural Highlights

- **ASGI-based real-time WebSocket infrastructure** backed by Django Channels and Daphne
- **JWT-secured WebSocket connections**, enforcing session-based access and role validation
- **Redis-powered message queueing** for transient communication and asynchronous background tasks
- **OpenTelemetry integration** for distributed tracing across services
- **Structured logging pipeline** compatible with ELK and SIEM platforms
- **Docker-native orchestration** with support for CI/CD, multi-stage builds, and secure container isolation
- **Full Helm + Kustomize Kubernetes support**, enabling rapid deployment across dev, staging, and production environments
- **Pluggable encryption models**: 
  - Client-side E2EE (1:1 chat using X25519/double-ratchet)
  - Group key management with Bring Your Own Key (BYOK) and AWS KMS integration
- **Security-first design**: DLP hooks, ephemeral messages, CSP enforcement, and automated vulnerability scanning
- **SCIM-based user provisioning** and support for SAML 2.0 / OIDC enterprise identity providers

## Core Capabilities

- Persistent, rate-limited, encrypted chat messaging
- Typing indicators and message lifecycle events
- Real-time client feedback using WebSocket state tracking
- API-level protection using DRF throttles and IP-aware middleware
- Admin interface for managing user roles, rooms, and retention settings
- Configurable self-destruction of messages via TTL/Celery
- SHA-chained, tamper-evident audit logs (optional Kafka integration)
- Fine-grained retention and legal hold enforcement
- Metrics exposed via Prometheus-compatible HTTP endpoints

## Technology Stack

- **Backend:** Django 4.x, Django Channels, Redis, Daphne, Celery
- **Auth:** JWT (via DRF), Django auth, SAML, OIDC, SCIM
- **Security Tooling:** Bandit, Trivy, Gitleaks, CSP, HTTPS by default
- **Observability:** OpenTelemetry, Prometheus, Jaeger, Grafana
- **Containerization:** Docker, Docker Compose, Helm, Kustomize
- **Tests:** Pytest with full coverage and CI assertions

## Local Deployment (Docker)

### Prerequisites

- Docker >= 24.0
- Docker Compose >= 2.0

### Run

```bash
git clone https://github.com/Psychevus/WebSocket-ChatApp.git
cd WebSocket-ChatApp
docker-compose build
docker-compose up
````

* Application: [http://localhost:8000](http://localhost:8000)
* Prometheus Metrics: [http://localhost:9090](http://localhost:9090)
* Grafana: [http://localhost:3000](http://localhost:3000) (default: `admin` / `admin`)
* Jaeger UI: [http://localhost:16686](http://localhost:16686)

### Quick Start (Free Demo)

```bash
docker build -f Dockerfile.demo -t chat-demo .
docker run -p 8000:8000 chat-demo
wscat -c ws://localhost:8000/ws/room/test/
```

**Note:** The demo disables Kafka, Celery, DLP, BYOK/KMS, and uses an in-memory channel layer. Full enterprise features remain in the default configuration.

## Testing & Code Quality

```bash
pip install -r requirements-dev.txt
pytest --cov=ChatApp --cov=WebSocketChatApp
```

* Coverage must exceed 80% (enforced via CI)
* Static analysis: `bandit`, `gitleaks`, `trivy` scans triggered on push
* Linting, secret detection, and dependency vulnerability audits are automated

## CI/CD Pipeline

The GitHub Actions workflow includes:

* Python environment bootstrap and dependency installation
* Unit/integration test execution with coverage
* Coverage summary export in Cobertura-compatible XML and JSON
* Security scanning (code, secrets, container images)
* Docker image build via BuildKit
* Conditional Helm chart packaging (for release branches)
* CVSS-aware failure thresholds on container vulnerabilities

## Kubernetes Deployment

### Helm

```bash
helm install chatapp ./deploy/helm -f deploy/helm/values-dev.yaml
```

For production overlays:

```bash
helm install chatapp ./deploy/helm -f deploy/helm/values-prod.yaml
```

### Kustomize

```bash
kustomize build deploy/kustomize/overlays/dev | kubectl apply -f -
```

Blue/green strategy supported. Rollout switch via:

```bash
bash ./scripts/rollout_to_green.sh
```

## Message Encryption

### One-to-One E2EE

* X25519 handshake
* Double-ratchet encryption model (similar to Signal protocol)
* Messages encrypted on the client before transmission

### Group BYOK

* Server-side encrypted using a unique per-group AES key
* BYOK stored in AWS KMS; rotation schedule configurable
* Legal hold and S3 export supported via background jobs

## Data Loss Prevention (DLP)

To enable Nightfall scanning on message transmission:

```bash
DLP_BEFORE_SEND_HOOK=ChatApp.dlp_plugins.nightfall_scan
NIGHTFALL_API_KEY=<token>
```

## Security Practices

* TLS required in production
* Secure, HttpOnly cookies
* CSP configured via `django-csp`
* Session management hardened against CSRF and replay attacks
* Audit logs chained and immutable
* Optional Kafka broker for security event streaming
* Entra ID (Azure AD) support for SAML SSO and SCIM provisioning

## Environment Configuration

```ini
DJANGO_SECRET_KEY=...
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=example.com
MYSQL_USER=chatapp
MYSQL_PASSWORD=...
REDIS_HOST=chatapp-redis
MESSAGE_ENCRYPTION_KEY=...
KMS_KEY_ID=...
CELERY_BROKER_URL=redis://chatapp-redis:6379/0
EPHEMERAL_MESSAGE_TTL=30
DLP_BEFORE_SEND_HOOK=...
NIGHTFALL_API_KEY=...
KAFKA_BROKER_URL=...
TOTP_ENFORCE=True
CSP_REPORT_ONLY=False
```

## Documentation

* [docs/scaling.md](docs/scaling.md): Horizontal scaling guidelines
* [docs/entra-id-sso-scim.md](docs/entra-id-sso-scim.md): Entra SSO + SCIM setup
* [OWASP\_SECURITY.md](OWASP_SECURITY.md): Secure deployment checklist

## Contributing

Please ensure all tests pass locally before submitting a pull request. Code must conform to repository linting and security policies. Feature proposals should be documented via GitHub Issues.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
