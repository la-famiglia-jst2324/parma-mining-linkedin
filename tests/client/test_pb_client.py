import itertools
from unittest.mock import MagicMock, create_autospec, patch

import httpx
import pytest
from httpx import HTTPStatusError, NetworkError, TimeoutException
from pydantic import ValidationError

from parma_mining.linkedin.model import CompanyModel
from parma_mining.linkedin.pb_client import PhantombusterClient
from parma_mining.mining_common.exceptions import CrawlingExternalError

item = {
    "name": "Test Company",
    "companyUrl": "http://testcompany.com",
    "location": "Test Location",
    "industry": "Test Industry",
    "industryCode": "12345",
    "description": "Test Description",
    "website": "http://testwebsite.com",
    "phone": "123-456-7890",
    "specialties": "Test Specialties",
    "companySize": "11-50 employees",
    "logo": "http://testlogo.com/logo.png",
    "founded": "2000",
    "followerCount": 1000,
    "employeesOnLinkedIn": 50,
    "salesNavigatorLink": "http://salesnavigatorlink.com",
    "banner": "http://testbanner.com/banner.png",
    "domain": "testcompany.com",
    "companyAddress": "123 Test Street, Test City, Test Country",
    "headquarters": "Test Headquarters",
    "timestamp": "2023-01-01T00:00:00",
    "query": "Test Query",
    "mainCompanyID": 123456,
    "linkedinID": "linkedin-id-123456",
}

expected_result = {
    "id": "test_company_id",
    "name": "Test Company",
    "data_source": "linkedin",
    "link": "http://testcompany.com",
    "location": "Test Location",
    "industry": "Test Industry",
    "industry_code": "12345",
    "description": "Test Description",
    "website": "http://testwebsite.com",
    "phone": "123-456-7890",
    "specialities": "Test Specialties",
    "size": "11-50 employees",
    "logo": "http://testlogo.com/logo.png",
    "banner": "http://testbanner.com/banner.png",
    "domain": "testcompany.com",
    "address": "123 Test Street, Test City, Test Country",
    "headquarters": "Test Headquarters",
    "founded": "2000",
    "follower_count": 1000,
    "employee_count": 50,
    "company_id": 123456,
    "linkedin_id": "linkedin-id-123456",
    "sales_navigator_link": "http://salesnavigatorlink.com",
    "query": "Test Query",
    "timestamp": "2023-01-01T00:00:00",
}


@pytest.fixture
def pb_client():
    return PhantombusterClient(errors={})


@patch("httpx.get")
def test_is_container_finished_true(mock_get, pb_client: PhantombusterClient):
    container_id = "test_container_id"
    mock_request = create_autospec(httpx.Request, instance=True)
    mock_response = httpx.Response(
        status_code=200,
        json={"status": "finished"},
        request=mock_request,
    )
    mock_get.return_value = mock_response

    assert pb_client._is_container_finished(container_id) is True
    mock_get.assert_called()


@patch("httpx.get")
def test_is_container_finished_false(mock_get, pb_client: PhantombusterClient):
    container_id = "test_container_id"
    mock_request = create_autospec(httpx.Request, instance=True)
    mock_response = httpx.Response(
        status_code=200,
        json={"status": "not-finished"},
        request=mock_request,
    )
    mock_get.return_value = mock_response

    assert pb_client._is_container_finished(container_id) is False
    mock_get.assert_called()


@patch("httpx.get")
def test_generate_s3_url(mock_get, pb_client: PhantombusterClient):
    fetch_url = f"{pb_client.fetch_url}?id=test_id"
    mock_response = {
        "orgS3Folder": "org_folder",
        "s3Folder": "s3_folder",
        "filename": "result",
    }
    mock_get.return_value.json.return_value = mock_response

    expected_url = (
        "https://phantombuster.s3.amazonaws.com/org_folder/s3_folder/result.json"
    )
    assert pb_client._generate_s3_url(fetch_url) == expected_url


def test_extract_company_info(pb_client: PhantombusterClient):
    company_id = "test_company_id"

    expected_result_with_id = expected_result.copy()
    expected_result_with_id["id"] = company_id

    result = pb_client._extract_company_info(item, company_id)
    assert result == expected_result_with_id


@pytest.fixture
def mock_company_data():
    return [
        {
            "name": "Company A",
            "companyUrl": "http://companya.com",
            "timestamp": "2023-01-01T00:00:00",
        },
        {
            "name": "Company B",
            "companyUrl": "http://companyb.com",
            "timestamp": "2023-01-01T00:00:00",
        },
    ]


