import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from src.gateways.fastapi_gateway import app

client = TestClient(app)


@pytest.fixture
def mock_sentinel():
    with patch("src.gateways.fastapi_gateway.sentinel") as mock_s:
        mock_s.intercept = AsyncMock()
        yield mock_s


def test_dashboard_route():
    response = client.get("/dashboard")
    assert response.status_code == 200


def test_intercept_success(mock_sentinel):
    mock_sentinel.intercept.return_value = {
        "status": "success",
        "message": "healed data",
    }

    response = client.post(
        "/intercept?source=Alpha&target=Beta", content='{"broken": "json"}'
    )
    assert response.status_code == 200
    assert response.json() == {"status": "success", "message": "healed data"}


def test_intercept_quarantine_drop(mock_sentinel):
    # When Sentinel returns None, it implies quarantine/malicious drop
    mock_sentinel.intercept.return_value = None

    response = client.post(
        "/intercept?source=Alpha&target=Beta", content='{"malicious": "payload"}'
    )
    assert response.status_code == 400
    assert "detail" in response.json()
