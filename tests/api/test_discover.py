from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from parma_mining.linkedin.api.dependencies.auth import authenticate
from parma_mining.linkedin.api.main import app
from parma_mining.mining_common.const import HTTP_200, HTTP_500
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
def mock_discover_client(mocker) -> MagicMock:
    mock = mocker.patch(
        "parma_mining.linkedin.api.main.PhantombusterClient.discover_company"
    )
    mock.return_value = [
        {"name": "discovery_name", "url": "https://www.example.com"},
    ]
    return mock


def test_discover_endpoint(client: TestClient, mock_discover_client: MagicMock):
    query = "sample query"
    response = client.get(f"/discover?query={query}")
    assert response.status_code == HTTP_200
    assert isinstance(response.json(), list)
    mock_discover_client.assert_called_once_with(query)


def test_discover_endpoint_exception(
    client: TestClient, mock_discover_client: MagicMock
):
    mock_discover_client.side_effect = HTTPException(
        status_code=500, detail="Test error"
    )
    query = "sample query"
    response = client.get(f"/discover?query={query}")

    assert response.status_code == HTTP_500
    assert (
        "Can't run discovery agent successfully. Error: 500: Test error"
        in response.json()["detail"]
    )
