import os

from opentelemetry import metrics, trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from prometheus_client import start_http_server

metrics_port = int(os.getenv("METRICS_PORT", "8001"))
start_http_server(port=metrics_port)

_reader = PrometheusMetricReader()
_provider = MeterProvider(metric_readers=[_reader])
metrics.set_meter_provider(_provider)

tracer_provider = TracerProvider()
console_processor = BatchSpanProcessor(ConsoleSpanExporter())
tracer_provider.add_span_processor(console_processor)

jaeger_exporter = JaegerExporter(
    agent_host_name=os.getenv("JAEGER_HOST", "localhost"),
    agent_port=int(os.getenv("JAEGER_PORT", "6831")),
)
jaeger_processor = BatchSpanProcessor(jaeger_exporter)
tracer_provider.add_span_processor(jaeger_processor)
trace.set_tracer_provider(tracer_provider)

DjangoInstrumentor().instrument()
RedisInstrumentor().instrument()

_meter = metrics.get_meter("chatapp")
websocket_latency_histogram = _meter.create_histogram(
    "chatapp.websocket.message_latency_ms",
    unit="ms",
    description="Latency of WebSocket message delivery",
)

redis_latency_histogram = _meter.create_histogram(
    "chatapp.redis.pubsub_latency_ms",
    unit="ms",
    description="Latency of Redis publish/subscribe",
)


def record_websocket_latency(duration_ms: float):
    websocket_latency_histogram.record(duration_ms)


def record_pubsub_latency(duration_ms: float):
    redis_latency_histogram.record(duration_ms)
