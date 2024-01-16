import json
from unittest.mock import MagicMock, patch

import httpx
import pytest

from parma_mining.linkedin.api.analytics_client import AnalyticsClient
from parma_mining.linkedin.model import CompanyModel
from parma_mining.mining_common.const import HTTP_200, HTTP_201, HTTP_404, HTTP_500
from parma_mining.mining_common.exceptions import AnalyticsError

TOKEN = "mocked_token"


@pytest.fixture
def analytics_client():
    return AnalyticsClient()


@pytest.fixture
def mock_company_model():
    mock_model = MagicMock(spec=CompanyModel)
    mock_model.id = "test_id"
    mock_model.name = "test_name"
    mock_model.data_source = "test_source"
    mock_model.link = "test_link"
    mock_model.location = "test_location"
    mock_model.industry = "test_industry"
    mock_model.industry_code = "test_industry_code"
    mock_model.description = "test_description"
    mock_model.website = "test_website"
    mock_model.phone = "test_phone"
    mock_model.specialities = "test_specialities"
    mock_model.size = "test_size"
    mock_model.logo = "test_logo"
    mock_model.banner = "test_banner"
    mock_model.domain = "test_domain"
    mock_model.address = "test_address"
    mock_model.headquarters = "test_headquarters"
    mock_model.founded = "test_founded"
    mock_model.follower_count = 123
    mock_model.employee_count = 456
    mock_model.company_id = 789
    mock_model.linkedin_id = "test_linkedin_id"
    mock_model.sales_navigator_link = "test_sales_navigator_link"
    mock_model.query = "test_query"
    mock_model.timestamp = "test_timestamp"

    mock_model.updated_model_dump.return_value = json.dumps(
        {
            "id": "test_id",
            "name": "test_name",
            "data_source": "test_source",
        }
    )
    return mock_model


@patch("httpx.post")
def test_send_post_request_success(mock_post, analytics_client):
    mock_post.return_value = httpx.Response(HTTP_200, json={"key": "value"})
    response = analytics_client.send_post_request(
        TOKEN, "http://example.com", {"data": "test"}
    )
    assert response == {"key": "value"}


@patch("httpx.post")
def test_send_post_request_failure(mock_post, analytics_client):
    mock_post.return_value = httpx.Response(HTTP_500, text="Internal Server Error")
    with pytest.raises(Exception) as exc_info:
        analytics_client.send_post_request(
            TOKEN, "http://example.com", {"data": "test"}
        )
    assert "API POST request failed with status code 500: Internal Server Error" in str(
        exc_info.value
    )


@patch("httpx.post")
def test_register_measurements(mock_post, analytics_client):
    mock_post.return_value = httpx.Response(HTTP_200, json={"id": "123"})
    mapping = {"Mappings": [{"DataType": "int", "MeasurementName": "test_metric"}]}
    result, updated_mapping = analytics_client.register_measurements(TOKEN, mapping)
    assert "source_measurement_id" in updated_mapping["Mappings"][0]
    assert result[0]["source_measurement_id"] == "123"


@patch("httpx.post")
def test_crawling_finished_success(mock_post, analytics_client):
    mock_post.return_value = httpx.Response(HTTP_200, json={"result": "success"})
    response = analytics_client.crawling_finished(TOKEN, {"data": "test"})
    assert response == {"result": "success"}


@patch("httpx.post")
def test_crawling_finished_failure(mock_post, analytics_client):
    mock_post.return_value = httpx.Response(HTTP_500, text="Internal Server Error")
    with pytest.raises(AnalyticsError):
        analytics_client.crawling_finished(TOKEN, {"data": "test"})


@patch("httpx.post")
def test_register_measurements_basic(mock_post, analytics_client):
    mock_post.return_value = httpx.Response(HTTP_200, json={"id": "123"})
    mapping = {"Mappings": [{"DataType": "int", "MeasurementName": "test_metric"}]}
    result, updated_mapping = analytics_client.register_measurements(TOKEN, mapping)
    assert updated_mapping["Mappings"][0]["source_measurement_id"] == "123"
    assert result[0]["source_measurement_id"] == "123"


