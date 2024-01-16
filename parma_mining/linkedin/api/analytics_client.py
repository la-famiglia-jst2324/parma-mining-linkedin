"""Module for sending data to analytics.

This module sends normalization data and raw data to analytics.
"""
import json
import logging
import os
import urllib.parse

import httpx
from dotenv import load_dotenv

from parma_mining.linkedin.model import CompanyModel
from parma_mining.mining_common.const import HTTP_201, HTTP_404
from parma_mining.mining_common.exceptions import AnalyticsError

logger = logging.getLogger(__name__)


class AnalyticsClient:
    """Class for sending data to analytics."""

    load_dotenv()
    analytics_base = str(os.getenv("ANALYTICS_BASE_URL") or "")

    measurement_url = urllib.parse.urljoin(analytics_base, "/source-measurement")
    feed_raw_url = urllib.parse.urljoin(analytics_base, "/feed-raw-data")
    crawling_finished_url = urllib.parse.urljoin(analytics_base, "/crawling-finished")

    def send_post_request(self, token: str, data):
        """Send a post request to the analytics API."""
        api_endpoint = self.measurement_url
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }
        response = httpx.post(api_endpoint, json=data, headers=headers)

        if response.status_code == HTTP_201:
            return response.json().get("id")
        else:
            msg = (
                f"API POST request failed "
                f"with status code {response.status_code}: "
                f"{response.text}"
            )
            logger.error(msg)
            raise AnalyticsError(msg)

    def crawling_finished(self, data):
        """Notify crawling is finished to the analytics."""
        return self.send_post_request(self.crawling_finished_url, data)

    def register_measurements(
        self, token: str, mapping, parent_id=None, source_module_id=None
    ):
        """Register measurements to analytics."""
        result = []
        for field_mapping in mapping["Mappings"]:
            measurement_data = {
                "source_module_id": source_module_id,
                "type": field_mapping["DataType"],
                "measurement_name": field_mapping["MeasurementName"],
            }

            if parent_id is not None:
                measurement_data["parent_measurement_id"] = parent_id

            measurement_data["source_measurement_id"] = self.send_post_request(
                token, measurement_data
            )

            # add the source measurement id to mapping
            field_mapping["source_measurement_id"] = measurement_data[
                "source_measurement_id"
            ]

            if "NestedMappings" in field_mapping:
                nested_measurements = self.register_measurements(
                    token,
                    {"Mappings": field_mapping["NestedMappings"]},
                    parent_id=measurement_data["source_measurement_id"],
                    source_module_id=source_module_id,
                )[0]
                result.extend(nested_measurements)
            result.append(measurement_data)
        return result, mapping

    def feed_raw_data(self, token: str, company: CompanyModel):
        """Feed raw data to analytics."""
        api_endpoint = self.feed_raw_url
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }
        # make the company model json serializable
        raw_data = json.loads(company.updated_model_dump())
        data = {
            "source_name": str(company.data_source),
            "company_id": str(company.id),
            "raw_data": raw_data,
        }

        response = httpx.post(api_endpoint, json=data, headers=headers)

        if response.status_code == HTTP_201:
            return response.json()
        elif response.status_code == HTTP_404:
            pass
        else:
            raise Exception(
                f"API request is failed with status code {response.status_code}"
            )