@patch("parma_mining.linkedin.model.CompanyModel.model_validate")
def test_process_company_data_success(
    mock_validate, mock_company_data, pb_client: PhantombusterClient
):
    mock_validate.side_effect = lambda x: x

    ids = ["id1", "id2"]
    result = pb_client._process_company_data(mock_company_data, ids, {})

    assert len(result) == len(mock_company_data)
    for company in result:
        assert isinstance(company, dict)


@patch("parma_mining.linkedin.model.CompanyModel.model_validate")
def test_process_company_data_exception(
    mock_validate, mock_company_data, pb_client: PhantombusterClient
):
    no_results = 0

    def raise_validation_error(*args, **kwargs):
        raise ValidationError([], CompanyModel)

    mock_validate.side_effect = raise_validation_error

    ids = ["id1", "id2"]
    result = pb_client._process_company_data(mock_company_data, ids, {})

    assert len(result) == no_results


@patch("parma_mining.linkedin.model.CompanyModel.model_validate")
def test_process_company_data_validation_error(
    mock_validate, mock_company_data, pb_client: PhantombusterClient
):
    mock_validate.side_effect = MagicMock(side_effect=ValidationError)

    ids = ["id1", "id2"]
    result = pb_client._process_company_data(mock_company_data, ids, {})

    assert len(result) == 0


@patch(
    "parma_mining.linkedin.pb_client.PhantombusterClient._collect_company_scraper_result"
)
@patch("parma_mining.linkedin.pb_client.PhantombusterClient._wait_for_container")
@patch("parma_mining.linkedin.pb_client.PhantombusterClient._launch_company_scraper")
def test_scrape_company_success(
    mock_launch, mock_wait, mock_collect, pb_client: PhantombusterClient
):
    mock_launch.return_value = "mock_container_id"
    mock_wait.return_value = True
    mock_collect.return_value = [
        {
            "id": "test_id",
            "name": "Test Company",
            "timestamp": "2023-01-01T00:00:00",
        }
    ]

    urls = ["http://companya.com"]
    ids = ["id1"]
    result = pb_client.scrape_company(urls, ids)

    mock_launch.assert_called_once_with(urls)
    mock_wait.assert_called_once_with("mock_container_id")
    mock_collect.assert_called_once_with(ids, pb_client.errors)

    assert len(result) == 1
    assert isinstance(result[0], dict)


@patch(
    "parma_mining.linkedin.pb_client.PhantombusterClient._collect_company_scraper_result"
)
@patch("parma_mining.linkedin.pb_client.PhantombusterClient._wait_for_container")
@patch("parma_mining.linkedin.pb_client.PhantombusterClient._launch_company_scraper")
def test_scrape_company_network_error(
    mock_launch, mock_wait, mock_collect, pb_client: PhantombusterClient
):
    mock_launch.return_value = "mock_container_id"
    mock_wait.return_value = True
    mock_collect.side_effect = NetworkError("Network error occurred")

    urls = ["http://companya.com"]
    ids = ["id1"]
    result = pb_client.scrape_company(urls, ids)

    assert len(result) == 0
    mock_launch.assert_called_once_with(urls)
    mock_wait.assert_called_once_with("mock_container_id")
    mock_collect.assert_called_once_with(ids, pb_client.errors)


@patch("parma_mining.linkedin.pb_client.PhantombusterClient._launch_company_scraper")
def test_scrape_company_no_container_id(mock_launch, pb_client: PhantombusterClient):
    mock_launch.return_value = None

    urls = ["http://companya.com"]
    ids = ["id1"]
    result = pb_client.scrape_company(urls, ids)

    assert len(result) == 0
    mock_launch.assert_called_once_with(urls)


@patch("parma_mining.linkedin.pb_client.PhantombusterClient._wait_for_container")
@patch("parma_mining.linkedin.pb_client.PhantombusterClient._launch_company_scraper")
def test_scrape_company_container_not_finished(
    mock_launch, mock_wait, pb_client: PhantombusterClient
):
    mock_launch.return_value = "mock_container_id"
    mock_wait.return_value = False

    urls = ["http://companya.com"]
    ids = ["id1"]
    result = pb_client.scrape_company(urls, ids)

    assert len(result) == 0
    mock_launch.assert_called_once_with(urls)
    mock_wait.assert_called_once_with("mock_container_id")


@patch("httpx.post")
def test_launch_company_scraper_success(mock_post, pb_client: PhantombusterClient):
    urls = ["http://example.com"]
    mock_response = httpx.Response(
        status_code=200,
        json={"containerId": "12345"},
    )
    mock_post.return_value = mock_response

    container_id = pb_client._launch_company_scraper(urls)
    mock_post.assert_called_once()
    assert container_id == "12345"


