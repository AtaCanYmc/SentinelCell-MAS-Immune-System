import os
from pydantic import BaseModel, Field
from typing import Dict, Any
from prometheus_client import Counter, Histogram, Gauge


class OTelResource(BaseModel):
    """Resource defining the origin of the telemetry."""

    attributes: Dict[str, Any]


def get_severity_text():
    return os.getenv("TELEMETRY_LOG_LEVEL", "INFO").upper()


def get_severity_number():
    level = os.getenv("TELEMETRY_LOG_LEVEL", "INFO").upper()
    return {"INFO": 9, "WARN": 13, "ERROR": 17}.get(level, 9)


class OpenTelemetryLog(BaseModel):
    """
    Pydantic Schema for OpenTelemetry Log Record Format.
    Ensures strict adherence to OTel logging specifications.
    """

    Timestamp: int = Field(description="Time of the log record in Unix nano-seconds")
    TraceId: str = Field(description="Request trace ID")
    SpanId: str = Field(description="Request span ID")
    TraceFlags: int = Field(default=1, description="W3C trace flag")
    SeverityText: str = Field(
        default_factory=get_severity_text, description="Severity textual representation"
    )
    SeverityNumber: int = Field(
        default_factory=get_severity_number,
        description="Severity numerical value (INFO=9)",
    )
    Body: str = Field(description="The string or structured log body")
    Resource: OTelResource = Field(description="Resource attributes")
    Attributes: Dict[str, Any] = Field(
        description="Additional log attributes specific to the event"
    )


class SentinelMetrics:
    """Prometheus metrics for SentinelCell"""

    def __init__(self):
        self.payload_intercepts = Counter(
            "sentinelcell_intercepts_total",
            "Total payloads intercepted by the Immune System",
            ["status"],
        )
        self.healing_success = Counter(
            "sentinelcell_healing_success_total", "Total payloads successfully healed"
        )
        self.healing_failure = Counter(
            "sentinelcell_healing_failure_total",
            "Total payloads quarantined after failed healing attempts",
        )
        self.latency = Histogram(
            "sentinelcell_processing_latency_seconds",
            "Latency of the payload processing pipeline",
            buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, float("inf")),
        )
        self.quarantine_status = Gauge(
            "sentinelcell_quarantine_status",
            "1 if the Immune System is in Quarantine Mode, 0 otherwise",
        )


# Global singleton
metrics = SentinelMetrics()
