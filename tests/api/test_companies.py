import logging
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient

from parma_mining.linkedin.api.dependencies.auth import authenticate
from parma_mining.linkedin.api.main import app
from parma_mining.mining_common.const import HTTP_200, HTTP_404, HTTP_500
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


logger = logging.getLogger(__name__)


@pytest.fixture
def mock_pb_client(mocker) -> MagicMock:
    """Mocking the PhantombusterClient's method to avoid actual API calls."""
    mock = mocker.patch(
        "parma_mining.linkedin.api.main.PhantombusterClient.scrape_company"
    )
    mock.return_value = [
        {
            # mock  the fields example
            "id": "example_id",
            "name": "example_name",
            "data_source": "example_data_source",
            "link": "example_link",
            "location": "example_location",
            "industry": "example_industry",
            "industry_code": "example_industry_code",
            "description": "example_description",
            "website": "example_website",
            "phone": "example_phone",
            "specialities": "example_specialities",
            "size": "example_size",
            "logo": "example_logo",
            "banner": "example_banner",
            "domain": "example_domain",
            "address": "example_address",
            "headquarters": "example_headquarters",
            "founded": "example_founded",
            "follower_count": 0,
            "employee_count": 0,
            "company_id": 1,
            "linkedin_id": "example_linkedin_id",
            "sales_navigator_link": "example_sales_navigator_link",
            "query": "example_query",
            "timestamp": "example_timestamp",
        }
    ]
    return mock


@pytest.fixture
def mock_analytics_client(mocker) -> tuple[MagicMock, MagicMock]:
    """Mocking the AnalyticsClient's methods."""
    mock_feed_raw_data = mocker.patch(
        "parma_mining.linkedin.api.main.AnalyticsClient.feed_raw_data"
    )
    mock_crawling_finished = mocker.patch(
        "parma_mining.linkedin.api.main.AnalyticsClient.crawling_finished"
    )

    return mock_feed_raw_data, mock_crawling_finished


def test_companies_success(
    client: TestClient, mock_pb_client: MagicMock, mock_analytics_client: MagicMock
):
    mock_feed_raw_data, mock_crawling_finished = mock_analytics_client

    payload = {
        "task_id": 123,
        "companies": {
            "Example_id1": {
                "name": ["langfuse"],
                "url": ["www.linkedin.com/company/langfuse"],
            },
            "Example_id2": {
                "name": ["personio"],
                "url": ["www.linkedin.com/company/personio"],
            },
        },
    }

    response = client.post("/companies", json=payload)

    mock_feed_raw_data.assert_called()
    mock_crawling_finished.assert_called()
    mock_pb_client.assert_called()

    assert response.status_code == HTTP_200


def test_companies_bad_request(client: TestClient, mocker):
    mocker.patch(
        "parma_mining.linkedin.api.main.PhantombusterClient.scrape_company",
        side_effect=HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Company not found"
        ),
    )

    payload = {
        "task_id": 123,
        "companies": {
            "Example_id1": {
                "name": ["langfuse"],
                "url": ["www.linkedin.com/company/langfuse"],
            },
            "Example_id2": {
                "name": ["personio"],
                "url": ["www.linkedin.com/company/personio"],
            },
        },
    }
    response = client.post("/companies", json=payload)
    assert response.status_code == HTTP_404


def test_companies_no_linkedin_url(
    client: TestClient, mock_pb_client: MagicMock, mock_analytics_client: MagicMock
):
    mock_feed_raw_data, mock_crawling_finished = mock_analytics_client

    payload = {
        "task_id": 123,
        "companies": {
            "Example_id1": {
                "name": ["company1"],
                "url": ["http://www.example.com/company1"],
            },
            "Example_id2": {
                "name": ["company2"],
                "url": ["http://www.example.com/company2"],
            },
        },
    }

    mock_pb_client.return_value = []
    mock_feed_raw_data.return_value = None
    mock_crawling_finished.return_value = []

    response = client.post("/companies", json=payload)
    assert response.status_code == HTTP_200
    mock_pb_client.assert_called()
    mock_crawling_finished.assert_called()


def test_companies_http_exception_in_analytics(
    client: TestClient, mock_pb_client: MagicMock, mocker
):
    mocker.patch(
        "parma_mining.linkedin.api.main.AnalyticsClient.feed_raw_data",
        side_effect=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Analytics server error",
        ),
    )

    payload = {
        "task_id": 123,
        "companies": {
            "Example_id1": {
                "name": ["langfuse"],
                "url": ["www.linkedin.com/company/langfuse"],
            },
            "Example_id2": {
                "name": ["personio"],
                "url": ["www.linkedin.com/company/personio"],
            },
        },
    }

    response = client.post("/companies", json=payload)
    assert response.status_code == HTTP_500
    assert "Can't send crawling data to the Analytics" in response.json()["detail"]
