import logging
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


logger = logging.getLogger(__name__)


@pytest.fixture
def mock_linkedin_client(mocker) -> MagicMock:
    """Mocking the LinkedinClient's method to avoid actual API calls."""
    mock = mocker.patch(
        "parma_mining.linkedin.api.main.LinkedinClient.get_company_details"
    )
    mock.return_value = {
        "linkedin_id": "test_linkedin_id",
        "name": "Test Company",
        "profile_url": "http://testcompany.com",
        "ads_rule": "Test Ads Rule",
        "employee_count": 100,
        "active": True,
        "job_search_url": "http://testcompany.com/jobs",
        "phone": "123-456-7890",
        "tagline": "Test Tagline",
        "description": "Test Description",
        "website": "http://testcompany.com",
        "logo_url": "http://testcompany.com/logo.png",
        "follower_count": 1000,
        "universal_name": "testcompany",
        "headquarter_city": "Test City",
        "headquarter_country": "Test Country",
        "head_quarter_postal_code": "12345",
        "industries": ["Test Industry"],
        "locations": ["Test Location"],
        "specialities": ["Test Speciality"],
        "hashtags": ["Test Hashtag"],
        "founded_year": 2000,
        "founded_month": 1,
        "founded_day": 1,
    }

    return mock


@pytest.fixture
def mock_analytics_client(mocker) -> MagicMock:
    """Mocking the AnalyticClient's method to avoid actual API calls during testing."""
    mock = mocker.patch("parma_mining.linkedin.api.main.AnalyticsClient.feed_raw_data")
    mock = mocker.patch(
        "parma_mining.linkedin.api.main.AnalyticsClient.crawling_finished"
    )
    # No return value needed, but you can add side effects or exceptions if necessary
    return mock


def test_get_company_details(
    mock_linkedin_client: MagicMock,
    mock_analytics_client: MagicMock,
    client: TestClient,
):
    payload = {
        "task_id": 123,
        "companies": {
            "Example_id1": {"urls": ["https://www.linkedin.com/company/test"]},
            "Example_id2": {"urls": ["https://www.linkedin.com/company/test"]},
        },
    }

    headers = {"Authorization": "Bearer test"}
    response = client.post("/companies", json=payload, headers=headers)

    mock_analytics_client.assert_called()

    assert response.status_code == HTTP_200
