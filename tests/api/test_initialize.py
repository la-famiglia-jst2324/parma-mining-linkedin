import json
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from parma_mining.linkedin.api.dependencies.auth import authenticate
from parma_mining.linkedin.api.main import app
from parma_mining.mining_common.const import HTTP_200
from tests.dependencies.mock_auth import mock_authenticate


@pytest.fixture
def client():
    assert app
    app.dependency_overrides.update(
        {
            authenticate: mock_authenticate,
        }
    )
    return TestClient(app)


@pytest.fixture
def mock_analytics_client(mocker) -> MagicMock:
    mock = mocker.patch(
        "parma_mining.linkedin.api.main.analytics_client.register_measurements",
        return_value=(None, "normalized_map"),
    )
    return mock


def test_initialize_endpoint(client: TestClient, mock_analytics_client: MagicMock):
    response = client.get("/initialize?source_id=123")

    mock_analytics_client.assert_called_once()
    assert response.status_code == HTTP_200

    results = json.loads(response.content)
    assert "frequency" in results
    assert "normalization_map" in results
