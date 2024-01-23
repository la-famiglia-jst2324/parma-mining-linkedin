from unittest.mock import MagicMock, patch

import pytest

from parma_mining.linkedin.client import LinkedinClient
from parma_mining.linkedin.model import DiscoveryResponse
from parma_mining.mining_common.exceptions import ClientError, CrawlingError


@pytest.fixture
def mock_linkedin_client():
    return LinkedinClient()


@patch("parma_mining.linkedin.client.search")
def test_discover_company_success(mock_search, mock_linkedin_client):
    mock_search.return_value = [
        "https://www.linkedin.com/company/test",
        "https://www.linkedin.com/company/test/about/",
    ]

    results = mock_linkedin_client.discover_company("Test")
    assert isinstance(results, DiscoveryResponse)
    assert len(results.urls) == 1
    assert results.urls[0] == "https://www.linkedin.com/company/test"


@patch("parma_mining.linkedin.client.search")
def test_discover_company_exception(mock_search_users, mock_linkedin_client):
    mock_search_users.side_effect = ClientError()
    with pytest.raises(ClientError):
        mock_linkedin_client.discover_company("Test")


@patch("parma_mining.linkedin.client.ApifyClient")
def test_get_company_details(mock_apify_client, mock_linkedin_client):
    # Create a mock for ApifyClient
    mock_client = MagicMock()
    mock_apify_client.return_value = mock_client

    # Prepare mock results
    mock_run_result = {
        "defaultDatasetId": "mocked_dataset_id",
    }

    # Prepare mock dataset item
    mock_item = {
        "name": "Mocked Company",
        "id": "123",
        "websiteUrl": "http://testcompany.com",
        "url": "http://testcompany.com",
        "adsRule": "Test Rule",
        "employeeCount": 200,
        "active": True,
        "jobSearchUrl": "http://testcompany.com/jobs",
        "phone": {"number": "123-456-7890"},
        "tagline": "Test Tagline",
        "description": "Test Description",
        "logoUrl": "http://testcompany.com/logo.png",
        "followerCount": 1000,
        "universalName": "testcompany",
        "specialities": ["Testing"],
        "headquarter": {
            "city": "Test City",
            "country": "Test Country",
            "postalCode": "12345",
        },
        "industries": [{"name": "Test Industry"}],
        "groupedLocations": [{"localizedName": "Test Location"}],
        "hashtag": [{"displayName": "Test Hashtag"}],
        "foundedOn": {"year": 2000, "month": 1, "day": 1},
    }

    # Configure mocks
    mock_client.actor.return_value.call.return_value = mock_run_result
    mock_client.dataset.return_value.iterate_items.return_value = [mock_item]

    # Run the method
    results = mock_linkedin_client.get_company_details(
        ["https://www.linkedin.com/company/test"]
    )

    # Assert the results
    assert results.name == "Mocked Company"
    assert results.linkedin_id == "123"


@patch("parma_mining.linkedin.client.ApifyClient")
def test_get_organization_details_exception(mock_apify_client, mock_linkedin_client):
    exception_instance = CrawlingError("Error fetching company details!")
    mock_apify_client.side_effect = exception_instance
    with pytest.raises(CrawlingError):
        mock_linkedin_client.get_company_details(
            ["https://www.linkedin.com/company/exceptional-test"]
        )
