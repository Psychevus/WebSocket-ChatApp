# WebRTC and Huddle

Huddles use WebRTC for real‑time audio and video. Most clients are behind NATs or firewalls so a TURN server is required for reliable connectivity.

## TURN Setup

Any standards compliant TURN server such as **coturn** can be used. A minimal configuration looks like:

```bash
sudo apt-get install coturn
cat <<CONF | sudo tee /etc/turnserver.conf
listening-port=3478
fingerprint
lt-cred-mech
use-auth-secret
static-auth-secret=<RANDOM_SECRET>
CONF
sudo turnserver -c /etc/turnserver.conf
```

In `WebSocketChatApp.settings` set the public address and credentials:

```python
TURN_SERVER = "turn:your-domain:3478"
TURN_USERNAME = "user"
TURN_PASSWORD = "pass"
```

Expose ports 3478 UDP and TCP so peers can reach the server.
