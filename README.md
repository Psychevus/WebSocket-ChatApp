# WebSocket Chat Application

## Overview
The WebSocket Chat Application demonstrates real-time messaging using Django, Django Channels and Redis. Conversations are stored in a relational database while Redis handles transient message queuing. Docker Compose orchestrates the services to provide a consistent environment with minimal setup.

## Features
- Live chat over WebSocket connections
- Persistent conversation and message history
- Rate limiting on HTTP views and WebSocket endpoints
- Robust form validation and logging
- Message sanitisation and length checks for extra security
- WebSocket connections automatically use `wss://` when the site is served over HTTPS
- Typing indicators show when participants are composing a message
- End-to-end encryption for 1-to-1 chats uses the double-ratchet algorithm with
  an X25519 handshake. Messages are encrypted client-side before being sent.
- Group conversations are encrypted at rest with BYOK-managed keys. Tenant keys
  are stored in AWS KMS following a pattern similar to Slack EKM.
- Pluggable data-loss-prevention hooks scan outgoing messages
- Per-room retention policies with legal hold and S3 export
- Ephemeral messages that self-destruct after a short TTL
- Two-factor authentication for account logins
- Immutable audit logs streamed to Kafka for SIEM integration
- Enterprise identity via SAML 2.0 and OpenID Connect
- SCIM-based user provisioning
- Role-based access control (Owner, Admin, Analyst)
- Dockerised services for the application, MySQL database and Redis
- Real-time telemetry with OpenTelemetry, Prometheus and Grafana

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

Prometheus will expose metrics on `http://localhost:9090` and Grafana will be available at `http://localhost:3000` (default credentials `admin`/`admin`).

## Telemetry
Metrics are exported using OpenTelemetry and Prometheus. Grafana Live can be used to visualise latency in real time. The Prometheus scrape endpoint is exposed on port `8001` from the Django container.

## Running Tests
Use SQLite and the in-memory channel layer when executing tests:
```bash
python manage.py test ChatApp.tests --settings=WebSocketChatApp.test_settings
```

Periodically clear expired messages using:
```bash
python manage.py expunge_old_messages
```

Ephemeral messages are purged automatically via Celery beat. Start a worker with:
```bash
celery -A WebSocketChatApp worker -B
```

## Deployment
Update environment variables as required for your platform. The provided Docker configuration can be adapted for cloud container services. A Helm chart and Kustomize overlays are also available under `deploy/` for Kubernetes environments.

### Kubernetes Deployment with Helm
```bash
helm install chatapp ./deploy/helm \
  --set encryption.key=$(base64 -w0 <path to key>) \
  --set saml.configPath=/etc/saml/config.json \
  --set scim.bearerToken=$SCIM_TOKEN
```
The chart provisions MySQL and Redis alongside the Django application so you can get running in minutes.

### Kustomize Overlays
Example overlays are located in `deploy/kustomize/overlays/`. Build the base manifests and apply an overlay with:
```bash
kustomize build deploy/kustomize/overlays/example | kubectl apply -f -
```

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
MESSAGE_ENCRYPTION_KEY=<base64 key for BYOK>
KMS_KEY_ID=<AWS KMS key ID for BYOK/EKM>
DLP_BEFORE_SEND_HOOK=ChatApp.dlp.default_dlp_callback
NIGHTFALL_API_KEY=<optional Nightfall API key>
ORG_RETENTION_DAYS=30
WORKSPACE_RETENTION_DAYS=30
EXPUNGE_S3_BUCKET=<optional S3 bucket for exports>
CELERY_BROKER_URL=redis://chatapp-redis:6379/0
EPHEMERAL_MESSAGE_TTL=30
MESSAGE_MAX_LENGTH=500
KAFKA_BROKER_URL=<optional Kafka broker for audit logs>
SAML_CONFIG_PATH=<path to saml config json>
OIDC_CLIENT_ID=<OIDC client id>
OIDC_CLIENT_SECRET=<OIDC client secret>
SCIM_BEARER_TOKEN=<token for SCIM auth>
TOTP_ENFORCE=True
```
Ensure HTTPS is enabled and cookies are transmitted securely.

## Entra ID SAML + SCIM Setup

For a walk-through of enabling single sign-on with Microsoft Entra ID and configuring automatic user and group provisioning, see [docs/entra-id-sso-scim.md](docs/entra-id-sso-scim.md).

## Contributing
Contributions are welcome! Please open pull requests and ensure the test suite passes.

## License
This project is available under the [MIT License](LICENSE).
