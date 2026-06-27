import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

_tracer = None
_propagator = TraceContextTextMapPropagator()


def init_tracer(service_name="SentinelCell"):
    global _tracer
    if _tracer is not None:
        return _tracer

    resource = Resource(attributes={SERVICE_NAME: service_name})

    provider = TracerProvider(resource=resource)

    # Check if OTLP is configured
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if otlp_endpoint:
        otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    else:
        # Fallback to console exporter if no OTLP endpoint is provided
        import sys

        if "pytest" not in sys.modules:
            provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

    trace.set_tracer_provider(provider)
    _tracer = trace.get_tracer(__name__)
    return _tracer


def get_tracer():
    global _tracer
    if _tracer is None:
        return init_tracer()
    return _tracer


def inject_trace_context(payload_dict: dict) -> dict:
    """Injects the current active trace context into a dictionary (usually payload metadata)."""
    _propagator.inject(payload_dict)
    return payload_dict


def extract_trace_context(payload_dict: dict):
    """Extracts trace context from a dictionary and returns a Context object."""
    return _propagator.extract(payload_dict)
