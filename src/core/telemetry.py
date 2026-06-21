from pydantic import BaseModel, Field
from typing import Dict, Any


class OTelResource(BaseModel):
    """Resource defining the origin of the telemetry."""

    attributes: Dict[str, Any]


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
        default="INFO", description="Severity textual representation"
    )
    SeverityNumber: int = Field(
        default=9, description="Severity numerical value (INFO=9)"
    )
    Body: str = Field(description="The string or structured log body")
    Resource: OTelResource = Field(description="Resource attributes")
    Attributes: Dict[str, Any] = Field(
        description="Additional log attributes specific to the event"
    )