@patch("httpx.post")
def test_launch_company_scraper_http_error(mock_post, pb_client: PhantombusterClient):
    urls = ["http://example.com"]
    mock_request = httpx.Request("POST", "http://test")
    mock_response = httpx.Response(status_code=400, request=mock_request)
    mock_post.side_effect = httpx.HTTPStatusError(
        message="Error", request=mock_request, response=mock_response
    )

    container_id = pb_client._launch_company_scraper(urls)
    mock_post.assert_called_once()
    assert container_id is None


@patch("httpx.post")
def test_launch_company_scraper_exception(mock_post, pb_client: PhantombusterClient):
    urls = ["http://example.com"]
    mock_post.side_effect = Exception("Generic Error")

    container_id = pb_client._launch_company_scraper(urls)
    mock_post.assert_called_once()
    assert container_id is None


@patch("time.sleep", return_value=None)
@patch("httpx.get")
def test_wait_for_container(mock_get, mock_sleep, pb_client: PhantombusterClient):
    container_id = "12345"
    mock_request = httpx.Request("GET", "http://test")
    mock_responses = [
        httpx.Response(
            status_code=200, json={"status": "running"}, request=mock_request
        ),
        httpx.Response(
            status_code=200, json={"status": "finished"}, request=mock_request
        ),
    ]
    mock_get.side_effect = mock_responses

    result = pb_client._wait_for_container(container_id)
    assert mock_get.call_count == len(mock_responses)
    assert result is True
    mock_sleep.assert_called()


@patch("time.sleep", return_value=None)
@patch("parma_mining.linkedin.pb_client.PhantombusterClient._is_container_finished")
def test_wait_for_container_running_then_finishes(
    mock_is_finished, mock_sleep, pb_client: PhantombusterClient
):
    container_id = "12345"
    side_effects = [False, False, True]
    mock_is_finished.side_effect = side_effects

    result = pb_client._wait_for_container(container_id)

    assert mock_is_finished.call_count == len(side_effects)
    assert result is True
    mock_sleep.assert_called()


@patch("time.sleep", return_value=None)
@patch("parma_mining.linkedin.pb_client.PhantombusterClient._is_container_finished")
def test_wait_for_container_http_status_error_handling(
    mock_is_finished, mock_sleep, pb_client: PhantombusterClient
):
    container_id = "12345"
    error = HTTPStatusError(
        message="HTTP Status Error",
        request=httpx.Request("GET", "http://test"),
        response=httpx.Response(status_code=500),
    )

    mock_is_finished.side_effect = [error, True]

    pb_client.maximum_runtime_scraping_seconds = 1

    result = pb_client._wait_for_container(container_id)

    assert result is True
    mock_sleep.assert_called()


@patch("time.sleep", return_value=None)
@patch("parma_mining.linkedin.pb_client.PhantombusterClient._is_container_finished")
def test_wait_for_container_timeout_exception_handling(
    mock_is_finished, mock_sleep, pb_client: PhantombusterClient
):
    container_id = "12345"

    mock_is_finished.side_effect = [TimeoutException("Timeout occurred"), True]

    pb_client.maximum_runtime_scraping_seconds = 1

    result = pb_client._wait_for_container(container_id)

    assert result is True
    mock_sleep.assert_called()


@patch("time.sleep", return_value=None)
@patch("parma_mining.linkedin.pb_client.PhantombusterClient._is_container_finished")
def test_wait_for_container_exception_handling(
    mock_is_finished, mock_sleep, pb_client: PhantombusterClient
):
    container_id = "12345"
    error = Exception("Generic Error")

    mock_is_finished.side_effect = [error, True]

    pb_client.maximum_runtime_scraping_seconds = 1

    result = pb_client._wait_for_container(container_id)

    assert result is True
    mock_sleep.assert_called()


@patch("parma_mining.linkedin.pb_client.PhantombusterClient._is_container_finished")
@patch("parma_mining.linkedin.pb_client.time.time")
@patch("parma_mining.linkedin.pb_client.time.sleep", return_value=None)
@patch("parma_mining.linkedin.pb_client.collect_errors")
def test_wait_for_container_max_runtime_exceeded(
    mock_collect_errors,
    mock_sleep,
    mock_time,
    mock_is_finished,
    pb_client: PhantombusterClient,
):
    container_id = "12345"

    start_time = 100
    time_values = itertools.count(start=start_time, step=10)
    mock_time.side_effect = lambda: next(time_values)

    mock_is_finished.return_value = False

    result = pb_client._wait_for_container(container_id)

    assert result is False

    error_message = "Maximum runtime of 10 minutes reached while scraping companies!"
    mock_collect_errors.assert_called()
    called_args = mock_collect_errors.call_args[0]
    assert called_args[0] == "GENERAL"
    assert called_args[1] == pb_client.errors
    assert isinstance(called_args[2], CrawlingExternalError)
    assert str(called_args[2]) == error_message
