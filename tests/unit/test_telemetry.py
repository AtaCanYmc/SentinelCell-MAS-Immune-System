import pytest
import time
from src.core.telemetry import OpenTelemetryLog, OTelResource
from pydantic import ValidationError


def test_telemetry_valid():
    log = OpenTelemetryLog(
        Timestamp=int(time.time() * 1e9),
        TraceId="a" * 32,
        SpanId="b" * 16,
        TraceFlags=1,
        SeverityText="INFO",
        SeverityNumber=9,
        Body="Test body",
        Resource=OTelResource(attributes={"service.name": "TestService"}),
        Attributes={"custom.field": "value"},
    )
    assert log.SeverityText == "INFO"
    assert log.Attributes["custom.field"] == "value"


def test_telemetry_invalid():
    with pytest.raises(ValidationError):
        # Missing required fields
        OpenTelemetryLog(
            Body="Test body",
        )
