import pytest
from fastapi import status
from fastapi.testclient import TestClient

from parma_mining.linkedin.api import app


@pytest.fixture
def client():
    assert app
    return TestClient(app)


def test_root_endpoint(client: TestClient):
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"welcome": "at parma-mining-linkedin"}
