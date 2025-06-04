import json
import logging
from kafka import KafkaProducer
from django.conf import settings

from .models import AuditLog

logger = logging.getLogger(__name__)
_producer = None

def _get_producer():
    global _producer
    if _producer is None and settings.KAFKA_BROKER_URL:
        try:
            _producer = KafkaProducer(
                bootstrap_servers=[settings.KAFKA_BROKER_URL],
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
        except Exception as exc:
            logger.error("Failed to create Kafka producer: %s", exc)
    return _producer

def record_audit_event(user, action, details: dict):
    entry = AuditLog.objects.create(user=user, action=action, details=details)
    producer = _get_producer()
    if producer:
        try:
            producer.send(
                "audit_logs",
                {
                    "timestamp": entry.timestamp.isoformat(),
                    "user_id": entry.user_id,
                    "action": entry.action,
                    "details": entry.details,
                },
            )
        except Exception as exc:
            logger.error("Failed to send audit log to Kafka: %s", exc)
    return entry
