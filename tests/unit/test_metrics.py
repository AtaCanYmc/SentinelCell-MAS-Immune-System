from fastapi.testclient import TestClient
from src.gateways.fastapi_gateway import app
from src.core.telemetry import metrics


def test_metrics_endpoint():
    """Test if Prometheus metrics endpoint is exposed and returning 200."""
    client = TestClient(app)
    response = client.get("/metrics")

    assert response.status_code == 200
    content = response.text

    # Assert that our custom metrics are registered
    assert "sentinelcell_intercepts_total" in content
    assert "sentinelcell_healing_success_total" in content
    assert "sentinelcell_healing_failure_total" in content
    assert "sentinelcell_processing_latency_seconds" in content


def test_metrics_increment():
    """Test if metrics can be incremented."""
    # Record initial count conceptually (not strictly necessary to assert absolute value, just that it doesn't crash)
    metrics.healing_success.inc()
    metrics.payload_intercepts.labels(status="received").inc()
    metrics.latency.observe(0.5)

    # This just ensures no exceptions are raised when interacting with the metrics
    assert True
