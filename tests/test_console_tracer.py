from WebSocketChatApp.console_tracer_provider import tracer_provider
from opentelemetry.sdk.trace import TracerProvider


def test_console_tracer_provider_output():
    provider = tracer_provider()
    assert isinstance(provider, TracerProvider)
