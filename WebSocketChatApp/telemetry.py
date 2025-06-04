import os
from opentelemetry import metrics
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from prometheus_client import start_http_server
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.instrumentation.django import DjangoInstrumentor

metrics_port = int(os.getenv("METRICS_PORT", "8001"))
start_http_server(port=metrics_port)

_reader = PrometheusMetricReader()
_provider = MeterProvider(metric_readers=[_reader])
metrics.set_meter_provider(_provider)

DjangoInstrumentor().instrument()

_meter = metrics.get_meter("chatapp")
websocket_latency_histogram = _meter.create_histogram(
    "chatapp.websocket.message_latency_ms",
    unit="ms",
    description="Latency of WebSocket message delivery",
)


def record_websocket_latency(duration_ms: float):
    websocket_latency_histogram.record(duration_ms)