@patch("httpx.post")
def test_register_measurements_multiple_nested_levels(mock_post, analytics_client):
    expected_result: int = 3
    mock_post.return_value = httpx.Response(HTTP_200, json={"id": "123"})
    multi_nested_mapping = {
        "Mappings": [
            {
                "DataType": "int",
                "MeasurementName": "level1_metric",
                "NestedMappings": [
                    {
                        "DataType": "string",
                        "MeasurementName": "level2_metric",
                        "NestedMappings": [
                            {"DataType": "float", "MeasurementName": "level3_metric"}
                        ],
                    }
                ],
            }
        ]
    }
    result, updated_mapping = analytics_client.register_measurements(
        TOKEN, multi_nested_mapping
    )

    # Assertions
    assert len(result) == expected_result
    assert updated_mapping["Mappings"][0]["source_measurement_id"] == "123"
    assert (
        updated_mapping["Mappings"][0]["NestedMappings"][0]["source_measurement_id"]
        == "123"
    )
    assert (
        updated_mapping["Mappings"][0]["NestedMappings"][0]["NestedMappings"][0][
            "source_measurement_id"
        ]
        == "123"
    )


@patch("httpx.post")
def test_register_measurements_no_mappings(mock_post, analytics_client):
    mock_post.return_value = httpx.Response(HTTP_200, json={"id": "123"})
    empty_mapping: dict = {"Mappings": []}
    result, updated_mapping = analytics_client.register_measurements(
        TOKEN, empty_mapping
    )
    assert result == []
    assert updated_mapping == empty_mapping


@patch("httpx.post")
def test_register_measurements_http_error(mock_post, analytics_client):
    mock_post.return_value = httpx.Response(HTTP_500)
    mapping = {"Mappings": [{"DataType": "int", "MeasurementName": "test_metric"}]}
    with pytest.raises(Exception):
        analytics_client.register_measurements(TOKEN, mapping)


@patch("httpx.post")
def test_register_measurements_return_value_structure(mock_post, analytics_client):
    mock_post.return_value = httpx.Response(HTTP_200, json={"id": "123"})
    mapping = {"Mappings": [{"DataType": "int", "MeasurementName": "test_metric"}]}
    result, updated_mapping = analytics_client.register_measurements(TOKEN, mapping)
    assert isinstance(result, list)
    assert isinstance(updated_mapping, dict)
    assert "Mappings" in updated_mapping
    assert len(result) == len(updated_mapping["Mappings"])
    for measurement in result:
        assert "source_measurement_id" in measurement
        assert measurement["source_measurement_id"] == "123"


@patch("httpx.post")
def test_register_measurements_with_parent_id_and_source_module_id(
    mock_post, analytics_client
):
    mock_post.return_value = httpx.Response(HTTP_200, json={"id": "123"})
    mapping = {"Mappings": [{"DataType": "int", "MeasurementName": "test_metric"}]}
    parent_id = "456"
    source_module_id = "789"
    result, updated_mapping = analytics_client.register_measurements(
        TOKEN, mapping, parent_id, source_module_id
    )

    assert len(result) == 1
    measurement_data = result[0]
    assert measurement_data["source_module_id"] == source_module_id
    assert measurement_data["parent_measurement_id"] == parent_id
    assert measurement_data["source_measurement_id"] == "123"
    assert updated_mapping["Mappings"][0]["source_measurement_id"] == "123"


@patch("httpx.post")
def test_feed_raw_data_success(mock_post, analytics_client, mock_company_model):
    mock_post.return_value = httpx.Response(HTTP_201, json={"result": "success"})
    result = analytics_client.feed_raw_data(TOKEN, mock_company_model)
    assert result == {"result": "success"}


@patch("httpx.post")
def test_feed_raw_data_failure(mock_post, analytics_client, mock_company_model):
    mock_post.return_value = httpx.Response(HTTP_500, text="Internal Server Error")
    with pytest.raises(Exception):
        analytics_client.feed_raw_data(TOKEN, mock_company_model)


@patch("httpx.post")
def test_feed_raw_data_404(mock_post, analytics_client, mock_company_model):
    mock_post.return_value = httpx.Response(HTTP_404, text="Not Found")
    result = analytics_client.feed_raw_data(TOKEN, mock_company_model)
    assert result is None
