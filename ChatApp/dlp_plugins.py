import logging
import os

import requests

logger = logging.getLogger(__name__)


def nightfall_scan(message: str, sender=None):
    """Send message to Nightfall DLP API. Returns True when no findings."""
    api_key = os.getenv('NIGHTFALL_API_KEY')
    if not api_key:
        return True
    try:
        response = requests.post(
            'https://api.nightfall.ai/v3/scan',
            json={'payload': message},
            headers={'Authorization': f'Bearer {api_key}'},
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()
        return len(data.get('findings', [])) == 0
    except Exception as exc:
        logger.error('Nightfall scan failed: %s', exc)
        return True


def google_dlp_scan(message: str, sender=None):
    """Reference Google DLP scan plugin."""
    try:
        from google.cloud import dlp_v2
    except Exception:
        logger.error('google-cloud-dlp library not installed')
        return True

    project_id = os.getenv('GOOGLE_PROJECT_ID')
    if not project_id:
        return True

    client = dlp_v2.DlpServiceClient()
    parent = f"projects/{project_id}"
    item = {'value': message}
    response = client.inspect_content(parent=parent, item=item)
    return len(response.result.findings) == 0
