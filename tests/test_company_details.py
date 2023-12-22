from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from starlette import status

from parma_mining.linkedin.api.main import app
from parma_mining.mining_common.const import HTTP_200, HTTP_404

client = TestClient(app)


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
def mock_analytics_client(mocker) -> MagicMock:
    """Mocking the AnalyticClient's method to avoid actual API calls during testing."""
    mock = mocker.patch("parma_mining.linkedin.api.main.AnalyticsClient.feed_raw_data")
    # No return value needed, but you can add side effects or exceptions if necessary
    return mock


def test_get_organization_details(
    mock_pb_client: MagicMock, mock_analytics_client: MagicMock
):
    payload = {
        "companies": {
            "Example_id1": {
                "name": ["langfuse"],
                "url": ["www.linkedin.com/company/langfuse"],
            },
            "Example_id2": {
                "name": ["personio"],
                "url": ["www.linkedin.com/company/personio"],
            },
        }
    }

    response = client.post("/companies", json=payload)

    mock_analytics_client.assert_called()

    assert response.status_code == HTTP_200


def test_get_organization_details_bad_request(mocker):
    mocker.patch(
        "parma_mining.linkedin.api.main.PhantombusterClient.scrape_company",
        side_effect=HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Company not found"
        ),
    )

    payload = {
        "companies": {
            "Example_id1": {
                "name": ["langfuse"],
                "url": ["www.linkedin.com/company/langfuse"],
            },
            "Example_id2": {
                "name": ["personio"],
                "url": ["www.linkedin.com/company/personio"],
            },
        }
    }
    response = client.post("/companies", json=payload)
    assert response.status_code == HTTP_404
